import pulp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_optimization(selected_needs_ids, needs_data, plans_data, relations_data, 
                       alpha=4, beta=3, gamma=0.5, delta=1, max_actions=3):
    """
    Builds and solves the optimization model using PuLP (Free CBC Solver).
    """
    
    # Filter data based on selected needs
    N_set = [nid for nid in selected_needs_ids if nid in needs_data]
    
    # Find relevant actions (plans) connected to these needs
    R_set = []
    for need in N_set:
        if need in relations_data:
            for plan in relations_data[need]:
                if plan in plans_data:
                    R_set.append((need, plan))
    
    # Unique actions involved
    A_set = list({plan for (_, plan) in R_set})
    
    if not N_set:
        raise ValueError("No valid needs selected or needs not found in data.")
    if not A_set:
        logger.warning("No actions found for the selected needs.")
        return 0, [], []

    # --- Build Model ---
    prob = pulp.LpProblem("Strategic_Planning", pulp.LpMaximize)

    # Variables
    # x[(i,j)]: assignment (need i -> action j)
    x = pulp.LpVariable.dicts("x", R_set, cat=pulp.LpBinary)
    
    # y[j]: action selection
    y = pulp.LpVariable.dicts("y", A_set, cat=pulp.LpBinary)

    # Parameters & Objective
    # Objective = sum(weight_ij * x_ij)
    objective_terms = []
    for (i, j) in R_set:
        # Calculate weight
        w_ij = (alpha * needs_data[i]['urgencia'] + 
                beta * needs_data[i]['importancia'] - 
                gamma * plans_data[j]['plazo_ejecucion'] - 
                delta * plans_data[j]['complejidad'])
        
        objective_terms.append(w_ij * x[(i, j)])
    
    prob += pulp.lpSum(objective_terms), "Objective_Value"

    # Constraints
    
    # 1. Coverage: Each selected need must be covered by at least one action
    for i in N_set:
        relevant_actions = [j for j in A_set if (i, j) in R_set]
        if relevant_actions:
            prob += pulp.lpSum(x[(i, j)] for j in relevant_actions) >= 1, f"Coverage_{i}"

    # 2. Coherence: If assigned (x=1), action must be selected (y=1) -> x_ij <= y_j
    for (i, j) in R_set:
        prob += x[(i, j)] <= y[j], f"Coherence_{i}_{j}"

    # 3. Max Actions
    prob += pulp.lpSum(y[j] for j in A_set) <= max_actions, "Max_Actions"

    # Solve
    # PuLP uses CBC by default, which needs no license
    solver = pulp.PULP_CBC_CMD(msg=False)
    try:
        prob.solve(solver)
    except Exception as e:
        logger.error(f"Solver failed: {e}")
        raise RuntimeError(f"Solver failed: {e}. Check libraries.")

    # Status check
    if pulp.LpStatus[prob.status] != 'Optimal':
        logger.warning(f"Optimization status: {pulp.LpStatus[prob.status]}")
        # Proceeding to extract what's possible, or return empty?
        # Usually checking 'Optimal' is key.

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
