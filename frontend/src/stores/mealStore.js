/**
 * MealPlanner — Pinia Store (Supabase + full features)
 * =====================================================
 * All data lives in the user's own Supabase project.
 * Features: weeks, calendar view, store tagging, ingredient comments,
 *           calendar↔week sync, WhatsApp shopping list.
 */

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getClient } from '../lib/supabase.js'

// ── Constants ─────────────────────────────────────────────────────────────
const AUTO_CLEAR_MS = 2 * 24 * 60 * 60 * 1000  // 2 days

export const CAT_META = {
  breakfast: { emoji: '☀️',  label: 'Breakfast',     colorClass: 'cat-breakfast', pillClass: 'pill-breakfast' },
  lunch:     { emoji: '🌿', label: 'Lunch',          colorClass: 'cat-lunch',     pillClass: 'pill-lunch'     },
  dinner:    { emoji: '🌙', label: 'Dinner',         colorClass: 'cat-dinner',    pillClass: 'pill-dinner'    },
  snacks:    { emoji: '🍎', label: 'Snacks/Fruits',  colorClass: 'cat-snacks',    pillClass: 'pill-snacks'    },
}
export const CATEGORIES = Object.keys(CAT_META)

export const SEED_STORES = [
  { id: 's1', name: 'Market',  emoji: '🏪', color: '#6b8f71', position: 0 },
  { id: 's2', name: 'Woolies', emoji: '🛒', color: '#007837', position: 1 },
  { id: 's3', name: 'Coles',   emoji: '🔴', color: '#d62b2b', position: 2 },
  { id: 's4', name: 'Other',   emoji: '🛍️', color: '#a07850', position: 3 },
]

// ── Supabase helpers ──────────────────────────────────────────────────────
function db() {
  const client = getClient()
  if (!client) throw new Error('Supabase not connected')
  return client
}

async function sbInsert(table, data) {
  const { data: row, error } = await db().from(table).insert(data).select().single()
  if (error) throw error
  return row
}
async function sbUpsert(table, data) {
  const { error } = await db().from(table).upsert(data)
  if (error) throw error
}
async function sbUpdate(table, id, data) {
  const { error } = await db().from(table).update(data).eq('id', id)
  if (error) throw error
}
async function sbDelete(table, id) {
  const { error } = await db().from(table).delete().eq('id', id)
  if (error) throw error
}

