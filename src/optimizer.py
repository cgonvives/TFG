import pulp
import logging
import joblib
import pandas as pd
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.utils import load_sector_cache, save_sector_cache, remove_accents, clean_text
from src.config import (
    MODEL_XGB, VEC_SOCIAL, VEC_NEED, VEC_SECTOR, PLAN_ENCODER, FEATURE_NAMES,
    LEARNED_HEURISTICS, ALPHA_DEFAULT, BETA_DEFAULT, GAMMA_DEFAULT, DELTA_DEFAULT,
    ML_WEIGHT_DEFAULT
)

# Global cache for sectors
_sector_cache = load_sector_cache()

def detect_sector(text):
    """
    Detects the industry sector from a company's 'objeto social' text.

    The lookup is done with the CLEANED version of the text (same as how
    the sector was stored in the cache during dataset construction in
    ml_data_explorer.py). This ensures cache hits and coherence between
    training and inference.

    NOTE: The sector is ONLY used as a feature inside the ML model (XGBoost).
    The heuristic optimizer weights (w_ij) intentionally do NOT use the sector.
    """
    if not text:
        return "Otros"

    # Always clean the text before cache lookup to match training-time keys
    clean = clean_text(text)
    if not clean:
        return "Otros"

    if clean in _sector_cache:
        return _sector_cache[clean]

    try:
        from src.llm_classifier import classify_sector_llm
        sector = classify_sector_llm(clean)
        if sector and sector != "Otros":
            _sector_cache[clean] = sector
            save_sector_cache(_sector_cache)
        return sector
    except Exception:
        return "Otros"

def get_ml_scores(R_set, needs_data, plans_data, objeto_social=None):
    """
    Predicts 'Advisor Acceptance' scores using the trained ML model.
    """
    if not all(os.path.exists(p) for p in [MODEL_XGB, VEC_SOCIAL, VEC_NEED, VEC_SECTOR, PLAN_ENCODER, FEATURE_NAMES]):
        logger.warning("ML Components missing. Falling back to default weights.")
        return {rel: 0.0 for rel in R_set}

    try:
        model = joblib.load(MODEL_XGB)
        vec_social = joblib.load(VEC_SOCIAL)
        vec_need = joblib.load(VEC_NEED)
        vec_sector = joblib.load(VEC_SECTOR)
        enc_plan = joblib.load(PLAN_ENCODER)
        feature_names = joblib.load(FEATURE_NAMES)
    except Exception as e:
        logger.error(f"Error loading ML components: {e}")
        return {rel: 0.0 for rel in R_set}

    # Company NLP Processing
    # 1. Social Feature (using TF-IDF)
    # voc_social was trained with terms like 'construccion' (no accent) 
    # but some others like 'tecnológica' (with accent). 
    # To maximize hits, we clean it.
    clean_obj = clean_text(objeto_social or "sin informacion")
    normalized_obj_no_accents = remove_accents(clean_obj)
    
    # We use a heuristic: try to find keywords in both. 
    # But sticking to the most common pattern found in audit: 
    # SOCIAL had 'construccion' instead of 'construcción'.
    text_vec_social = vec_social.transform([normalized_obj_no_accents]).toarray()[0]
    social_features = dict(zip([f"social_{c}" for c in vec_social.get_feature_names_out()], text_vec_social))
    
    # 2. Sector Feature (using TF-IDF) — used ONLY inside the ML model.
    # The heuristic weights (w_ij) below do NOT use the sector intentionally.
    # detect_sector() internally cleans the text before cache lookup,
    # ensuring the key matches the one stored during training (ml_data_explorer.py).
    sec_name = detect_sector(objeto_social) if objeto_social else "Otros"
    logger.info(f"Sector detected for ML model: '{sec_name}'")
    X_sector = vec_sector.transform([sec_name])
    feat_sector = pd.DataFrame(X_sector.toarray(), columns=[f"sec_{c}" for c in vec_sector.get_feature_names_out()])
    sector_features = feat_sector.iloc[0].to_dict()
    # Relation features
    features_list = []
    for (i, j) in R_set:
        # Build need context (similar to training)
        card_name = needs_data[i].get('nombre_tarjeta', '')
        card_desc = needs_data[i].get('texto_explicativo', '')
        # FIXED: Key is 'necesidad', not 'problema_necesidad'
        prob_desc = needs_data[i].get('necesidad', '')
        
        # Cleanup parenthesis and extra spaces to match trainer if possible
        # but the trainer just did straight fit_transform on CSV strings.
        context_text = f"{prob_desc} {card_desc}".replace("(", "").replace(")", "").strip()
        clean_need_text = clean_text(context_text or "sin informacion")
        
        # DEBUG (will be visible in logs)
        # logger.debug(f"Need ID: {i} | Context: {clean_need_text[:50]}...")
        
        text_vec_need = vec_need.transform([clean_need_text]).toarray()[0]
        need_nlp_features = dict(zip([f"need_{c}" for c in vec_need.get_feature_names_out()], text_vec_need))
        
        # 4. Plan ID Feature (using OneHot)
        # Ensure plan_id is handled as we did in training
        plan_vec = enc_plan.transform([[j]])[0]
        plan_features = dict(zip([f"plan_{c}" for c in enc_plan.get_feature_names_out(['cod_plan'])], plan_vec))

        f = {
            'Urgencia': needs_data[i].get('urgencia', 1),
            'Importancia': needs_data[i].get('importancia', 1),
            'Complejidad': plans_data[j].get('complejidad', 1),
            'Plazo': plans_data[j].get('plazo_ejecucion', 1)
        }
        f.update(sector_features)
        f.update(social_features)
        f.update(need_nlp_features)
        f.update(plan_features)
        features_list.append(f)

    X = pd.DataFrame(features_list)
    X = X.reindex(columns=feature_names, fill_value=0)
    
    scores = model.predict_proba(X)[:, 1]
    
    # Log ML scores per plan (only visible at DEBUG level)
    scoring_dict = {R_set[idx][1]: round(float(scores[idx]), 4) for idx in range(len(R_set))}
    logger.debug(f"ML scores for sector '{sec_name}': {scoring_dict}")
    
    return {R_set[idx]: scores[idx] for idx in range(len(R_set))}

