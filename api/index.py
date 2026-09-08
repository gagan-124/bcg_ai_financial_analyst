"""Vercel Serverless Function entrypoint for BCG AI Financial Analyst.

Exposes the FastAPI application instance for Vercel's Python runtime.
Ensures the backend directory is in sys.path so that internal module
imports (app.core, app.api, app.services, etc.) resolve seamlessly.
"""

import importlib
import os
import sys

# Resolve absolute path to the backend directory and repository root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

for directory in (BACKEND_DIR, PROJECT_ROOT):
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Dynamically import after sys.path is initialized
_main_module = importlib.import_module("app.main")
app = _main_module.app

# Serverless runtime handler alias
handler = app

__all__ = ["app", "handler"]
