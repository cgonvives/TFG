import json
import os
from src.optimizer import solve_optimization

def load_json_data():
    base_path = "data/processed"
    with open(f"{base_path}_necesidades.json", "r") as f:
        needs = json.load(f)
    with open(f"{base_path}_planes.json", "r") as f:
        plans = json.load(f)
    with open(f"{base_path}_relacion_necesidad_plan.json", "r") as f:
        rels = json.load(f)
    return needs, plans, rels

def verify_ml_impact():
    needs_data, plans_data, relations_data = load_json_data()
    
    # Test case: Select a few common needs
    selected_needs = ["1.2.7.", "2.2.5.", "3.1.1."]
    
    print("--- Case 1: Standard Optimizer (No ML) ---")
    val1, actions1, _ = solve_optimization(selected_needs, needs_data, plans_data, relations_data, objeto_social=None)
    for a in actions1:
        print(f"- {a['description']} (id: {a['id']})")

    print("\n--- Case 2: ML Optimizer (Sector: Agricultural Services) ---")
    # Using a fake "objeto_social" that matches agricultural context
    objeto_agri = "Servicios agrícolas de siembra y recolección de cereales."
    val2, actions2, _ = solve_optimization(selected_needs, needs_data, plans_data, relations_data, objeto_social=objeto_agri, ml_weight=50.0)
    for a in actions2:
        print(f"- {a['description']} (id: {a['id']})")

    print("\n--- Case 3: ML Optimizer (Sector: Technology / Software) ---")
    objeto_tech = "Desarrollo de software y consultoría tecnológica avanzada."
    val3, actions3, _ = solve_optimization(selected_needs, needs_data, plans_data, relations_data, objeto_social=objeto_tech, ml_weight=50.0)
    for a in actions3:
        print(f"- {a['description']} (id: {a['id']})")

    # Comparison
    ids1 = {a['id'] for a in actions1}
    ids2 = {a['id'] for a in actions2}
    ids3 = {a['id'] for a in actions3}
    
    if ids1 != ids2 or ids2 != ids3:
        print("\nSUCCESS: Recommendations changed based on the company profile!")
    else:
        print("\nNOTE: Recommendations remained the same (this could happen if the catalog is small or weights are similar).")

if __name__ == "__main__":
    verify_ml_impact()
