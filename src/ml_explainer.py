import pandas as pd
import numpy as np
import shap
import joblib
import os
import matplotlib.pyplot as plt
import src.ml_model_trainer as trainer

def generate_explanations(dataset_path):
    print(f"Loading data for explanation: {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # Load model and feature names
    model = joblib.load("models/correction_model.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    
    # Prepare X (same as in trainer)
    # Note: We need the exact features the model was trained on
    # For simplicity, we just take a few rows from the final dataset and map them
    # But wait, it's easier to just use the training logic to get X
    
    # Actually, let's just use the feature names we saved
    # We will reconstruct a representative sample for global importance
    # (Simplified: just reload the dataset and re-run the part that creates X)
    
    # Actually, safer to just use a sample from the CSV if it has the features
    # But the CSV doesn't have the TF-IDF features yet.
    
    # Let's recreate X from the CSV using the models
    print("Reconstructing feature matrix for SHAP...")
    vec_social = joblib.load("models/vec_social.pkl")
    vec_need = joblib.load("models/vec_need.pkl")
    sector_encoder = joblib.load("models/sector_encoder.pkl")
    
    df['objeto_social'] = df['objeto_social'].fillna('sin informacion')
    df['contexto_necesidad'] = df['contexto_necesidad'].fillna('sin informacion')
    df['sector'] = df['sector'].fillna('Otros')
    
    X_social = vec_social.transform(df['objeto_social']).toarray()
    feat_social = pd.DataFrame(X_social, columns=[f"social_{c}" for c in vec_social.get_feature_names_out()])
    
    X_need = vec_need.transform(df['contexto_necesidad']).toarray()
    feat_need = pd.DataFrame(X_need, columns=[f"need_{c}" for c in vec_need.get_feature_names_out()])
    
    X_sector = sector_encoder.transform(df[['sector']])
    feat_sector = pd.DataFrame(X_sector, columns=sector_encoder.get_feature_names_out(['sector']))
    
    numeric_features = df[['Urgencia', 'Importancia', 'Complejidad', 'Plazo']]
    X = pd.concat([numeric_features, feat_sector, feat_social, feat_need], axis=1)
    X = X.reindex(columns=feature_names, fill_value=0)
    
    # Initialize Explainer
    print("Calculating SHAP values (this may take a moment)...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # 1. Global Importance Plot
    print("Generating Global Feature Importance plot...")
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False, max_display=15)
    plt.title("Global Feature Importance (SHAP)")
    os.makedirs("doc/images", exist_ok=True)
    plt.tight_layout()
    plt.savefig("doc/images/shap_global_importance.png")
    plt.close()
    
    # 2. Local Explanation Helper
    def get_local_explanation(row_idx):
        # Contribution of each feature for a single prediction
        sv = shap_values[row_idx]
        features = X.columns
        # Sort by importance (absolute value)
        sorted_indices = np.argsort(np.abs(sv))[::-1]
        
        reasons = []
        for i in sorted_indices[:5]:
            if np.abs(sv[i]) < 0.05: continue # Ignore small noise
            direction = "Aumenta la probabilidad" if sv[i] > 0 else "Disminuye la probabilidad"
            reasons.append(f"{features[i]} ({X.iloc[row_idx, i]}): {direction}")
        return reasons

    # Generate a sample report for the walkthrough
    print("\n--- Example Local Explanations ---")
    for i in range(min(5, len(X))):
        print(f"\nSample {i} (Accepted: {df.iloc[i]['accepted']}):")
        expls = get_local_explanation(i)
        for e in expls:
            print(f"  - {e}")

    print(f"\nImages and analysis generated in doc/images/")

if __name__ == "__main__":
    generate_explanations("data/ml_dataset_final.csv")
