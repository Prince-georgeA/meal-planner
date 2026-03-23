"""
MealPlanner — FastAPI Backend v5 (Vercel edition)
==================================================
Runs as a Vercel serverless function at /api/*.
Vercel strips the /api prefix before passing requests to FastAPI,
so all routes here use / (no /api prefix).

  /api/health          → FastAPI sees /health
  /api/docs            → FastAPI sees /docs
  /api/recipes/import  → FastAPI sees /recipes/import
"""

from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from mangum import Mangum

app = FastAPI(
    title="MealPlanner API",
    version="5.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
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
@app.get("/health")
def health():
    return {"status": "ok", "mode": "supabase-byod", "version": "5.0.0"}


# ── Custom docs page ──────────────────────────────────────────────────────────
@app.get("/docs", include_in_schema=False)
def custom_docs():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MealPlanner API</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
         background:#fdf6ec;color:#2c2416;padding:32px 16px}
    .wrap{max-width:680px;margin:0 auto}
    h1{font-size:26px;font-weight:700;margin-bottom:4px}
    h1 span{color:#c1440e}
    .sub{font-size:14px;color:#a07850;margin-bottom:28px}
    .card{background:#fff9f2;border:1.5px solid #ede0cc;border-radius:14px;
          padding:22px;margin-bottom:18px}
    .method{display:inline-block;background:#c1440e;color:#fff;font-size:11px;
            font-weight:700;padding:3px 10px;border-radius:6px;margin-bottom:8px}
    .method.get{background:#6b8f71}
    .path{font-size:17px;font-weight:700;font-family:monospace;
          margin-bottom:8px;color:#2c2416}
    .desc{font-size:13px;color:#a07850;line-height:1.6;margin-bottom:14px}
    label{display:block;font-size:11px;font-weight:700;letter-spacing:.08em;
          text-transform:uppercase;color:#a07850;margin-bottom:6px}
    textarea{width:100%;min-height:300px;background:#faf6ef;
             border:1.5px solid #ede0cc;border-radius:10px;padding:12px;
             font-family:"Fira Code","Courier New",monospace;font-size:12px;
             color:#2c2416;resize:vertical;outline:none}
    textarea:focus{border-color:#c1440e}
    .btn{display:inline-flex;align-items:center;gap:8px;background:#c1440e;
         color:#fff;border:none;border-radius:10px;padding:10px 22px;
         font-size:14px;font-weight:600;cursor:pointer;margin-top:12px;
         transition:opacity .15s}
    .btn:hover{opacity:.88}
    .btn:disabled{opacity:.5;cursor:not-allowed}
    .btn.green{background:#6b8f71}
    .result{margin-top:14px;background:#faf6ef;border:1.5px solid #ede0cc;
            border-radius:10px;padding:14px;font-family:monospace;font-size:12px;
            white-space:pre-wrap;max-height:280px;overflow-y:auto;display:none}
    .result.show{display:block}
    .result.ok{border-color:#a5d6a7;background:#e8f5e9;color:#1b5e20}
    .result.err{border-color:#fcc;background:#fff5f5;color:#c0392b}
    .row{display:flex;align-items:center;gap:12px}
    #health-out{font-size:13px;font-family:monospace}
  </style>
</head>
<body>
<div class="wrap">
  <h1>Meal<span>Planner</span> API</h1>
  <p class="sub">Bulk recipe import — paste your Supabase credentials and recipes below</p>

  <div class="card">
    <div class="method get">GET</div>
    <div class="path">/api/health</div>
    <div class="desc">Verify the API is running.</div>
    <div class="row">
      <button class="btn green" onclick="checkHealth()">Check health</button>
      <span id="health-out"></span>
    </div>
  </div>

  <div class="card">
    <div class="method">POST</div>
    <div class="path">/api/recipes/import</div>
    <div class="desc">
      Bulk-import recipes into your Supabase project.<br>
      <strong>replace_all: false</strong> — merges by name, appends new ones.<br>
      <strong>replace_all: true</strong> — wipes existing recipes first.
    </div>
    <label>Request body (JSON)</label>
    <textarea id="body">{
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
    <button class="btn" id="run-btn" onclick="runImport()">&#9654; Run Import</button>
    <pre class="result" id="out"></pre>
  </div>
</div>
<script>
async function checkHealth(){
  const el=document.getElementById("health-out");
  el.textContent="checking…";
  try{
    const r=await fetch("/api/health");
    const d=await r.json();
    el.textContent="✓ "+JSON.stringify(d);
    el.style.color="#2e7d32";
  }catch(e){el.textContent="✗ "+e.message;el.style.color="#c0392b"}
}
async function runImport(){
  const btn=document.getElementById("run-btn");
  const out=document.getElementById("out");
  btn.disabled=true;btn.textContent="⏳ Running…";
  out.className="result show";out.textContent="Sending…";
  try{
    const body=document.getElementById("body").value;
    JSON.parse(body);
    const r=await fetch("/api/recipes/import",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:body
    });
    const d=await r.json();
    out.className=r.ok?"result show ok":"result show err";
    out.textContent=JSON.stringify(d,null,2);
  }catch(e){
    out.className="result show err";
    out.textContent="Error: "+e.message;
  }
  btn.disabled=false;btn.textContent="▶ Run Import";
}
</script>
</body>
</html>"""
    return HTMLResponse(html)


# ── Bulk import ───────────────────────────────────────────────────────────────
@app.post("/recipes/import", response_model=ImportResult)
async def import_recipes(payload: ImportPayload):
    """
    Bulk-import recipes into the user's own Supabase project.
    Credentials are used only for this request — never stored server-side.
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

        r = await client.get(f"{rest}/recipes?select=id,name", headers=headers)
        if r.status_code == 401:
            raise HTTPException(401, "Invalid Supabase credentials — check your URL and anon key")
        if r.status_code not in (200, 206):
            raise HTTPException(502, f"Supabase error: {r.text}")

        existing = r.json()

        if payload.replace_all and existing:
            dr = await client.delete(
                f"{rest}/recipes?id=gte.0",
                headers={**headers, "Prefer": "return=minimal"},
            )
            if dr.status_code not in (200, 204):
                raise HTTPException(502, f"Failed to clear recipes: {dr.text}")
            existing = []

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
                pr = await client.post(f"{rest}/recipes", json=data, headers=headers)
                if pr.status_code not in (200, 201):
                    raise HTTPException(502, f"Failed to insert '{recipe.name}': {pr.text}")
                inserted = pr.json()
                new_id   = inserted[0]["id"] if isinstance(inserted, list) else inserted["id"]
                results.append({**data, "id": new_id})
                name_to_id[key_lower] = new_id
                added += 1

    return ImportResult(added=added, updated=updated, total=len(results), recipes=results)


# Vercel serverless handler — lifespan="off" prevents startup crash
handler = Mangum(app, lifespan="off")
