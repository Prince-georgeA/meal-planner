"""
Vercel serverless entry point for the MealPlanner FastAPI backend.
Vercel runs this file as a serverless function and routes /api/* to it.
"""
import sys
import os

# Add the backend directory to the Python path so `from main import app` works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app  # noqa: F401  — Vercel picks up `app` automatically
