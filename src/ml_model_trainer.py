import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import OneHotEncoder
import joblib
import os
from src.config import (
    MODEL_XGB, VEC_SOCIAL, VEC_NEED, VEC_SECTOR, PLAN_ENCODER, FEATURE_NAMES,
    MAX_FEATURES_SOCIAL, MAX_FEATURES_NEED, MAX_FEATURES_SECTOR
)

def train_ml_model(dataset_path):
    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    
    # Fill NaN
    df['objeto_social'] = df['objeto_social'].fillna('sin informacion')
    df['contexto_necesidad'] = df['contexto_necesidad'].fillna('sin informacion')
    df['sector'] = df['sector'].fillna('Otros')
    
    # 1. NLP: Vectorize Objeto Social (Empresa)
    print("Vectorizing Objeto Social...")
    vec_social = TfidfVectorizer(max_features=MAX_FEATURES_SOCIAL, stop_words=None)
    X_social = vec_social.fit_transform(df['objeto_social'])
    feat_social = pd.DataFrame(X_social.toarray(), columns=[f"social_{c}" for c in vec_social.get_feature_names_out()])
    
    # 2. NLP: Vectorize Contexto Necesidad (Tarjeta)
    print("Vectorizing Contexto Necesidad...")
    vec_need = TfidfVectorizer(max_features=MAX_FEATURES_NEED, stop_words=None)
    X_need = vec_need.fit_transform(df['contexto_necesidad'])
    feat_need = pd.DataFrame(X_need.toarray(), columns=[f"need_{c}" for c in vec_need.get_feature_names_out()])
    
    # 3. Categorical: Sector Encoding (using TF-IDF for dynamic sectors)
    print("Encoding Sectors...")
    vec_sector = TfidfVectorizer(max_features=MAX_FEATURES_SECTOR, stop_words=None)
    X_sector = vec_sector.fit_transform(df['sector'])
    feat_sector = pd.DataFrame(X_sector.toarray(), columns=[f"sec_{c}" for c in vec_sector.get_feature_names_out()])
    
    # 4. Categorical: Plan Encoding (One Hot)
    print("Encoding Plans...")
    df['cod_plan'] = df['cod_plan'].fillna('sin_plan')
    enc_plan = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_plan = enc_plan.fit_transform(df[['cod_plan']])
    feat_plan = pd.DataFrame(X_plan, columns=[f"plan_{c}" for c in enc_plan.get_feature_names_out(['cod_plan'])])
    
    # 5. Numeric Features
    numeric_features = df[['Urgencia', 'Importancia', 'Complejidad', 'Plazo']].reset_index(drop=True)
    
    X = pd.concat([numeric_features, feat_sector, feat_social, feat_need, feat_plan], axis=1)
    y = df['accepted']
    
    # 6. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 7. Train
    print("Training Enriched XGBoost...")
    model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, objective='binary:logistic', random_state=42)
    model.fit(X_train, y_train)
    
    # 8. Evaluate
    y_proba = model.predict_proba(X_test)[:, 1]
    print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    
    # 9. Save
    os.makedirs(os.path.dirname(MODEL_XGB), exist_ok=True)
    joblib.dump(model, MODEL_XGB)
    joblib.dump(vec_social, VEC_SOCIAL)
    joblib.dump(vec_need, VEC_NEED)
    joblib.dump(vec_sector, VEC_SECTOR)
    joblib.dump(enc_plan, PLAN_ENCODER)
    joblib.dump(X.columns.tolist(), FEATURE_NAMES)
    
    print(f"\nAll artifacts saved to {os.path.dirname(MODEL_XGB)}/ folder.")

if __name__ == "__main__":
    from src.config import ML_DATASET_FINAL
    train_ml_model(ML_DATASET_FINAL)
