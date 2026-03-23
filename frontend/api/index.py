"""
Vercel serverless function — lives at frontend/api/index.py
because Vercel Root Directory is set to 'frontend'.
Vercel serves this at /api/* and strips the /api prefix
before passing to FastAPI.
"""
import sys
import os

# Path to backend/ from frontend/api/index.py → ../../backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from main import app  # noqa: F401
