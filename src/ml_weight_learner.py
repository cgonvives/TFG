import pandas as pd
import numpy as np
from scipy.optimize import minimize
import os
import joblib

def learn_optimal_weights(dataset_path):
    print(f"Loading dataset for weight learning: {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # We only care about positive samples (accepted=1) to see what experts liked
    # and compare them with the rejected options for the same context.
    
    # Inverse Optimization Objective:
    # Find weights [alpha, beta, gamma, delta] such that:
    # Score = alpha*Urg + beta*Imp - gamma*Plazo - delta*Comp
    # is maximized for the chosen plans.
    
    # Initial weights
    initial_params = [4.0, 3.0, 0.5, 1.0] # alpha, beta, gamma, delta
    
    # We will use a "Contrastive Loss" or "Rank Loss":
    # For each company and need, the chosen plan should have a higher score than NOT chosen ones.
    
    groups = df.groupby(['cod_company', 'cod_weakness'])
    
    def objective_function(params):
        alpha, beta, gamma, delta = params
        total_loss = 0
        count = 0
        
        for (comp, need), group in groups:
            if len(group) < 2: continue # Need at least one positive and one negative
            
            # Calculate scores for all options in this group using current params
            # Score = alpha*Urg + beta*Imp - gamma*Plazo - delta*Comp
            group = group.copy()
            group['score'] = (alpha * group['Urgencia'] + 
                             beta * group['Importancia'] - 
                             gamma * group['Plazo'] - 
                             delta * group['Complejidad'])
            
            chosen = group[group['accepted'] == 1]
            rejected = group[group['accepted'] == 0]
            
            if chosen.empty or rejected.empty: continue
            
            # Loss: we want Score(chosen) >> Score(rejected)
            # Softmax-like loss or hinge loss
            max_chosen_score = chosen['score'].max()
            max_rejected_score = rejected['score'].max()
            
            # penalty if rejected > chosen
            # Using a simple hinge loss: max(0, margin + rejected - chosen)
            diff = 1.0 + max_rejected_score - max_chosen_score
            total_loss += max(0, diff)
            count += 1
            
        return total_loss / (count if count > 0 else 1)

    print("Running optimization to find best heuristic weights...")
    res = minimize(objective_function, initial_params, method='Nelder-Mead', bounds=[(0, 10), (0, 10), (0, 5), (0, 5)])
    
    learned_weights = res.x
    print("\n--- Learned Weights ---")
    print(f"Alpha (Urgencia):   {learned_weights[0]:.2f}")
    print(f"Beta (Importancia): {learned_weights[1]:.2f}")
    print(f"Gamma (Plazo):      {learned_weights[2]:.2f}")
    print(f"Delta (Complejidad):{learned_weights[3]:.2f}")
    
    # Save for optimizer use
    os.makedirs("models", exist_ok=True)
    weights_dict = {
        'alpha': learned_weights[0],
        'beta': learned_weights[1],
        'gamma': learned_weights[2],
        'delta': learned_weights[3]
    }
    joblib.dump(weights_dict, "models/learned_heuristics.pkl")
    print("\nLearned weights saved to models/learned_heuristics.pkl")

if __name__ == "__main__":
    dataset_path = "data/ml_dataset_final.csv"
    if os.path.exists(dataset_path):
        learn_optimal_weights(dataset_path)
    else:
        print("Dataset not found. Run ml_data_explorer.py first.")
