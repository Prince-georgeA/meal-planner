"""
MealPlanner — FastAPI Backend v5 (Vercel edition)
==================================================
Runs as a Vercel serverless function at /api/*.
The Vue frontend is served by Vercel's CDN as static files.

This backend has one job:
  POST /api/recipes/import — bulk-load recipes into a user's own Supabase DB

No user data is stored here. Each user connects their own Supabase project
via the connection screen in the app.

Local dev (Vite proxies /api → port 8000):
  cd backend && python -m uvicorn main:app --reload --port 8000
"""

from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MealPlanner API",
    description=(
        "Bulk recipe import into your own Supabase project.\n\n"
        "## How to use\n"
        "1. Open `/api/docs`\n"
        "2. Find `POST /api/recipes/import`\n"
        "3. Click **Try it out**\n"
        "4. Paste your Supabase URL, anon key, and recipe list\n"
        "5. Click **Execute** — recipes appear in the app immediately"
    ),
    version="5.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

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

    - `supabase_url` — Your project URL e.g. `https://xxxx.supabase.co`
    - `supabase_key` — Your project **anon** (public) key
    - `replace_all`  — `false` (default): merge by name. `true`: wipe and reload.
    - `recipes`      — List of recipes to import

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
          "ingredients": ["Roasted semiya", "Onion", "Green chilli", "Mustard seeds", "Curry leaves"]
        }
      ]
    }
    ```
    """
    supabase_url: str
    supabase_key: str
    replace_all:  bool        = False
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
    }


# ── Bulk import ───────────────────────────────────────────────────────────────
@app.post("/api/recipes/import", response_model=ImportResult, tags=["Recipes"])
async def import_recipes(payload: ImportPayload):
    """
    Bulk-import recipes into the user's own Supabase project.

    Credentials are used only for this request — never stored server-side.

    - **replace_all = false**: recipes with the same name are updated; new names appended.
    - **replace_all = true**: all existing recipes are deleted first, then re-inserted.
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

        # Fetch existing recipes
        r = await client.get(f"{rest}/recipes?select=id,name", headers=headers)
        if r.status_code == 401:
            raise HTTPException(401, "Invalid Supabase credentials — check your URL and anon key")
        if r.status_code not in (200, 206):
            raise HTTPException(502, f"Supabase error: {r.text}")

        existing = r.json()

        # replace_all: wipe first
        if payload.replace_all and existing:
            dr = await client.delete(
                f"{rest}/recipes?id=gte.0",
                headers={**headers, "Prefer": "return=minimal"},
            )
            if dr.status_code not in (200, 204):
                raise HTTPException(502, f"Failed to clear recipes: {dr.text}")
            existing = []

        # Build name → id index for duplicate detection
        name_to_id = {row["name"].lower(): row["id"] for row in existing}

        added, updated, results = 0, 0, []

        for recipe in payload.recipes:
            data = {
                "name":        recipe.name,
                "emoji":       recipe.emoji,
                "category":    recipe.category,
                "ingredients": recipe.ingredients,
            }
            key_lower = recipe.name.lower()

            if key_lower in name_to_id:
                # UPDATE
                existing_id = name_to_id[key_lower]
                pr = await client.patch(
                    f"{rest}/recipes?id=eq.{existing_id}",
                    json=data, headers=headers,
                )
                if pr.status_code not in (200, 204):
                    raise HTTPException(502, f"Failed to update '{recipe.name}': {pr.text}")
                results.append({**data, "id": existing_id})
                updated += 1
            else:
                # INSERT
                pr = await client.post(f"{rest}/recipes", json=data, headers=headers)
                if pr.status_code not in (200, 201):
                    raise HTTPException(502, f"Failed to insert '{recipe.name}': {pr.text}")
                inserted = pr.json()
                new_id   = inserted[0]["id"] if isinstance(inserted, list) else inserted["id"]
                results.append({**data, "id": new_id})
                name_to_id[key_lower] = new_id
                added += 1

    return ImportResult(added=added, updated=updated, total=len(results), recipes=results)
