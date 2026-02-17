import pandas as pd
import numpy as np
import glob
import os
import json
import sys
import io
from llm_classifier import classify_sector_llm

# Force utf-8 output for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    # Remove common legal prefixes
    prefixes = ["la sociedad tiene por objeto", "objeto social:", "actividad principal", "la participacion.", "la explotacion", "cnae"]
    for p in prefixes:
        text = text.replace(p, "")
    # Remove symbols and extra spaces
    text = "".join([c if c.isalnum() or c.isspace() else " " for c in text])
    return " ".join(text.split())
    
from utils import load_sector_cache, save_sector_cache
import time

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
        # Pacing: strictly stay under 15 RPM limit (1 call every 10s is safe)
        time.sleep(10)
        sector = classify_sector_llm(text)
        if sector and sector != "Otros":
            _sector_cache[text] = sector
            save_sector_cache(_sector_cache)
        return sector
    except Exception:
        return "Otros"

def explore_and_unify_data(file_path):
    # Print safe name
    print(f"Loading data file...")
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    print(f"Sheets: {sheet_names}")

    # 1. Load Catalog Data (same as data.py)
    # Autodetect sheets
    needs_sheet = [h for h in sheet_names if "neces" in h.lower()][0]
    plans_sheet = [h for h in sheet_names if "catalog" in h.lower() or "plan" in h.lower()][0]
    hist_sheet = [h for h in sheet_names if "hist" in h.lower()][0]
    social_sheet = [h for h in sheet_names if "social" in h.lower()][0]

    df_needs = pd.read_excel(file_path, sheet_name=needs_sheet)
    df_plans = pd.read_excel(file_path, sheet_name=plans_sheet)
    df_hist = pd.read_excel(file_path, sheet_name=hist_sheet)
    df_social = pd.read_excel(file_path, sheet_name=social_sheet)

    print("\n--- Data Samples ---")
    print(f"Needs: {df_needs.columns.tolist()}")
    print(f"Plans: {df_plans.columns.tolist()}")
    print(f"Historical: {df_hist.columns.tolist()}")
    print(f"Social: {df_social.columns.tolist()}")

    # 2. Process Company Context (Social Object)
    # Identifying company code columns
    c_hist = [c for c in df_hist.columns if 'cod' in c.lower() and 'comp' in c.lower()][0]
    c_social = [c for c in df_social.columns if 'cod' in c.lower() and 'comp' in c.lower()][0]
    c_obj = [c for c in df_social.columns if 'objeto' in c.lower()][0]

    df_companies = df_social[[c_social, c_obj]].drop_duplicates().rename(columns={c_social: 'cod_company', c_obj: 'objeto_social'})
    
    # NLP Cleaning and Sector Detection
    print("Processing NLP features...")
    df_companies["clean_objeto"] = df_companies["objeto_social"].apply(clean_text)
    df_companies["sector"] = df_companies["clean_objeto"].apply(detect_sector)
    # Replace the original for training
    df_companies["objeto_social"] = df_companies["clean_objeto"]

    # Identificar columnas en Datos Históricos
    c_h_comp = 'cod_company'
    c_h_need = 'cod_weakness'
    c_h_plan = 'cod_plan'

    # 4. Unificar Features de Empresas
    df_unified = df_hist[[c_h_comp, c_h_need, c_h_plan]].dropna()
    df_unified['accepted'] = 1  # POSITIVE SAMPLES
    df_unified = df_unified.merge(df_companies, on='cod_company', how='left')

    # 5. Unificar Features de Necesidades
    # En df_needs, el código está en 'Código Problema'
    c_n_code = 'Código Problema'
    # Seleccionamos estrictamente las columnas indicadas por el usuario
    cols_needs = [c_n_code, 'Nombre Tarjeta', 'Texto explicativo', 'Problema / Necesidad', 'Urgencia', 'Importancia']
    df_needs_clean = df_needs[cols_needs].dropna(subset=[c_n_code])
    
    # Pre-limpieza de texto explicativo (combinamos con Problema / Necesidad para mayor riqueza)
    df_needs_clean['contexto_necesidad'] = df_needs_clean['Problema / Necesidad'].fillna('') + " " + df_needs_clean['Texto explicativo'].fillna('')
    df_needs_clean['contexto_necesidad'] = df_needs_clean['contexto_necesidad'].apply(clean_text)
    
    df_unified = df_unified.merge(df_needs_clean, left_on=c_h_need, right_on=c_n_code, how='left')

    # 6. Unificar Features de Planes
    # En df_plans, el código está en 'Código Plan'
    c_p_code = 'Código Plan'
    df_plans_clean = df_plans[[c_p_code, 'Plazo de ejecución', 'Complejidad']].dropna(subset=[c_p_code])
    df_unified = df_unified.merge(df_plans_clean, left_on=c_h_plan, right_on=c_p_code, how='left')

    # 7. Mapear valores categóricos (como en data.py)
    urgency_map = {"Menos urgente": 1, "Urgente": 2, "Muy urgente": 3}
    importance_map = {"Menos importante": 1, "Importante": 2, "Muy importante": 3}
    complexity_map = {"Sencillo": 1, "Complejo": 2, "Muy  complejo": 3}
    
    df_unified['Urgencia'] = df_unified['Urgencia'].map(urgency_map).fillna(1).astype(int)
    df_unified['Importancia'] = df_unified['Importancia'].map(importance_map).fillna(1).astype(int)
    df_unified['Complejidad'] = df_unified['Complejidad'].map(complexity_map).fillna(1).astype(int)
    df_unified['Plazo'] = df_unified['Plazo de ejecución'].str.extract(r"(\d+)").astype(float).fillna(1).astype(int)
    df_unified.drop(columns=['Plazo de ejecución'], inplace=True)

    # 8. Generar Muestras Negativas
    # Para cada par (empresa, necesidad), qué planes NO se eligieron del catálogo?
    print("\nGenerating negative samples...")
    # Crear relación Necesidad -> Lista de Planes del catálogo
    catalog_relations = {}
    for _, row in df_plans.dropna(subset=['Código Problema', 'Código Plan']).iterrows():
        n = row['Código Problema']
        p = row['Código Plan']
        catalog_relations.setdefault(n, set()).add(p)

    negative_samples = []
    # Agrupar por empresa y necesidad para ver qué eligieron
    grouped = df_unified.groupby(['cod_company', 'cod_weakness'])['cod_plan'].apply(set).reset_index()
    
    for _, row in grouped.iterrows():
        comp = row['cod_company']
        need = row['cod_weakness']
        chosen_plans = row['cod_plan']
        
        # Planes disponibles para esta necesidad pero no elegidos
        if need in catalog_relations:
            available_plans = catalog_relations[need]
            not_chosen = available_plans - chosen_plans
            
            for p_neg in not_chosen:
                negative_samples.append({
                    'cod_company': comp,
                    'cod_weakness': need,
                    'cod_plan': p_neg,
                    'accepted': 0
                })

    df_neg = pd.DataFrame(negative_samples)
    
    # Añadir features a las muestras negativas
    df_neg = df_neg.merge(df_companies, on='cod_company', how='left')
    df_neg = df_neg.merge(df_needs_clean, left_on='cod_weakness', right_on=c_n_code, how='left')
    df_neg = df_neg.merge(df_plans_clean, left_on='cod_plan', right_on=c_p_code, how='left')
    
    # Limpiar y mapear negativas
    df_neg.drop(columns=[c_n_code, c_p_code], inplace=True)
    df_neg['Urgencia'] = df_neg['Urgencia'].map(urgency_map).fillna(1).astype(int)
    df_neg['Importancia'] = df_neg['Importancia'].map(importance_map).fillna(1).astype(int)
    df_neg['Complejidad'] = df_neg['Complejidad'].map(complexity_map).fillna(1).astype(int)
    df_neg['Plazo'] = df_neg['Plazo de ejecución'].str.extract(r"(\d+)").astype(float).fillna(1).astype(int)
    df_neg.drop(columns=['Plazo de ejecución'], inplace=True)

    # Combinar Positivos y Negativos
    df_final = pd.concat([df_unified, df_neg], ignore_index=True)

    save_path = "data/ml_dataset_final.csv"
    df_final.to_csv(save_path, index=False, encoding='utf-8')
    print(f"\nFinal ML dataset saved to {save_path}")
    print(f"Final shape: {df_final.shape}")
    print(f"Accepted ratio: {df_final['accepted'].mean():.2f}")
    
    return df_final

if __name__ == "__main__":
    NEW_FILE = glob.glob("data/Planes de acción - TFG v2.xlsx")[0]
    df_final = explore_and_unify_data(NEW_FILE)
