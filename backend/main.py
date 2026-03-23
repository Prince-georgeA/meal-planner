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
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# ── App ───────────────────────────────────────────────────────────────────────
# Vercel serverless doesn't serve Swagger UI static assets,
# so we disable built-in docs and provide a lightweight custom page.
app = FastAPI(
    title="MealPlanner API",
    version="5.0.0",
    docs_url=None,
    redoc_url=None,
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


@app.get("/api/docs", include_in_schema=False)
def custom_docs():
    """Lightweight API docs page — works on Vercel serverless."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MealPlanner API Docs</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #fdf6ec; color: #2c2416; padding: 32px 16px; }
    .wrap { max-width: 680px; margin: 0 auto; }
    h1 { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
    h1 span { color: #c1440e; }
    .sub { font-size: 14px; color: #a07850; margin-bottom: 32px; }
    .card { background: #fff9f2; border: 1.5px solid #ede0cc; border-radius: 14px;
            padding: 24px; margin-bottom: 20px; }
    .method { display: inline-block; background: #c1440e; color: #fff;
              font-size: 11px; font-weight: 700; padding: 3px 10px;
              border-radius: 6px; letter-spacing: .06em; margin-bottom: 10px; }
    .path { font-size: 17px; font-weight: 700; font-family: monospace;
            margin-bottom: 8px; color: #2c2416; }
    .desc { font-size: 13.5px; color: #a07850; line-height: 1.6; margin-bottom: 16px; }
    label { display: block; font-size: 11px; font-weight: 700; letter-spacing: .08em;
            text-transform: uppercase; color: #a07850; margin-bottom: 5px; }
    textarea { width: 100%; min-height: 320px; background: #faf6ef;
               border: 1.5px solid #ede0cc; border-radius: 10px; padding: 12px;
               font-family: "Fira Code", "Courier New", monospace; font-size: 12px;
               color: #2c2416; resize: vertical; outline: none; }
    textarea:focus { border-color: #c1440e; }
    .btn { display: inline-flex; align-items: center; gap: 8px;
           background: #c1440e; color: #fff; border: none; border-radius: 10px;
           padding: 11px 24px; font-size: 14px; font-weight: 600;
           cursor: pointer; margin-top: 14px; transition: opacity .15s; }
    .btn:hover { opacity: .88; }
    .btn:disabled { opacity: .5; cursor: not-allowed; }
    .result { margin-top: 16px; background: #faf6ef; border: 1.5px solid #ede0cc;
              border-radius: 10px; padding: 14px; font-family: monospace;
              font-size: 12px; white-space: pre-wrap; max-height: 300px;
              overflow-y: auto; display: none; }
    .result.show { display: block; }
    .result.ok  { border-color: #a5d6a7; background: #e8f5e9; color: #1b5e20; }
    .result.err { border-color: #fcc; background: #fff5f5; color: #c0392b; }
    .health-row { display: flex; align-items: center; gap: 12px; }
    .health-btn { background: #6b8f71; }
    #health-out { font-size: 13px; color: #2e7d32; font-family: monospace; }
  </style>
</head>
<body>
<div class="wrap">
  <h1>Meal<span>Planner</span> API</h1>
  <p class="sub">Bulk recipe import — paste your Supabase credentials and recipe list below</p>

  <!-- Health -->
  <div class="card">
    <div class="method">GET</div>
    <div class="path">/api/health</div>
    <div class="desc">Check the API is running.</div>
    <div class="health-row">
      <button class="btn health-btn" onclick="checkHealth()">Check health</button>
      <span id="health-out"></span>
    </div>
  </div>

  <!-- Import -->
  <div class="card">
    <div class="method">POST</div>
    <div class="path">/api/recipes/import</div>
    <div class="desc">
      Bulk-import recipes directly into your Supabase project.<br>
      <strong>replace_all: false</strong> — updates existing by name, appends new.<br>
      <strong>replace_all: true</strong> — wipes all recipes first, then inserts.
    </div>
    <label>Request Body (JSON)</label>
    <textarea id="import-body">{
  "supabase_url": "https://xxxxxxxxxxxx.supabase.co",
  "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "replace_all": false,
  "recipes": [
    {
      "name": "Avocado Toast",
      "emoji": "🥑",
      "category": "breakfast",
      "ingredients": ["2 slices sourdough", "1 avocado", "Salt", "Chilli flakes", "Lemon juice"]
    },
    {
      "name": "Pasta Arrabiata",
      "emoji": "🍝",
      "category": "dinner",
      "ingredients": ["300g penne", "400g tinned tomatoes", "3 garlic cloves", "Red chilli", "Olive oil"]
    }
  ]
}</textarea>
    <button class="btn" id="import-btn" onclick="runImport()">▶ Run Import</button>
    <pre class="result" id="import-out"></pre>
  </div>
</div>

<script>
  async function checkHealth() {
    const el = document.getElementById("health-out")
    el.textContent = "checking…"
    try {
      const r = await fetch("/api/health")
      const d = await r.json()
      el.textContent = "✓ " + JSON.stringify(d)
    } catch(e) { el.textContent = "✗ " + e.message }
  }

  async function runImport() {
    const btn = document.getElementById("import-btn")
    const out = document.getElementById("import-out")
    btn.disabled = true
    btn.textContent = "⏳ Running…"
    out.className = "result show"
    out.textContent = "Sending request…"
    try {
      const body = document.getElementById("import-body").value
      JSON.parse(body)  // validate JSON first
      const r = await fetch("/api/recipes/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
      })
      const d = await r.json()
      out.className = r.ok ? "result show ok" : "result show err"
      out.textContent = JSON.stringify(d, null, 2)
    } catch(e) {
      out.className = "result show err"
      out.textContent = "Error: " + e.message
    }
    btn.disabled = false
    btn.textContent = "▶ Run Import"
  }
</script>
</body>
</html>"""
    return HTMLResponse(html)


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