// ── Store ─────────────────────────────────────────────────────────────────
export const useMealStore = defineStore('meal', () => {

  // ── State ─────────────────────────────────────────────────────────────
  const recipes            = ref([])
  const weeks              = ref([])
  const stores             = ref([])
  const recipeStores       = ref({})   // { [recipeId]: { [ingIdx]: storeId } }
  const weekOverrides      = ref({})   // { [weekId:foodId:ingIdx]: storeId }
  const checkedIngredients = ref({})   // { 'weekId:foodId:ingIdx': true }
  const ingredientComments = ref({})   // { 'weekId:foodId:ingIdx': { text, createdAt } }
  const lastActivityAt     = ref({})   // { [weekId]: timestamp }
  const calendarMeals      = ref({})   // { 'YYYY-MM-DD': { breakfast:[…], … } }
  const toast              = ref(null)
  const syncStatus         = ref('idle')

  let _toastTimer = null

  // ── Toast ──────────────────────────────────────────────────────────────
  function showToast(message, type = 'success') {
    if (_toastTimer) clearTimeout(_toastTimer)
    toast.value = { message, type }
    _toastTimer = setTimeout(() => { toast.value = null }, 2800)
  }

  // ── Sync helpers ───────────────────────────────────────────────────────
  function setSaving() { syncStatus.value = 'saving' }
  function setSaved()  {
    syncStatus.value = 'saved'
    setTimeout(() => { if (syncStatus.value === 'saved') syncStatus.value = 'idle' }, 2000)
  }
  function setOffline() { syncStatus.value = 'offline' }

  async function withSync(fn) {
    setSaving()
    try {
      const result = await fn()
      setSaved()
      return result
    } catch (err) {
      console.error('Supabase error:', err)
      setOffline()
      showToast('Sync failed — check connection', 'error')
      throw err
    }
  }

  // ── Init: load all data from Supabase ──────────────────────────────────
  async function initFromServer() {
    const client = getClient()
    if (!client) { syncStatus.value = 'offline'; return }
    syncStatus.value = 'saving'
    try {
      const [
        { data: recipesData,   error: e1 },
        { data: weeksData,     error: e2 },
        { data: foodsData,     error: e3 },
        { data: storesData,    error: e4 },
        { data: ingStores,     error: e5 },
        { data: checkedData,   error: e6 },
        { data: commentsData,  error: e7 },
        { data: calData,       error: e8 },
      ] = await Promise.all([
        client.from('recipes').select('*').order('id'),
        client.from('weeks').select('*').order('id'),
        client.from('week_foods').select('*').order('position').order('id'),
        client.from('stores').select('*').order('position'),
        client.from('ingredient_stores').select('*'),
        client.from('checked_ingredients').select('*'),
        client.from('ingredient_comments').select('*'),
        client.from('calendar_meals').select('*'),
      ])

      if (e1 || e2 || e3) { syncStatus.value = 'offline'; return }

      // Recipes
      recipes.value = (recipesData || []).map(r => ({ ...r, ingredients: r.ingredients || [] }))

      // Weeks + foods
      const blankCats = () => ({ breakfast: [], lunch: [], dinner: [], snacks: [] })
      const foodsByWeek = {}
      for (const f of (foodsData || [])) {
        if (!foodsByWeek[f.week_id]) foodsByWeek[f.week_id] = blankCats()
        foodsByWeek[f.week_id][f.category].push({
          id: f.id, name: f.name, emoji: f.emoji,
          recipeId: f.recipe_id,
          customIngredients: f.custom_ingredients || [],
          syncedFromCalendar: f.synced_from_calendar || false,
        })
      }
      weeks.value = (weeksData || []).map(w => ({
        id: w.id, label: w.label, dates: w.dates || '',
        dateFrom: w.date_from || null,
        dateTo:   w.date_to   || null,
        createdAt: new Date(w.created_at).getTime(),
        categories: foodsByWeek[w.id] || blankCats(),
      }))

      // Stores (seed if empty)
      if (!storesData?.length) {
        await client.from('stores').insert(SEED_STORES)
        stores.value = [...SEED_STORES]
      } else {
        stores.value = storesData
      }

      // recipeStores map
      const rsMap = {}
      for (const { recipe_id, ing_index, store_id } of (ingStores || [])) {
        if (!rsMap[recipe_id]) rsMap[recipe_id] = {}
        rsMap[recipe_id][ing_index] = store_id
      }
      recipeStores.value = rsMap

      // checkedIngredients
      const checked = {}
      for (const { week_id, food_id, ing_index } of (checkedData || [])) {
        checked[`${week_id}:${food_id}:${ing_index}`] = true
      }
      checkedIngredients.value = checked

      // ingredientComments
      const comments = {}
      for (const { week_id, food_id, ing_index, text, created_at } of (commentsData || [])) {
        comments[`${week_id}:${food_id}:${ing_index}`] = { text, createdAt: new Date(created_at).getTime() }
      }
      ingredientComments.value = comments

      // calendarMeals
      const calMap = {}
      for (const row of (calData || [])) {
        if (!calMap[row.date_str]) calMap[row.date_str] = { breakfast: [], lunch: [], dinner: [], snacks: [] }
        calMap[row.date_str][row.category].push({
          recipeId: row.recipe_id,
          name:     row.name,
          emoji:    row.emoji,
        })
      }
      calendarMeals.value = calMap

      syncStatus.value = 'idle'
    } catch (err) {
      console.error('initFromServer failed:', err)
      syncStatus.value = 'offline'
    }
  }

  // ── Auto-clear ─────────────────────────────────────────────────────────
  function checkAutoClear(weekId) {
    const last = lastActivityAt.value[weekId]
    if (!last) return
    if (Date.now() - last >= AUTO_CLEAR_MS) {
      clearWeekSelections(weekId, true)
      showToast('🔄 Selections auto-cleared (2 days since last use)', 'info')
    }
  }

  // ── Recipe actions ─────────────────────────────────────────────────────
  async function addRecipe(payload) {
    const data = {
      name:        payload.name.trim(),
      emoji:       payload.emoji || '🍽️',
      category:    payload.category || null,
      ingredients: payload.ingredients.filter(i => i.trim()),
    }
    return await withSync(async () => {
      const row = await sbInsert('recipes', data)
      const recipe = { ...row, ingredients: row.ingredients || [] }
      recipes.value.push(recipe)
      showToast(`"${recipe.name}" added to recipe library`)
      return recipe
    })
  }

  async function updateRecipe(id, payload) {
    const idx = recipes.value.findIndex(r => r.id === id)
    if (idx === -1) return
    const updated = {
      name:        payload.name.trim(),
      emoji:       payload.emoji || recipes.value[idx].emoji,
      category:    payload.category || null,
      ingredients: payload.ingredients.filter(i => i.trim()),
    }
    recipes.value[idx] = { ...recipes.value[idx], ...updated }
    withSync(() => sbUpdate('recipes', id, updated))
    showToast('Recipe updated')
  }

  async function deleteRecipe(id) {
    const idx = recipes.value.findIndex(r => r.id === id)
    if (idx === -1) return
    recipes.value.splice(idx, 1)
    delete recipeStores.value[id]
    withSync(() => sbDelete('recipes', id))
    showToast('Recipe removed', 'info')
  }

  function getRecipeById(id) {
    return recipes.value.find(r => r.id === id) || null
  }

  const recipesByCategory = computed(() => {
    const grouped = { breakfast: [], lunch: [], dinner: [], snacks: [], uncategorised: [] }
    for (const r of recipes.value) {
      const key = (r.category && grouped[r.category] !== undefined) ? r.category : 'uncategorised'
      grouped[key].push(r)
    }
    return grouped
  })

  // ── Week actions ───────────────────────────────────────────────────────
  async function addWeek(label = null, dateFrom = null, dateTo = null) {
    const n = weeks.value.length + 1
    const wLabel = label || `Week ${n}`
    let fromTs = null, toTs = null
    if (dateFrom && dateTo) {
      const f = new Date(dateFrom); f.setHours(0,0,0,0)
      const t = new Date(dateTo);   t.setHours(0,0,0,0)
      fromTs = f.getTime(); toTs = t.getTime()
    }
    return await withSync(async () => {
      const row = await sbInsert('weeks', {
        label: wLabel, dates: '',
        date_from: fromTs, date_to: toTs,
      })
      const week = {
        id: row.id, label: row.label, dates: '',
        dateFrom: fromTs, dateTo: toTs,
        createdAt: new Date(row.created_at).getTime(),
        categories: { breakfast: [], lunch: [], dinner: [], snacks: [] },
      }
      weeks.value.push(week)
      showToast(`${week.label} added!`)
      return week
    })
  }

  async function copyWeek(sourceWeekId) {
    const source = weeks.value.find(w => w.id === sourceWeekId)
    if (!source) return null
    const n = weeks.value.length + 1
    return await withSync(async () => {
      const wRow = await sbInsert('weeks', { label: `Week ${n}`, dates: '', date_from: null, date_to: null })
      const newWeek = {
        id: wRow.id, label: wRow.label, dates: '',
        dateFrom: null, dateTo: null,
        createdAt: new Date(wRow.created_at).getTime(),
        categories: { breakfast: [], lunch: [], dinner: [], snacks: [] },
      }
      let pos = 0
      for (const [cat, foods] of Object.entries(source.categories)) {
        for (const food of foods) {
          const fRow = await sbInsert('week_foods', {
            week_id: wRow.id, category: cat,
            recipe_id: food.recipeId, name: food.name, emoji: food.emoji,
            custom_ingredients: food.customIngredients || [],
            synced_from_calendar: false, position: pos++,
          })
          newWeek.categories[cat].push({
            id: fRow.id, name: fRow.name, emoji: fRow.emoji,
            recipeId: fRow.recipe_id,
            customIngredients: fRow.custom_ingredients || [],
            syncedFromCalendar: false,
          })
        }
      }
      weeks.value.push(newWeek)
      showToast(`Copied "${source.label}" → "${newWeek.label}"`)
      return newWeek
    })
  }

  async function updateWeekLabel(weekId, label, dates, dateFrom = null, dateTo = null) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return
    const updates = {}
    if (label !== undefined) { week.label = label.trim() || week.label; updates.label = week.label }
    if (dates !== undefined) { week.dates = dates.trim(); updates.dates = week.dates }
    if (dateFrom !== null && dateTo !== null) {
      const f = new Date(dateFrom); f.setHours(0,0,0,0)
      const t = new Date(dateTo);   t.setHours(0,0,0,0)
      week.dateFrom = f.getTime(); week.dateTo = t.getTime()
      updates.date_from = week.dateFrom; updates.date_to = week.dateTo
    }
    withSync(() => sbUpdate('weeks', weekId, updates))
    showToast('Week updated')
    syncCalendarToWeeks()
  }

  async function deleteWeek(weekId) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return
    weeks.value = weeks.value.filter(w => w.id !== weekId)
    const prefix = `${weekId}:`
    for (const key of Object.keys(checkedIngredients.value)) {
      if (key.startsWith(prefix)) delete checkedIngredients.value[key]
    }
    for (const key of Object.keys(ingredientComments.value)) {
      if (key.startsWith(prefix)) delete ingredientComments.value[key]
    }
    delete lastActivityAt.value[weekId]
    withSync(() => sbDelete('weeks', weekId))
    showToast(`"${week.label}" deleted`, 'info')
  }

  // ── Food item actions ──────────────────────────────────────────────────
  async function addFoodToWeek(weekId, category, payload) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week || !week.categories[category]) return null
    if (payload.recipeId) {
      const exists = week.categories[category].some(f => f.recipeId === payload.recipeId)
      if (exists) {
        showToast(`"${payload.name}" is already in ${CAT_META[category].label}`, 'info')
        return null
      }
    }
    return await withSync(async () => {
      const pos = week.categories[category].length
      const row = await sbInsert('week_foods', {
        week_id: weekId, category,
        recipe_id: payload.recipeId || null,
        name: payload.name.trim(),
        emoji: payload.emoji || '🍽️',
        custom_ingredients: payload.customIngredients || [],
        synced_from_calendar: payload.syncedFromCalendar || false,
        position: pos,
      })
      const food = {
        id: row.id, name: row.name, emoji: row.emoji,
        recipeId: row.recipe_id,
        customIngredients: row.custom_ingredients || [],
        syncedFromCalendar: row.synced_from_calendar || false,
      }
      week.categories[category].push(food)
      showToast(`"${food.name}" added to ${CAT_META[category].label}`)
      return food
    })
  }

  async function removeFoodFromWeek(weekId, category, foodId) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return
    week.categories[category] = week.categories[category].filter(f => f.id !== foodId)
    const prefix = `${weekId}:${foodId}:`
    for (const key of Object.keys(checkedIngredients.value)) {
      if (key.startsWith(prefix)) delete checkedIngredients.value[key]
    }
    for (const key of Object.keys(ingredientComments.value)) {
      if (key.startsWith(prefix)) delete ingredientComments.value[key]
    }
    withSync(() => sbDelete('week_foods', foodId))
    showToast('Item removed', 'info')
  }

  function getFoodIngredients(food) {
    if (food.recipeId) {
      const recipe = getRecipeById(food.recipeId)
      return recipe ? recipe.ingredients : []
    }
    return food.customIngredients || []
  }

  // ── Ingredient checkbox ────────────────────────────────────────────────
  async function toggleIngredient(weekId, foodId, ingIndex) {
    const key = `${weekId}:${foodId}:${ingIndex}`
    const isNowChecked = !checkedIngredients.value[key]
    checkedIngredients.value[key] = isNowChecked
    lastActivityAt.value[weekId] = Date.now()
    if (isNowChecked) {
      withSync(() =>
        db().from('checked_ingredients')
          .insert({ week_id: weekId, food_id: foodId, ing_index: ingIndex })
          .then(({ error }) => { if (error && error.code !== '23505') throw error })
      )
    } else {
      withSync(() =>
        db().from('checked_ingredients')
          .delete().eq('week_id', weekId).eq('food_id', foodId).eq('ing_index', ingIndex)
          .then(({ error }) => { if (error) throw error })
      )
    }
  }

  function isIngredientChecked(weekId, foodId, ingIndex) {
    return !!checkedIngredients.value[`${weekId}:${foodId}:${ingIndex}`]
  }

  async function clearWeekSelections(weekId, silent = false) {
    const prefix = `${weekId}:`
    for (const key of Object.keys(checkedIngredients.value)) {
      if (key.startsWith(prefix)) delete checkedIngredients.value[key]
    }
    delete lastActivityAt.value[weekId]
    withSync(() =>
      db().from('checked_ingredients').delete().eq('week_id', weekId)
        .then(({ error }) => { if (error) throw error })
    )
    if (!silent) showToast('All selections cleared', 'info')
  }

  function getCheckedCountForWeek(weekId) {
    const prefix = `${weekId}:`
    return Object.entries(checkedIngredients.value).filter(([k, v]) => k.startsWith(prefix) && v).length
  }

  function getCheckedCountForFood(weekId, foodId) {
    const prefix = `${weekId}:${foodId}:`
    return Object.entries(checkedIngredients.value).filter(([k, v]) => k.startsWith(prefix) && v).length
  }

  // ── Ingredient comments ────────────────────────────────────────────────
  function _ingKey(weekId, foodId, ingIdx) {
    return `${weekId}:${foodId}:${ingIdx}`
  }

  function getIngredientComment(weekId, foodId, ingIdx) {
    return ingredientComments.value[_ingKey(weekId, foodId, ingIdx)]?.text || ''
  }

  async function setIngredientComment(weekId, foodId, ingIdx, text) {
    const key     = _ingKey(weekId, foodId, ingIdx)
    const cleaned = text?.trim() || ''
    if (!cleaned) {
      delete ingredientComments.value[key]
      withSync(() =>
        db().from('ingredient_comments')
          .delete().eq('week_id', weekId).eq('food_id', foodId).eq('ing_index', ingIdx)
          .then(({ error }) => { if (error) throw error })
      )
    } else {
      ingredientComments.value[key] = { text: cleaned, createdAt: Date.now() }
      withSync(() =>
        db().from('ingredient_comments')
          .upsert({ week_id: weekId, food_id: foodId, ing_index: ingIdx, text: cleaned })
          .then(({ error }) => { if (error) throw error })
      )
    }
  }

  function pruneExpiredIngredientComments() {
    const now = Date.now()
    for (const [key, val] of Object.entries(ingredientComments.value)) {
      const { createdAt } = val
      if (!createdAt || (now - createdAt) >= AUTO_CLEAR_MS) {
        delete ingredientComments.value[key]
      }
    }
  }

  // ── Store management ───────────────────────────────────────────────────
  async function addStore(payload) {
    const s = {
      id:       's' + Date.now(),
      name:     payload.name.trim(),
      emoji:    payload.emoji || '🏬',
      color:    payload.color || '#888888',
      position: stores.value.length,
    }
    return await withSync(async () => {
      await db().from('stores').insert(s)
      stores.value.push(s)
      showToast(`"${s.name}" added`)
      return s
    })
  }

  async function deleteStore(storeId) {
    stores.value = stores.value.filter(s => s.id !== storeId)
    withSync(() => db().from('stores').delete().eq('id', storeId).then(({ error }) => { if (error) throw error }))
    showToast('Store removed', 'info')
  }

  function storeUsageCount(storeId) {
    return Object.values(recipeStores.value).reduce((acc, ingMap) =>
      acc + Object.values(ingMap).filter(s => s === storeId).length, 0)
  }

  function resolveIngStore(weekId, foodId, ingIdx, recipeId) {
    const overrideKey = `${weekId}:${foodId}:${ingIdx}`
    if (weekOverrides.value[overrideKey] !== undefined) return weekOverrides.value[overrideKey]
    return recipeStores.value[recipeId]?.[ingIdx] ?? null
  }

  async function setIngStore(weekId, foodId, ingIdx, recipeId, storeId) {
    const overrideKey = `${weekId}:${foodId}:${ingIdx}`
    if (storeId === null) {
      delete weekOverrides.value[overrideKey]
    } else {
      weekOverrides.value[overrideKey] = storeId
    }
    if (recipeId) await setRecipeIngStore(recipeId, ingIdx, storeId)
  }

  async function setRecipeIngStore(recipeId, ingIdx, storeId) {
    if (!recipeStores.value[recipeId]) recipeStores.value[recipeId] = {}
    if (storeId === null) {
      delete recipeStores.value[recipeId][ingIdx]
      withSync(() =>
        db().from('ingredient_stores').delete()
          .eq('recipe_id', recipeId).eq('ing_index', ingIdx)
          .then(({ error }) => { if (error) throw error })
      )
    } else {
      recipeStores.value[recipeId][ingIdx] = storeId
      withSync(() =>
        db().from('ingredient_stores')
          .upsert({ recipe_id: recipeId, ing_index: ingIdx, store_id: storeId })
          .then(({ error }) => { if (error) throw error })
      )
    }
  }

  // ── Shopping list / WhatsApp ───────────────────────────────────────────
  function buildShoppingList(weekId) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return {}
    const result = {}
    for (const [cat, foods] of Object.entries(week.categories)) {
      const items = []
      for (const food of foods) {
        const ings = getFoodIngredients(food)
        ings.forEach((ing, idx) => {
          if (isIngredientChecked(weekId, food.id, idx)) {
            items.push({ food: food.name, ingredient: ing })
          }
        })
      }
      if (items.length) result[cat] = items
    }
    return result
  }

  function buildWhatsAppText(weekId) {
    pruneExpiredIngredientComments()
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return ''
    const label = week.label + (week.dates ? ` (${week.dates})` : '')
    let msg = `🛒 *Shopping List — ${label}*\n📅 Market Day: Friday / Saturday\n\n`
    const storeMap = {}
    for (const [cat, foods] of Object.entries(week.categories)) {
      for (const food of foods) {
        const ings = getFoodIngredients(food)
        ings.forEach((ing, idx) => {
          if (!isIngredientChecked(weekId, food.id, idx)) return
          const storeId = resolveIngStore(weekId, food.id, idx, food.recipeId) || '__none__'
          const comment = getIngredientComment(weekId, food.id, idx)
          if (!storeMap[storeId]) storeMap[storeId] = {}
          if (!storeMap[storeId][cat]) storeMap[storeId][cat] = []
          storeMap[storeId][cat].push({ ingredient: ing, food: food.name, comment })
        })
      }
    }
    for (const store of stores.value) {
      const catMap = storeMap[store.id]
      if (!catMap) continue
      msg += `*${store.emoji} ${store.name}*\n`
      for (const cat of CATEGORIES) {
        const items = catMap[cat]
        if (!items?.length) continue
        msg += `  _${CAT_META[cat].emoji} ${CAT_META[cat].label}_\n`
        items.forEach(({ ingredient, food, comment }) => {
          msg += `    • ${ingredient}${comment ? ` — ${comment}` : ''}  _(${food})_\n`
        })
      }
      msg += '\n'
    }
    const untagged = storeMap['__none__']
    if (untagged) {
      msg += `*🛍️ Untagged*\n`
      for (const cat of CATEGORIES) {
        ;(untagged[cat] || []).forEach(({ ingredient, food, comment }) => {
          msg += `  • ${ingredient}${comment ? ` — ${comment}` : ''}  _(${food})_\n`
        })
      }
      msg += '\n'
    }
    msg += `_Sent from MealPlanner_ 🥘`
    return encodeURIComponent(msg)
  }

  // ── Date helpers ───────────────────────────────────────────────────────
  const _MONTHS_S = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

  function _dk(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  }
  function _dFromKey(k) {
    const [y, m, d] = k.split('-').map(Number)
    return new Date(y, m-1, d)
  }
  function _formatDateRange(from, to) {
    const f = from instanceof Date ? from : new Date(from)
    const t = to   instanceof Date ? to   : new Date(to)
    if (f.getMonth() === t.getMonth()) {
      return `${_MONTHS_S[f.getMonth()]} ${f.getDate()}–${t.getDate()}`
    }
    return `${_MONTHS_S[f.getMonth()]} ${f.getDate()} – ${_MONTHS_S[t.getMonth()]} ${t.getDate()}`
  }

  // ── Calendar meals ─────────────────────────────────────────────────────
  function getDayMeals(dateStr) {
    if (!calendarMeals.value[dateStr]) {
      calendarMeals.value[dateStr] = { breakfast: [], lunch: [], dinner: [], snacks: [] }
    }
    return calendarMeals.value[dateStr]
  }

  function syncCalendarToWeeks() {
    for (const [dateStr, meals] of Object.entries(calendarMeals.value)) {
      const date = _dFromKey(dateStr)
      date.setHours(0,0,0,0)
      const dayTs = date.getTime()
      const week  = weeks.value.find(w =>
        w.dateFrom != null && w.dateTo != null &&
        dayTs >= w.dateFrom && dayTs <= w.dateTo
      )
      if (!week) continue
      for (const [cat, items] of Object.entries(meals)) {
        if (!week.categories[cat]) continue
        for (const item of items) {
          if (!week.categories[cat].find(f => f.recipeId === item.recipeId)) {
            addFoodToWeek(week.id, cat, {
              name: item.name, emoji: item.emoji,
              recipeId: item.recipeId, customIngredients: [],
              syncedFromCalendar: true,
            })
          }
        }
      }
    }
  }

  async function addRecipeToDay(dateStr, category, recipe) {
    if (!CATEGORIES.includes(category)) return
    const day = getDayMeals(dateStr)
    if (day[category].find(i => i.recipeId === recipe.id)) {
      showToast(`"${recipe.name}" is already on this day`, 'info')
      return
    }
    day[category].push({ recipeId: recipe.id, name: recipe.name, emoji: recipe.emoji })
    // Persist to Supabase
    withSync(() =>
      db().from('calendar_meals')
        .insert({ date_str: dateStr, category, recipe_id: recipe.id, name: recipe.name, emoji: recipe.emoji })
        .then(({ error }) => { if (error) throw error })
    )
    syncCalendarToWeeks()
    showToast(`"${recipe.name}" added to calendar`)
  }

  async function removeRecipeFromDay(dateStr, category, index) {
    const day = calendarMeals.value[dateStr]
    if (!day?.[category]) return
    const removed = day[category][index]
    day[category].splice(index, 1)
    // Persist deletion
    withSync(() =>
      db().from('calendar_meals')
        .delete().eq('date_str', dateStr).eq('category', category).eq('recipe_id', removed?.recipeId)
        .then(({ error }) => { if (error) throw error })
    )
    if (removed?.recipeId != null) {
      _syncCalendarRemovalToWeeks(category, removed.recipeId)
    }
    showToast('Removed from calendar', 'info')
  }

  function _syncCalendarRemovalToWeeks(category, recipeId) {
    for (const week of weeks.value) {
      if (!week.dateFrom || !week.dateTo) continue
      const foodIdx = week.categories[category]?.findIndex(
        f => f.recipeId === recipeId && f.syncedFromCalendar
      )
      if (foodIdx === -1 || foodIdx == null) continue
      const stillExists = Object.entries(calendarMeals.value).some(([ds, meals]) => {
        const d = _dFromKey(ds); d.setHours(0,0,0,0)
        const ts = d.getTime()
        return ts >= week.dateFrom && ts <= week.dateTo &&
          (meals[category] || []).some(i => i.recipeId === recipeId)
      })
      if (!stillExists) {
        const food = week.categories[category][foodIdx]
        week.categories[category].splice(foodIdx, 1)
        const prefix = `${week.id}:${food.id}:`
        for (const key of Object.keys(checkedIngredients.value)) {
          if (key.startsWith(prefix)) delete checkedIngredients.value[key]
        }
        withSync(() => sbDelete('week_foods', food.id))
      }
    }
  }

  async function addRecipeToWeek(weekId, category, recipeId, calendarDateStr = null) {
    const recipe = getRecipeById(recipeId)
    if (!recipe) return
    const week = weeks.value.find(w => w.id === weekId)
    if (!week) return
    if (!week.categories[category].find(f => f.recipeId === recipeId)) {
      await addFoodToWeek(weekId, category, {
        name: recipe.name, emoji: recipe.emoji,
        recipeId: recipe.id, customIngredients: [],
      })
    } else {
      showToast(`"${recipe.name}" is already in ${CAT_META[category].label}`, 'info')
    }
    if (calendarDateStr) {
      await addRecipeToDay(calendarDateStr, category, recipe)
    }
  }

  function weekHasCalendarData(weekId) {
    const week = weeks.value.find(w => w.id === weekId)
    if (!week?.dateFrom || !week?.dateTo) return false
    for (const [dateStr, meals] of Object.entries(calendarMeals.value)) {
      const date = _dFromKey(dateStr); date.setHours(0,0,0,0)
      const dayTs = date.getTime()
      if (dayTs >= week.dateFrom && dayTs <= week.dateTo) {
        if (Object.values(meals).some(a => a.length > 0)) return true
      }
    }
    return false
  }

  // ── Computed ───────────────────────────────────────────────────────────
  const totalRecipes = computed(() => recipes.value.length)
  const totalWeeks   = computed(() => weeks.value.length)

  return {
    // State
    recipes, weeks, stores, recipeStores, checkedIngredients,
    ingredientComments, calendarMeals, toast, syncStatus,

    // Recipe
    addRecipe, updateRecipe, deleteRecipe, getRecipeById,

    // Week
    addWeek, copyWeek, updateWeekLabel, deleteWeek, checkAutoClear,

    // Food
    addFoodToWeek, removeFoodFromWeek, getFoodIngredients,

    // Ingredients
    toggleIngredient, isIngredientChecked, clearWeekSelections,
    getCheckedCountForWeek, getCheckedCountForFood,

    // Stores
    addStore, deleteStore, storeUsageCount,
    resolveIngStore, setIngStore, setRecipeIngStore,

    // Comments
    getIngredientComment, setIngredientComment,

    // Shopping
    buildShoppingList, buildWhatsAppText,

    // Calendar
    getDayMeals, addRecipeToDay, removeRecipeFromDay,
    syncCalendarToWeeks, addRecipeToWeek, weekHasCalendarData,
    _dk, _dFromKey, _formatDateRange,

    // Computed
    totalRecipes, totalWeeks, recipesByCategory,

    // Sync
    syncStatus, initFromServer,

    // Utils
    showToast,
  }
})
