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
    from .data import load_processed_data
except ImportError:
    try:
        from src.optimizer import solve_optimization
        from src.data import load_processed_data
    except ImportError:
        from optimizer import solve_optimization
        from data import load_processed_data

app = FastAPI(title="Optimizador Estratégico")

# ... (CORS config)

# Global data storage
DATA_CACHE = {
    "needs": {},
    "plans": {},
    "relations": {}
}

def load_data():
    """Loads JSON data into memory using centralized logic."""
    try:
        needs, plans, relations = load_processed_data()
        DATA_CACHE["needs"] = needs
        DATA_CACHE["plans"] = plans
        DATA_CACHE["relations"] = relations
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")

# Load data on startup
@app.on_event("startup")
async def startup_event():
    load_data()

from src.config import ALPHA_DEFAULT, BETA_DEFAULT, GAMMA_DEFAULT, DELTA_DEFAULT

# Data Models
class SolveRequest(BaseModel):
    selected_needs: List[str]
    max_actions: int = 3
    objeto_social: Optional[str] = None
    alpha: float = ALPHA_DEFAULT
    beta: float = BETA_DEFAULT
    gamma: float = GAMMA_DEFAULT
    delta: float = DELTA_DEFAULT

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
    
    print(f"Solving with {len(request.selected_needs)} needs, max_actions={request.max_actions} and sector={request.objeto_social[:30] if request.objeto_social else 'N/A'}")
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
            objeto_social=request.objeto_social
        )
        
        return {
            "objective_value": obj_val,
            "actions": actions,
            "assignments": assigns
        }
    except ValueError as ve:
        # Known feasibility or validation errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        error_detail = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(error_detail) # also print to stderr
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

# Mount Static Files (Frontend)
# Must be last to not override API routes
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
