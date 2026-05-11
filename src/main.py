"""
main.py — FastAPI server for the AsFin Strategic Optimizer.

Serves both the existing optimizer API and the new administration
endpoints for data upload, ML re-training, and LLM configuration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import shutil
from typing import List, Optional

# ── Local imports ───────────────────────────────────────────────────
try:
    from src.optimizer import solve_optimization
    from src.data import load_processed_data
    from src.config import (
        ALPHA_DEFAULT, BETA_DEFAULT, GAMMA_DEFAULT, DELTA_DEFAULT,
        DATA_DIR, STATIC_DIR, EXCEL_FILE,
    )
    from src.settings_manager import load_settings, save_settings, record_upload
    from src.pipeline_runner import pipeline
    from src.llm_router import test_connection
except ImportError:
    from optimizer import solve_optimization
    from data import load_processed_data
    from config import (
        ALPHA_DEFAULT, BETA_DEFAULT, GAMMA_DEFAULT, DELTA_DEFAULT,
        DATA_DIR, STATIC_DIR, EXCEL_FILE,
    )
    from settings_manager import load_settings, save_settings, record_upload
    from pipeline_runner import pipeline
    from llm_router import test_connection


app = FastAPI(title="AsFin — Optimizador Estratégico")

# ── Global data storage ─────────────────────────────────────────────
DATA_CACHE = {
    "needs": {},
    "plans": {},
    "relations": {},
}


def load_data():
    """Loads processed JSON data into memory."""
    try:
        needs, plans, relations = load_processed_data()
        DATA_CACHE["needs"] = needs
        DATA_CACHE["plans"] = plans
        DATA_CACHE["relations"] = relations
        print(f"[OK] Data loaded: {len(needs)} needs, {len(plans)} plans.")
    except Exception as e:
        print(f"[WARN] Data not loaded yet: {e}")


@app.on_event("startup")
async def startup_event():
    load_data()


# ════════════════════════════════════════════════════════════════════
#  EXISTING ENDPOINTS (Optimizer)
# ════════════════════════════════════════════════════════════════════

class SolveRequest(BaseModel):
    selected_needs: List[str]
    max_actions: int = 3
    objeto_social: Optional[str] = None
    alpha: float = ALPHA_DEFAULT
    beta: float = BETA_DEFAULT
    gamma: float = GAMMA_DEFAULT
    delta: float = DELTA_DEFAULT


@app.get("/needs")
async def get_needs():
    """Returns the list of available needs."""
    return DATA_CACHE["needs"]


@app.post("/solve")
async def solve(request: SolveRequest):
    """Executes the optimization model."""
    if not DATA_CACHE["needs"]:
        raise HTTPException(status_code=500, detail="Data not loaded properly.")

    print(
        f"Solving with {len(request.selected_needs)} needs, "
        f"max_actions={request.max_actions} and "
        f"sector={request.objeto_social[:30] if request.objeto_social else 'N/A'}"
    )
    try:
        obj_val, actions, assigns = solve_optimization(
            selected_needs_ids=request.selected_needs,
            needs_data=DATA_CACHE["needs"],
            plans_data=DATA_CACHE["plans"],
            relations_data=DATA_CACHE["relations"],
            alpha=request.alpha,
            beta=request.beta,
            gamma=request.gamma,
            delta=request.delta,
            max_actions=request.max_actions,
            objeto_social=request.objeto_social,
        )
        return {
            "objective_value": obj_val,
            "actions": actions,
            "assignments": assigns,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


# ════════════════════════════════════════════════════════════════════
#  NEW ENDPOINTS — Settings / LLM
# ════════════════════════════════════════════════════════════════════

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    api_key: Optional[str] = None


@app.get("/api/settings")
async def get_settings():
    """Return current settings (API key is masked for security)."""
    settings = load_settings()
    masked = dict(settings)
    key = masked.get("api_key", "")
    if key and len(key) > 8:
        masked["api_key_preview"] = key[:4] + "…" + key[-4:]
    else:
        masked["api_key_preview"] = "No configurada"
    masked.pop("api_key", None)  # Never send the full key to the frontend
    return masked


@app.post("/api/settings")
async def update_settings(body: SettingsUpdate):
    """Save LLM provider and/or API key."""
    updates = {}
    if body.llm_provider is not None:
        if body.llm_provider not in ("openai", "gemini", "anthropic"):
            raise HTTPException(status_code=400, detail="Proveedor no válido.")
        updates["llm_provider"] = body.llm_provider
    if body.api_key is not None:
        updates["api_key"] = body.api_key
    saved = save_settings(updates)
    return {"message": "Configuración guardada.", "provider": saved.get("llm_provider")}


class TestLLMRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None


@app.post("/api/settings/test-llm")
async def test_llm(body: TestLLMRequest):
    """Test LLM connection with the provided or stored key."""
    settings = load_settings()
    provider = body.provider or settings.get("llm_provider", "gemini")
    key = body.api_key or settings.get("api_key", "")
    result = test_connection(provider, key)
    status_code = 200 if result["success"] else 400
    return JSONResponse(content=result, status_code=status_code)


# ════════════════════════════════════════════════════════════════════
#  NEW ENDPOINTS — Data Upload
# ════════════════════════════════════════════════════════════════════

@app.post("/api/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """
    Upload a new .xlsx data file.  The file is saved as
    ``app_data/data/user_data.xlsx`` (fixed internal name).
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx")

    dest = os.path.join(DATA_DIR, "user_data.xlsx")
    try:
        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)

        # Quick validation: try to open with openpyxl/pandas
        import pandas as pd
        xl = pd.ExcelFile(dest)
        sheet_names = xl.sheet_names

        # Record the upload
        record_upload(file.filename)

        return {
            "message": "Archivo subido correctamente.",
            "filename": file.filename,
            "internal_path": "user_data.xlsx",
            "sheets": sheet_names,
            "size_kb": round(len(contents) / 1024, 1),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


@app.get("/api/data/info")
async def data_info():
    """Return information about the current dataset."""
    settings = load_settings()

    # Check which Excel file exists
    user_file = os.path.join(DATA_DIR, "user_data.xlsx")
    has_user_data = os.path.exists(user_file)

    # Count needs/plans from cache
    info = {
        "has_data": has_user_data or os.path.exists(EXCEL_FILE),
        "original_filename": settings.get("original_filename", ""),
        "last_upload_date": settings.get("last_upload_date", ""),
        "last_training_date": settings.get("last_training_date", ""),
        "num_needs": len(DATA_CACHE.get("needs", {})),
        "num_plans": len(DATA_CACHE.get("plans", {})),
    }
    return info


# ════════════════════════════════════════════════════════════════════
#  NEW ENDPOINTS — ML Pipeline
# ════════════════════════════════════════════════════════════════════

@app.get("/api/pipeline/status")
async def pipeline_status():
    """Get the current status of the ML training pipeline."""
    return pipeline.get_status()


@app.post("/api/pipeline/run")
async def pipeline_run():
    """Start the full ML pipeline (data → training → weights) in background."""
    # Determine which Excel to use
    user_file = os.path.join(DATA_DIR, "user_data.xlsx")
    if os.path.exists(user_file):
        excel_path = user_file
    elif os.path.exists(EXCEL_FILE):
        excel_path = EXCEL_FILE
    else:
        raise HTTPException(
            status_code=400,
            detail="No hay archivo de datos. Suba un archivo .xlsx primero.",
        )

    result = pipeline.start(excel_path, reload_callback=load_data)
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


# ════════════════════════════════════════════════════════════════════
#  Static Files (must be last to not override API routes)
# ════════════════════════════════════════════════════════════════════

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