def solve_optimization(selected_needs_ids, needs_data, plans_data, relations_data, 
                         alpha=ALPHA_DEFAULT, beta=BETA_DEFAULT, gamma=GAMMA_DEFAULT, delta=DELTA_DEFAULT, max_actions=3,
                         objeto_social=None, ml_weight=ML_WEIGHT_DEFAULT, use_learned_weights=True):
    """
    Builds and solves the optimization model with ML-enhanced weights.
    """
    if use_learned_weights:
        if os.path.exists(LEARNED_HEURISTICS):
            try:
                learned = joblib.load(LEARNED_HEURISTICS)
                alpha = learned.get('alpha', alpha)
                beta = learned.get('beta', beta)
                gamma = learned.get('gamma', gamma)
                delta = learned.get('delta', delta)
                logger.info(f"Using learned weights: alpha={alpha:.2f}, beta={beta:.2f}, gamma={gamma:.2f}, delta={delta:.2f}")
            except Exception as e:
                logger.error(f"Error loading learned weights: {e}")
    
    # Filter data based on selected needs and ensure uniqueness
    unique_needs = sorted(list(set(selected_needs_ids))) # Sorted for determinism
    N_set = [nid for nid in unique_needs if nid in needs_data]
    
    # Find relevant actions
    R_set = []
    seen_rels = set()
    for need in N_set: # N_set is sorted
        if need in relations_data:
            # Sort plans for determinism
            sorted_plans = sorted(relations_data[need])
            for plan in sorted_plans:
                if plan in plans_data:
                    rel = (need, plan)
                    if rel not in seen_rels:
                        R_set.append(rel)
                        seen_rels.add(rel)
    
    # Unique actions involved - SORTED for determinism
    A_set = sorted(list({plan for (_, plan) in R_set}))
    
    if not N_set:
        raise ValueError("No se han seleccionado necesidades válidas.")
    if not A_set:
        return 0, [], []

    # Get ML Scores if applicable
    ml_scores = get_ml_scores(R_set, needs_data, plans_data, objeto_social)

    # --- Build Model ---
    prob = pulp.LpProblem("Strategic_Planning", pulp.LpMaximize)

    # Variables
    x = pulp.LpVariable.dicts("x", R_set, cat=pulp.LpBinary)
    y = pulp.LpVariable.dicts("y", A_set, cat=pulp.LpBinary)

    # Parameters & Objective
    objective_terms = []
    for (i, j) in R_set:
        # ── Heuristic weight (sector-agnostic) ──────────────────────────────
        # w_ij depends ONLY on need urgency/importance and plan complexity/time.
        # The sector is intentionally NOT used here so that the base heuristic
        # is sector-neutral. The sector's influence comes exclusively through
        # the ML model score (ml_boost) below, making the added value of the
        # ML model clearly measurable vs the heuristic baseline.
        w_ij = (alpha * needs_data[i]['urgencia'] +
                beta  * needs_data[i]['importancia'] -
                gamma * plans_data[j]['plazo_ejecucion'] -
                delta * plans_data[j]['complejidad'])

        # ── ML correction (sector-aware via XGBoost) ─────────────────────
        # ml_scores were computed by get_ml_scores() which includes sector
        # features extracted by detect_sector() + vec_sector vectorizer.
        ml_boost = ml_weight * ml_scores[(i, j)]

        # Micro tie-breaker for perfect determinism: penalize high IDs insignificantly
        # This ensures that if two plans have EXACTLY same score, the selection is stable.
        tie_breaker = 0.000001 / (float(hash(j) % 1000) + 1.0)

        objective_terms.append((w_ij + ml_boost + tie_breaker) * x[(i, j)])
    
    prob += pulp.lpSum(objective_terms) + (0.001 * pulp.lpSum(y[j] for j in A_set)), "Objective_Value"

    # Constraints
    for i in N_set:
        relevant_actions = [j for j in A_set if (i, j) in R_set]
        if relevant_actions:
            prob += pulp.lpSum(x[(i, j)] for j in relevant_actions) >= 1, f"Coverage_{i}"

    for (i, j) in R_set:
        prob += x[(i, j)] <= y[j], f"Coherence_{i}_{j}"

    prob += pulp.lpSum(y[j] for j in A_set) <= max_actions, "Max_Actions"

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    try:
        prob.solve(solver)
    except Exception as e:
        logger.error(f"Solver failed: {e}")
        raise RuntimeError(f"Error interno del motor de optimización.")

    # Status check
    status = pulp.LpStatus[prob.status]
    if status == 'Infeasible':
        raise ValueError(f"No es posible cubrir las {len(N_set)} necesidades seleccionadas con solo {max_actions} acciones.")
    elif status != 'Optimal':
        logger.warning(f"Optimization status: {status}")
        raise ValueError(f"No se pudo encontrar una solución óptima (Estado: {status}).")

    # Extract Results
    objective_value = pulp.value(prob.objective)
    
    # Track contributions per action for sorted output
    plan_contributions = {}
    for (i, j) in R_set:
        if pulp.value(x[(i, j)]) > 0.5:
            # Recompute total weight for this (need, plan)
            w_ij = (alpha * needs_data[i]['urgencia'] + 
                    beta * needs_data[i]['importancia'] - 
                    gamma * plans_data[j]['plazo_ejecucion'] - 
                    delta * plans_data[j]['complejidad'])
            ml_boost = ml_weight * ml_scores[(i, j)]
            contribution = w_ij + ml_boost
            plan_contributions[j] = plan_contributions.get(j, 0) + contribution

    recommended_actions = []
    # Sort Actions by total contribution (High to Low)
    sorted_A = sorted(A_set, key=lambda j: plan_contributions.get(j, -1e9) if pulp.value(y[j]) > 0.5 else -2e9, reverse=True)
    
    for j in sorted_A:
        if pulp.value(y[j]) > 0.5:
            recommended_actions.append({
                "id": j,
                "description": plans_data[j]['descripcion'],
                "period": plans_data[j]['plazo_ejecucion'],
                "complexity": plans_data[j]['complejidad']
            })

    assignments = []
    for (i, j) in R_set:
        if pulp.value(x[(i, j)]) > 0.5:
            assignments.append({
                "need_id": i,
                "action_id": j
            })

    return objective_value, recommended_actions, assignments
