# -*- mode: python ; coding: utf-8 -*-
"""
AsFin Optimizer — PyInstaller spec file.

Build with:
    pyinstaller asfin.spec --clean

Output:
    dist/AsFin_Optimizer.exe
"""

import os
import sys
import pulp
from PyInstaller.utils.hooks import collect_submodules, collect_all

# Collect everything for critical libraries
# collect_all returns a tuple of (datas, binaries, hidden_imports)
xg_datas, xg_binaries, xg_hidden = collect_all('xgboost')
sk_datas, sk_binaries, sk_hidden = collect_all('sklearn')

# Locate pulp solver binaries
pulp_path = os.path.dirname(pulp.__file__)
pulp_solver_dir = os.path.join(pulp_path, 'solverdir')

# Collect all submodules that PyInstaller may miss
hidden = (
    collect_submodules('uvicorn') +
    collect_submodules('pulp') +
    collect_submodules('starlette') +
    collect_submodules('pydantic') +
    collect_submodules('pydantic_core') +
    xg_hidden +
    sk_hidden +
    [
        'src', 'src.main', 'src.config', 'src.data', 'src.optimizer',
        'src.llm_classifier', 'src.llm_router', 'src.settings_manager',
        'src.pipeline_runner', 'src.utils',
        'src.ml_model_trainer', 'src.ml_weight_learner', 'src.ml_data_explorer',
        'multiprocessing',
        'openai', 'anthropic', 'google.generativeai',
        'joblib', 'pandas', 'numpy', 'openpyxl',
    ]
)

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=xg_binaries + sk_binaries,
    datas=[
        # Frontend static files (read-only inside the exe)
        ('src/static', 'src/static'),
        # Seed data (copied to app_data/ on first run)
        ('data/processed_necesidades.json', 'data'),
        ('data/processed_planes.json', 'data'),
        ('data/processed_relacion_necesidad_plan.json', 'data'),
        ('data/sector_cache.json', 'data'),
        ('data/planes_accion_tfg_v2.xlsx', 'data'),
        ('data/ml_dataset_final.csv', 'data'),
        # Pre-trained models (copied to app_data/ on first run)
        ('models/correction_model.pkl', 'models'),
        ('models/feature_names.pkl', 'models'),
        ('models/learned_heuristics.pkl', 'models'),
        ('models/plan_encoder.pkl', 'models'),
        ('models/vec_need.pkl', 'models'),
        ('models/vec_sector.pkl', 'models'),
        ('models/vec_social.pkl', 'models'),
        # PuLP Solvers (Critical for .exe optimization)
        (pulp_solver_dir, 'pulp/solverdir'),
    ] + xg_datas + sk_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'tkinter', 'PIL', 'IPython', 'notebook',
        'pytest', 'sphinx',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AsFin_Optimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # Keep console visible for debugging; set False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='src/static/images/logo.ico',  # Uncomment if you have an .ico
)
