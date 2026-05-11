"""
pipeline_runner.py — Background ML pipeline orchestrator.

Runs the full data-processing → training pipeline in a background
thread so the web UI stays responsive.  Exposes a simple status API
that the frontend polls.
"""

import logging
import threading
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Singleton-style runner that tracks pipeline status."""

    def __init__(self):
        self.status: str = "idle"       # idle | running | completed | error
        self.current_step: str = ""
        self.progress: float = 0.0
        self.error_message: str = ""
        self.last_run: str = ""
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    # ── Public API ──────────────────────────────────────────────────

    def get_status(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "current_step": self.current_step,
                "progress": round(self.progress, 2),
                "error_message": self.error_message,
                "last_run": self.last_run,
            }

    def start(self, excel_path: str, reload_callback=None):
        """
        Launch the full pipeline in a background thread.

        Parameters
        ----------
        excel_path : str
            Absolute path to the uploaded ``.xlsx`` file.
        reload_callback : callable, optional
            Called after successful training to reload DATA_CACHE
            in the FastAPI app.
        """
        with self._lock:
            if self.status == "running":
                return {"error": "Pipeline ya en ejecución."}
            self.status = "running"
            self.progress = 0.0
            self.current_step = "Iniciando…"
            self.error_message = ""

        self._thread = threading.Thread(
            target=self._run,
            args=(excel_path, reload_callback),
            daemon=True,
        )
        self._thread.start()
        return {"message": "Pipeline iniciado."}

    # ── Internal pipeline logic ─────────────────────────────────────

    def _update(self, step: str, progress: float):
        with self._lock:
            self.current_step = step
            self.progress = progress
        logger.info(f"Pipeline [{progress:.0%}] {step}")

    def _run(self, excel_path: str, reload_callback):
        try:
            # Late imports so the module loads even if some deps are missing
            from src.config import DATA_DIR, MODEL_DIR, PROCESSED_BASE, ML_DATASET_FINAL

            # ── Step 1: Process raw Excel → JSON ────────────────────
            self._update("Procesando datos del Excel…", 0.10)
            from src.data import load_data, extract_needs, extract_plans_and_relations, save_json
            needs_df, plans_df = load_data(excel_path)

            self._update("Extrayendo necesidades y planes…", 0.20)
            needs_dict = extract_needs(needs_df)
            plans_dict, relations_dict = extract_plans_and_relations(plans_df)
            save_json(needs_dict, plans_dict, relations_dict, PROCESSED_BASE)

            # ── Step 2: Build ML dataset ────────────────────────────
            self._update("Construyendo dataset ML…", 0.35)
            from src.ml_data_explorer import explore_and_unify_data
            explore_and_unify_data(excel_path)

            # ── Step 3: Train XGBoost model ─────────────────────────
            self._update("Entrenando modelo XGBoost…", 0.60)
            from src.ml_model_trainer import train_ml_model
            train_ml_model(ML_DATASET_FINAL)

            # ── Step 4: Learn optimal heuristic weights ─────────────
            self._update("Optimizando pesos heurísticos…", 0.80)
            from src.ml_weight_learner import learn_optimal_weights
            learn_optimal_weights(ML_DATASET_FINAL)

            # ── Step 5: Record & reload ─────────────────────────────
            self._update("Finalizando…", 0.95)
            from src.settings_manager import record_training
            record_training()

            if reload_callback:
                reload_callback()

            with self._lock:
                self.status = "completed"
                self.progress = 1.0
                self.current_step = "Pipeline completado con éxito."
                self.last_run = datetime.now().isoformat()

            logger.info("Pipeline completed successfully.")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Pipeline failed:\n{tb}")
            with self._lock:
                self.status = "error"
                self.error_message = str(e)
                self.current_step = "Error durante el pipeline."


# Module-level singleton
pipeline = PipelineRunner()
