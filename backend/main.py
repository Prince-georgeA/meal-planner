"""
MealPlanner — FastAPI Backend v5
=================================
Two jobs:
  1. Serve the built Vue frontend
  2. POST /api/recipes/import  — bulk-load recipes into a user's Supabase DB

The backend holds zero user data. Each user's data lives in their own
Supabase project, connected via the connection screen in the app.

Dev:
  cd frontend && npm run dev -- --host          (Vite handles /api proxy)
Production:
  cd frontend && npm run build
  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import socket
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MealPlanner API",
    description=(
        "Serves the MealPlanner frontend and provides a **bulk recipe import** "
        "endpoint that writes directly into the user's own Supabase project.\n\n"
        "## How to bulk-import recipes\n"
        "1. Open `/docs` in your browser\n"
        "2. Find `POST /api/recipes/import`\n"
        "3. Click **Try it out**\n"
        "4. Paste your Supabase URL, anon key, and recipe list\n"
        "5. Click **Execute** — recipes appear in the app immediately"
    ),
    version="5.0.0",
)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except: return None


LOCAL_IP = get_local_ip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ───────────────────────────────────────────────────────────

VALID_CATS = {"breakfast", "lunch", "dinner", "snacks"}

class RecipeIn(BaseModel):
    """
    A single recipe.

    ```json
    {
      "name": "Pasta Carbonara",
      "emoji": "🍝",
      "category": "dinner",
      "ingredients": ["200g spaghetti", "3 egg yolks", "100g pancetta", "50g pecorino"]
    }
    ```
    """
    name:        str
    emoji:       str           = "🍽️"
    category:    Optional[str] = None
    ingredients: List[str]     = []

    @field_validator("category")
    @classmethod
    def validate_cat(cls, v):
        if v is not None and v not in VALID_CATS:
            raise ValueError(f"category must be one of {sorted(VALID_CATS)} or null")
        return v

    @field_validator("ingredients")
    @classmethod
    def strip_ings(cls, v):
        return [i.strip() for i in v if i.strip()]


class RecipeOut(RecipeIn):
    id: int


class ImportPayload(BaseModel):
    """
    Bulk import recipes directly into a Supabase project.

    - `supabase_url`  — Your project URL (e.g. `https://xxxx.supabase.co`)
    - `supabase_key`  — Your project's **anon** (public) key
    - `replace_all`   — `false` (default): merge/update by name. `true`: wipe first.
    - `recipes`       — List of recipes to import

    Example:
    ```json
    {
      "supabase_url": "https://xxxxxxxxxxxx.supabase.co",
      "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "replace_all": false,
      "recipes": [
        {
          "name": "Semiya Upma",
          "emoji": "🍲",
          "category": "breakfast",
          "ingredients": ["Roasted semiya", "Onion", "Green chilli", "Mustard seeds", "Curry leaves", "Oil"]
        },
        {
          "name": "Dal Tadka",
          "emoji": "🍛",
          "category": "dinner",
          "ingredients": ["Toor dal", "Tomato", "Onion", "Garlic", "Cumin", "Ghee", "Coriander"]
        }
      ]
    }
    ```
    """
    supabase_url: str
    supabase_key: str
    replace_all:  bool         = False
    recipes:      List[RecipeIn]


class ImportResult(BaseModel):
    added:   int
    updated: int
    total:   int
    recipes: List[RecipeOut]


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health():
    return {
        "status":  "ok",
        "mode":    "supabase-byod",
        "version": "5.0.0",
        "localIp": LOCAL_IP,
        "docs":    "/docs",
    }


# ── Bulk import ───────────────────────────────────────────────────────────────
@app.post("/api/recipes/import", response_model=ImportResult, tags=["Recipes"])
async def import_recipes(payload: ImportPayload):
    """
    Bulk-import recipes directly into the user's Supabase project.

    The server connects to Supabase on behalf of the request using the
    provided anon key, then returns.  No credentials are stored server-side.

    - **replace_all = false** (default): recipes with the same name are updated;
      new names are appended. Safe to run repeatedly.
    - **replace_all = true**: all existing recipes are deleted first, then the
      provided list is inserted clean.
    """
    url     = payload.supabase_url.rstrip("/")
    key     = payload.supabase_key
    headers = {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }
    rest = f"{url}/rest/v1"

    async with httpx.AsyncClient(timeout=20) as client:

        # ── Fetch existing recipes ──
        r = await client.get(f"{rest}/recipes?select=id,name", headers=headers)
        if r.status_code == 401:
            raise HTTPException(401, "Invalid Supabase credentials")
        if r.status_code not in (200, 206):
            raise HTTPException(502, f"Supabase error fetching recipes: {r.text}")

        existing = r.json() if r.status_code in (200, 206) else []

        # ── replace_all: delete everything first ──
        if payload.replace_all and existing:
            dr = await client.delete(
                f"{rest}/recipes?id=gte.0",
                headers={**headers, "Prefer": "return=minimal"},
            )
            if dr.status_code not in (200, 204):
                raise HTTPException(502, f"Failed to clear recipes: {dr.text}")
            existing = []

        # ── Build name→id index ──
        name_to_id = {row["name"].lower(): row["id"] for row in existing}

        added   = 0
        updated = 0
        results = []

        for recipe in payload.recipes:
            data = {
                "name":        recipe.name,
                "emoji":       recipe.emoji,
                "category":    recipe.category,
                "ingredients": recipe.ingredients,
            }
            key_lower = recipe.name.lower()

            if key_lower in name_to_id:
                # UPDATE existing
                existing_id = name_to_id[key_lower]
                pr = await client.patch(
                    f"{rest}/recipes?id=eq.{existing_id}",
                    json=data,
                    headers=headers,
                )
                if pr.status_code not in (200, 204):
                    raise HTTPException(502, f"Failed to update '{recipe.name}': {pr.text}")
                results.append({**data, "id": existing_id})
                updated += 1
            else:
                # INSERT new
                pr = await client.post(f"{rest}/recipes", json=data, headers=headers)
                if pr.status_code not in (200, 201):
                    raise HTTPException(502, f"Failed to insert '{recipe.name}': {pr.text}")
                inserted = pr.json()
                new_id   = inserted[0]["id"] if isinstance(inserted, list) else inserted["id"]
                results.append({**data, "id": new_id})
                name_to_id[key_lower] = new_id
                added += 1

    return ImportResult(
        added=added,
        updated=updated,
        total=len(results),
        recipes=results,
    )


# ── Serve Vue frontend ────────────────────────────────────────────────────────
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        index = FRONTEND_DIST / "index.html"
        return FileResponse(index) if index.exists() else {"error": "Run: cd frontend && npm run build"}
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message":  "MealPlanner API — Supabase BYOD",
            "network":  f"http://{LOCAL_IP}:8000" if LOCAL_IP else "unknown",
            "hint":     "cd frontend && npm run dev -- --host",
            "docs":     "/docs",
        }
