import pulp
import logging
import joblib
import pandas as pd
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    prefixes = ["la sociedad tiene por objeto", "objeto social:", "actividad principal", "la participacion.", "la explotacion", "cnae"]
    for p in prefixes:
        text = text.replace(p, "")
    text = "".join([c if c.isalnum() or c.isspace() else " " for c in text])
    return " ".join(text.split())

from src.utils import load_sector_cache, save_sector_cache

# Global cache for sectors
_sector_cache = load_sector_cache()

def detect_sector(text):
    """
    Detects the industry sector using LLM classification.
    """
    if not text:
        return "Otros"
        
    if text in _sector_cache:
        return _sector_cache[text]
        
    try:
        from src.llm_classifier import classify_sector_llm
        sector = classify_sector_llm(text)
        if sector and sector != "Otros":
            _sector_cache[text] = sector
            save_sector_cache(_sector_cache)
        return sector
    except Exception:
        return "Otros"

def get_ml_scores(R_set, needs_data, plans_data, objeto_social=None):
    """
    Predicts 'Advisor Acceptance' scores using the trained ML model.
    """
    model_path = "models/correction_model.pkl"
    vec_social_path = "models/vec_social.pkl"
    vec_need_path = "models/vec_need.pkl"
    vec_sector_path = "models/vec_sector.pkl" # Changed from enc_path
    feat_path = "models/feature_names.pkl"
    
    if not all(os.path.exists(p) for p in [model_path, vec_social_path, vec_need_path, vec_sector_path, feat_path]): # Updated path variable
        logger.warning("ML Components missing. Falling back to default weights.")
        return {rel: 0.0 for rel in R_set}

    try:
        model = joblib.load(model_path)
        vec_social = joblib.load(vec_social_path)
        vec_need = joblib.load(vec_need_path)
        vec_sector = joblib.load(vec_sector_path)
        feature_names = joblib.load(feat_path)
    except Exception as e:
        logger.error(f"Error loading ML components: {e}")
        return {rel: 0.0 for rel in R_set}

    # Company NLP Processing
    clean_obj = clean_text(objeto_social or "sin informacion")
    
    text_vec_social = vec_social.transform([clean_obj]).toarray()[0]
    social_features = dict(zip([f"social_{c}" for c in vec_social.get_feature_names_out()], text_vec_social))
    
    # 2. Sector Feature (using TF-IDF)
    sec_name = detect_sector(objeto_social) if objeto_social else "Otros"
    X_sector = vec_sector.transform([sec_name])
    feat_sector = pd.DataFrame(X_sector.toarray(), columns=[f"sec_{c}" for c in vec_sector.get_feature_names_out()])
    sector_features = feat_sector.iloc[0].to_dict() # Convert DataFrame row to dict for consistency

    # Relation features
    features_list = []
    for (i, j) in R_set:
        # Build need context (similar to training)
        card_name = needs_data[i].get('nombre_tarjeta', '')
        card_desc = needs_data[i].get('texto_explicativo', '')
        prob_desc = needs_data[i].get('problema_necesidad', '')
        context_text = f"{prob_desc} {card_desc}".strip()
        clean_need_text = clean_text(context_text or "sin informacion")
        
        text_vec_need = vec_need.transform([clean_need_text]).toarray()[0]
        need_nlp_features = dict(zip([f"need_{c}" for c in vec_need.get_feature_names_out()], text_vec_need))
        
        f = {
            'Urgencia': needs_data[i].get('urgencia', 1),
            'Importancia': needs_data[i].get('importancia', 1),
            'Complejidad': plans_data[j].get('complejidad', 1),
            'Plazo': plans_data[j].get('plazo_ejecucion', 1)
        }
        f.update(sector_features)
        f.update(social_features)
        f.update(need_nlp_features)
        features_list.append(f)

    X = pd.DataFrame(features_list)
    X = X.reindex(columns=feature_names, fill_value=0)
    
    scores = model.predict_proba(X)[:, 1]
    return {R_set[idx]: scores[idx] for idx in range(len(R_set))}

def solve_optimization(selected_needs_ids, needs_data, plans_data, relations_data, 
                         alpha=4, beta=3, gamma=0.5, delta=1, max_actions=3,
                         objeto_social=None, ml_weight=10.0, use_learned_weights=True):
    """
    Builds and solves the optimization model with ML-enhanced weights.
    """
    if use_learned_weights:
        weights_path = "models/learned_heuristics.pkl"
        if os.path.exists(weights_path):
            try:
                learned = joblib.load(weights_path)
                alpha = learned.get('alpha', alpha)
                beta = learned.get('beta', beta)
                gamma = learned.get('gamma', gamma)
                delta = learned.get('delta', delta)
                logger.info(f"Using learned weights: alpha={alpha:.2f}, beta={beta:.2f}, gamma={gamma:.2f}, delta={delta:.2f}")
            except Exception as e:
                logger.error(f"Error loading learned weights: {e}")
    
    # Filter data based on selected needs and ensure uniqueness
    unique_needs = list(dict.fromkeys(selected_needs_ids))
    N_set = [nid for nid in unique_needs if nid in needs_data]
    
    # Find relevant actions
    R_set = []
    seen_rels = set()
    for need in N_set:
        if need in relations_data:
            for plan in relations_data[need]:
                if plan in plans_data:
                    rel = (need, plan)
                    if rel not in seen_rels:
                        R_set.append(rel)
                        seen_rels.add(rel)
    
    # Unique actions involved
    A_set = list({plan for (_, plan) in R_set})
    
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
        # Base weight from rules
        w_ij = (alpha * needs_data[i]['urgencia'] + 
                beta * needs_data[i]['importancia'] - 
                gamma * plans_data[j]['plazo_ejecucion'] - 
                delta * plans_data[j]['complejidad'])
        
        # Add ML correction
        ml_boost = ml_weight * ml_scores[(i, j)]
        
        objective_terms.append((w_ij + ml_boost) * x[(i, j)])
    
    prob += pulp.lpSum(objective_terms) + (0.01 * pulp.lpSum(y[j] for j in A_set)), "Objective_Value"

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
    
    recommended_actions = []
    for j in A_set:
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
