"""
launcher.py — Entry point for the AsFin Optimizer .exe

This module is the target for PyInstaller.  It:
  1. Creates the ``app_data/`` directory structure on first run.
  2. Copies bundled seed data (Excel, models, JSONs) if they don't exist yet.
  3. Opens the default browser after a short delay.
  4. Starts the Uvicorn server on http://127.0.0.1:8000.
"""

import multiprocessing
import os
import shutil
import sys
import threading
import time
import webbrowser


def _resource(relative_path: str) -> str:
    """Resolve a path inside the PyInstaller bundle (or project root in dev)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def _seed_initial_data():
    """
    On first launch, copy the bundled data and models into ``app_data/``
    so the application works out of the box.
    """
    from src.config import DATA_DIR, MODEL_DIR

    # ── Seed data files ─────────────────────────────────────────────
    bundled_data = _resource("data")
    if os.path.isdir(bundled_data):
        for fname in os.listdir(bundled_data):
            src = os.path.join(bundled_data, fname)
            dst = os.path.join(DATA_DIR, fname)
            if not os.path.exists(dst) and os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"  📄 Copied {fname} → app_data/data/")

    # ── Seed model files ────────────────────────────────────────────
    bundled_models = _resource("models")
    if os.path.isdir(bundled_models):
        for fname in os.listdir(bundled_models):
            src = os.path.join(bundled_models, fname)
            dst = os.path.join(MODEL_DIR, fname)
            if not os.path.exists(dst) and os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"  🧠 Copied {fname} → app_data/models/")


def _open_browser():
    """Wait for the server to be ready, then open the browser."""
    time.sleep(2.5)
    url = "http://127.0.0.1:8000"
    print(f"\n🌐 Opening browser: {url}")
    webbrowser.open(url)


def main():
    multiprocessing.freeze_support()

    print("=" * 50)
    print("  AsFin — Optimizador Estratégico")
    print("=" * 50)

    # Ensure data directories exist
    from src.config import DATA_DIR, MODEL_DIR
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Seed initial data if first run
    _seed_initial_data()

    # Open browser in background
    threading.Thread(target=_open_browser, daemon=True).start()

    # Start server
    import uvicorn
    from src.main import app
    print("\n🚀 Starting server on http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop.\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
