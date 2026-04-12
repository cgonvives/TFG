import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
DOC_DIR = os.path.join(BASE_DIR, "doc")

# Data File Paths
_files = os.listdir(DATA_DIR)
_excel_name = next((f for f in _files if "Planes de" in f and "v2" in f and f.endswith(".xlsx")), "Planes de acción - TFG v2.xlsx")
EXCEL_FILE = os.path.join(DATA_DIR, _excel_name)
PROCESSED_BASE = os.path.join(DATA_DIR, "processed")
ML_DATASET_FINAL = os.path.join(DATA_DIR, "ml_dataset_final.csv")
SECTOR_CACHE_FILE = os.path.join(DATA_DIR, "sector_cache.json")

# Model File Paths
MODEL_XGB = os.path.join(MODEL_DIR, "correction_model.pkl")
VEC_SOCIAL = os.path.join(MODEL_DIR, "vec_social.pkl")
VEC_NEED = os.path.join(MODEL_DIR, "vec_need.pkl")
VEC_SECTOR = os.path.join(MODEL_DIR, "vec_sector.pkl")
PLAN_ENCODER = os.path.join(MODEL_DIR, "plan_encoder.pkl")
LEARNED_HEURISTICS = os.path.join(MODEL_DIR, "learned_heuristics.pkl")
FEATURE_NAMES = os.path.join(MODEL_DIR, "feature_names.pkl")

# Heuristic Weights Defaults
ALPHA_DEFAULT = 4.0
BETA_DEFAULT = 3.0
GAMMA_DEFAULT = 0.5
DELTA_DEFAULT = 1.0

# ML Parameters
ML_WEIGHT_DEFAULT = 10.0
MAX_FEATURES_SOCIAL = 300
MAX_FEATURES_NEED = 300
MAX_FEATURES_SECTOR = 50
