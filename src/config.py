import os
import sys

# ──────────────────────────────────────────────────────────────
# Path helpers for PyInstaller compatibility
# ──────────────────────────────────────────────────────────────

def resource_path(relative_path):
    """
    Locates bundled resources whether running as a script or as a
    PyInstaller-frozen executable.

    When frozen, PyInstaller extracts files to a temporary folder
    referenced by sys._MEIPASS.  During development the paths are
    resolved relative to the project root (parent of ``src/``).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        relative_path,
    )


def get_app_data_dir():
    """
    Returns the directory for persistent user data.

    * **Frozen (.exe):** ``app_data/`` next to the executable so the
      user can find and back up their files easily.
    * **Development:** the project root itself (keeps the existing
      layout intact).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), "app_data")
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ──────────────────────────────────────────────────────────────
# Base Directories
# ──────────────────────────────────────────────────────────────

# Read-only resources bundled inside the .exe (or project root in dev)
BASE_DIR = resource_path("")

# Persistent read/write directory for user data
APP_DATA = get_app_data_dir()
DATA_DIR = os.path.join(APP_DATA, "data")
MODEL_DIR = os.path.join(APP_DATA, "models")
DOC_DIR = os.path.join(APP_DATA, "doc")

# Ensure writable directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# Settings (persistent user configuration)
# ──────────────────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(APP_DATA, "settings.json")

# ──────────────────────────────────────────────────────────────
# Data File Paths
# ──────────────────────────────────────────────────────────────

def _detect_excel():
    """Find the main Excel file in DATA_DIR, falling back to a default name."""
    if os.path.isdir(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".xlsx") and "Planes de" in f:
                return os.path.join(DATA_DIR, f)
    # Check for the user-uploaded standard name
    user_upload = os.path.join(DATA_DIR, "user_data.xlsx")
    if os.path.exists(user_upload):
        return user_upload
    return os.path.join(DATA_DIR, "planes_accion_tfg_v2.xlsx")

EXCEL_FILE = _detect_excel()
PROCESSED_BASE = os.path.join(DATA_DIR, "processed")
ML_DATASET_FINAL = os.path.join(DATA_DIR, "ml_dataset_final.csv")
SECTOR_CACHE_FILE = os.path.join(DATA_DIR, "sector_cache.json")

# ──────────────────────────────────────────────────────────────
# Model File Paths
# ──────────────────────────────────────────────────────────────
MODEL_XGB = os.path.join(MODEL_DIR, "correction_model.pkl")
VEC_SOCIAL = os.path.join(MODEL_DIR, "vec_social.pkl")
VEC_NEED = os.path.join(MODEL_DIR, "vec_need.pkl")
VEC_SECTOR = os.path.join(MODEL_DIR, "vec_sector.pkl")
PLAN_ENCODER = os.path.join(MODEL_DIR, "plan_encoder.pkl")
LEARNED_HEURISTICS = os.path.join(MODEL_DIR, "learned_heuristics.pkl")
FEATURE_NAMES = os.path.join(MODEL_DIR, "feature_names.pkl")

# ──────────────────────────────────────────────────────────────
# Static files (bundled read-only frontend)
# ──────────────────────────────────────────────────────────────
STATIC_DIR = resource_path(os.path.join("src", "static"))

# ──────────────────────────────────────────────────────────────
# Heuristic Weights Defaults
# ──────────────────────────────────────────────────────────────
ALPHA_DEFAULT = 4.0
BETA_DEFAULT = 3.0
GAMMA_DEFAULT = 0.5
DELTA_DEFAULT = 1.0

# ──────────────────────────────────────────────────────────────
# ML Parameters
# ──────────────────────────────────────────────────────────────
ML_WEIGHT_DEFAULT = 10.0
MAX_FEATURES_SOCIAL = 300
MAX_FEATURES_NEED = 300
MAX_FEATURES_SECTOR = 50
