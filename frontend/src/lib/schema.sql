-- MealPlanner — Supabase Schema v2
-- Run once in: Supabase Dashboard → SQL Editor → New Query → paste → Run

-- ── Stores ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stores (
  id       TEXT PRIMARY KEY,
  name     TEXT NOT NULL,
  emoji    TEXT NOT NULL DEFAULT '🏪',
  color    TEXT NOT NULL DEFAULT '#888888',
  position INTEGER NOT NULL DEFAULT 0
);
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON stores FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Recipes ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recipes (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  emoji       TEXT NOT NULL DEFAULT '🍽️',
  category    TEXT CHECK (category IN ('breakfast','lunch','dinner','snacks')),
  ingredients JSONB NOT NULL DEFAULT '[]',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON recipes FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Ingredient → Store mapping ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingredient_stores (
  recipe_id BIGINT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  ing_index INTEGER NOT NULL,
  store_id  TEXT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
  PRIMARY KEY (recipe_id, ing_index)
);
ALTER TABLE ingredient_stores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON ingredient_stores FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Weeks ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weeks (
  id               BIGSERIAL PRIMARY KEY,
  label            TEXT NOT NULL,
  dates            TEXT NOT NULL DEFAULT '',
  date_from        BIGINT,          -- unix ms timestamp (null = no range set)
  date_to          BIGINT,          -- unix ms timestamp
  last_activity_at BIGINT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE weeks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON weeks FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Week food items ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS week_foods (
  id                   BIGSERIAL PRIMARY KEY,
  week_id              BIGINT NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
  category             TEXT NOT NULL CHECK (category IN ('breakfast','lunch','dinner','snacks')),
  recipe_id            BIGINT REFERENCES recipes(id) ON DELETE SET NULL,
  name                 TEXT NOT NULL,
  emoji                TEXT NOT NULL DEFAULT '🍽️',
  custom_ingredients   JSONB NOT NULL DEFAULT '[]',
  synced_from_calendar BOOLEAN NOT NULL DEFAULT FALSE,
  position             INTEGER NOT NULL DEFAULT 0
);
ALTER TABLE week_foods ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON week_foods FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Checked ingredients (shopping list state) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS checked_ingredients (
  week_id   BIGINT NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
  food_id   BIGINT NOT NULL REFERENCES week_foods(id) ON DELETE CASCADE,
  ing_index INTEGER NOT NULL,
  PRIMARY KEY (week_id, food_id, ing_index)
);
ALTER TABLE checked_ingredients ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON checked_ingredients FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Ingredient comments (notes on shopping items) ─────────────────────────────
CREATE TABLE IF NOT EXISTS ingredient_comments (
  week_id   BIGINT NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
  food_id   BIGINT NOT NULL REFERENCES week_foods(id) ON DELETE CASCADE,
  ing_index INTEGER NOT NULL,
  text      TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (week_id, food_id, ing_index)
);
ALTER TABLE ingredient_comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON ingredient_comments FOR ALL TO anon USING (true) WITH CHECK (true);

-- ── Calendar meals ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS calendar_meals (
  id         BIGSERIAL PRIMARY KEY,
  date_str   TEXT NOT NULL,          -- 'YYYY-MM-DD'
  category   TEXT NOT NULL CHECK (category IN ('breakfast','lunch','dinner','snacks')),
  recipe_id  BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  emoji      TEXT NOT NULL DEFAULT '🍽️',
  UNIQUE (date_str, category, recipe_id)
);
ALTER TABLE calendar_meals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON calendar_meals FOR ALL TO anon USING (true) WITH CHECK (true);
