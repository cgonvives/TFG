# Web Interface Walkthrough

I have transformed the Pyomo optimization model into an interactive web application.

## Application Overview

The application is built with:
- **Backend**: FastAPI (Python) - serves the optimization API and static files.
- **Frontend**: HTML/JS/CSS - Expanded to a **Company Portal** with a landing page, **Dark/Light Mode**, and **Turquoise branding**.
- **Logic**: Refactored `src/planner.ipynb` into `src/optimizer.py`. Replaced **Gurobi** with **PuLP (CBC)** for open-source, license-free execution.

## Features

1.  **Needs Selection**: Users can view all needs loaded from `problemas_planes.xlsx` and select relevant ones.
2.  **Interactive Optimization**: Clicking "Generar Plan Óptimo" sends the selection to the backend, which runs the optimization using **PuLP**.
3.  **Visualization**: Results are displayed cleanly, showing the objective value, recommended actions, and specific need-to-action assignments.
4.  **Theming**: Toggle between Dark and Light modes using the icon in the header.

## Current State & Next Steps
- **Status**: Functional MVP with Portal and Optimizer.
- **Theme**: Turquoise Blue, Dark/Light Mode supported.
- **Next Steps**:
    - Implement "Analítica Financiera" dashboard.
    - Add user authentication for internal access.
    - Deploy to a production server.

1.  **Activate Environment**: Ensure you are in the `.venv` or have dependencies installed.
    ```powershell
    .\.venv\Scripts\activate
    ```
2.  **Start Server**:
    ```powershell
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ```
3.  **Access App**: Open [http://localhost:8000](http://localhost:8000) in your browser.

## Verification

### API Test
Ran a test request to `GET /needs`:
- **Expected**: JSON list of needs.
- **Result**: Data returned successfully (verified via script).

### UI Check
- **Needs List**: Loads automatically on startup.
- **Optimization**: Successfully calls the solver and renders results.
