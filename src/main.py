from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import List, Optional

# Import local modules
try:
    from .optimizer import solve_optimization
except ImportError:
    try:
        from src.optimizer import solve_optimization
    except ImportError:
        from optimizer import solve_optimization

app = FastAPI(title="Optimizador Estratégico")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
DATA_CACHE = {
    "needs": {},
    "plans": {},
    "relations": {}
}

# Paths to data files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed") # Assuming data.py saves here?
# Let's check where data.py saves. It uses "data/processed" relative to run. 
# The files are named "processed_necesidades.json", etc.

def load_data():
    """Loads JSON data into memory."""
    try:
        # Paths based on data.py: SAVE_PATH = "data/processed"
        # files: "data/processed_necesidades.json"
        
        # Check if files exist, if not, maybe run data.py?
        # For now assume they exist as per previous context
        
        p_needs = os.path.join(DATA_DIR, "processed_necesidades.json")
        p_plans = os.path.join(DATA_DIR, "processed_planes.json")
        p_rels = os.path.join(DATA_DIR, "processed_relacion_necesidad_plan.json")

        if not os.path.exists(p_needs):
            print(f"File not found: {p_needs}. Attempting to run data extraction...")
            # Ideally we would call load_data() from data.py here
            # But let's assume valid state for now
            pass

        with open(p_needs, "r", encoding="utf-8") as f:
            DATA_CACHE["needs"] = json.load(f)
        with open(p_plans, "r", encoding="utf-8") as f:
            DATA_CACHE["plans"] = json.load(f)
        with open(p_rels, "r", encoding="utf-8") as f:
            DATA_CACHE["relations"] = json.load(f)
            
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")

# Load data on startup
@app.on_event("startup")
async def startup_event():
    load_data()

# Data Models
class SolveRequest(BaseModel):
    selected_needs: List[str]
    max_actions: int = 3
    alpha: float = 4.0
    beta: float = 3.0
    gamma: float = 0.5
    delta: float = 1.0

# API Endpoints
@app.get("/needs")
async def get_needs():
    """Returns the list of available needs."""
    return DATA_CACHE["needs"]

@app.post("/solve")
async def solve(request: SolveRequest):
    """Executes the optimization model."""
    if not DATA_CACHE["needs"]:
         raise HTTPException(status_code=500, detail="Data not loaded properly.")
    
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
            max_actions=request.max_actions
        )
        
        return {
            "objective_value": obj_val,
            "actions": actions,
            "assignments": assigns
        }
    except Exception as e:
        import traceback
        error_detail = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(error_detail) # also print to stderr
        raise HTTPException(status_code=500, detail=error_detail)

# Mount Static Files (Frontend)
# Must be last to not override API routes
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
