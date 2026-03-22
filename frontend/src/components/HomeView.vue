<template>
  <div class="home-view">

    <!-- Hero -->
    <section class="hero">
      <p class="hero-eyebrow"> Kitchen Planner</p>
      <h1 class="hero-title">Plan the  week,<br /><em>enjoy your meal</em></h1>
      <p class="hero-sub">
        Organise meals by week, tick off ingredients, and send  shopping
        list to WhatsApp on market day (Fri / Sat).
      </p>
    </section>

    <!-- Weeks / Calendar Section -->
    <section class="section">
      <div class="section-header">
        <p class="section-label">
          {{ activeTab === 'weeks' ? `📅 Your Weeks (${store.weeks.length})` : '📅 Calendar' }}
        </p>
        <!-- Tab toggle -->
        <div class="section-tab-group">
          <button
            class="section-tab"
            :class="{ active: activeTab === 'weeks' }"
            @click="activeTab = 'weeks'"
          >📋 Your Weeks</button>
          <button
            class="section-tab"
            :class="{ active: activeTab === 'calendar' }"
            @click="activeTab = 'calendar'"
          >📅 Calendar</button>
        </div>
      </div>

      <!-- Weeks grid -->
      <div v-if="activeTab === 'weeks'" class="weeks-grid">
        <WeekCard
          v-for="week in store.weeks"
          :key="week.id"
          :week="week"
          @click="$emit('open-week', week.id)"
          @copy="store.copyWeek(week.id)"
          @delete="confirmDeleteWeek(week)"
          @edit-dates="openEditDates"
        />
        <button class="btn-add-week" @click="showAddWeek = true" aria-label="Add new week">
          <span class="add-week-icon">＋</span>
          <span class="add-week-label">Add new week</span>
        </button>
      </div>

      <!-- Calendar view -->
      <CalendarView v-else @open-week="$emit('open-week', $event)" @go-weeks="activeTab = 'weeks'" />
    </section>

    <div class="divider"></div>

    <!-- Recipe Library -->
    <section class="section">
      <div class="section-header">
        <p class="section-label">📖 Recipe Library ({{ store.recipes.length }})</p>
        <button class="btn btn-ghost" @click="$emit('add-recipe')">
          ＋ Add Recipe
        </button>
      </div>

      <div v-if="store.recipes.length === 0" class="empty-state">
        <div class="empty-icon">📖</div>
        <p class="empty-text">No recipes yet — click "+ Add Recipe" to start your library</p>
      </div>

      <!-- Category accordion panels -->
      <div v-else class="lib-categories">
        <div
          v-for="cat in libCats"
          :key="cat.key"
          class="lib-cat-panel"
          :class="`lib-${cat.key}`"
        >
          <!-- Category Header (clickable) -->
          <button
            class="lib-cat-header"
            @click="toggleLibCat(cat.key)"
            :aria-expanded="openLibCats.includes(cat.key)"
          >
            <div class="lib-cat-header-left">
              <span class="lib-cat-emoji">{{ cat.emoji }}</span>
              <span class="lib-cat-name">{{ cat.label }}</span>
              <span class="lib-cat-badge">{{ cat.recipes.length }}</span>
            </div>
            <span class="lib-chevron" :class="{ open: openLibCats.includes(cat.key) }">›</span>
          </button>

          <!-- Food items list -->
          <Transition name="lib-expand">
            <div v-if="openLibCats.includes(cat.key) && cat.recipes.length > 0" class="lib-food-list">
              <div
                v-for="recipe in cat.recipes"
                :key="recipe.id"
                class="lib-food-row"
                @click="openRecipeModal(recipe)"
                role="button"
                tabindex="0"
                @keydown.enter="openRecipeModal(recipe)"
              >
                <span class="lib-food-emoji">{{ recipe.emoji }}</span>
                <div class="lib-food-info">
                  <span class="lib-food-name">{{ recipe.name }}</span>
                  <span class="lib-food-ings">{{ recipe.ingredients.length }} ingredient{{ recipe.ingredients.length !== 1 ? 's' : '' }}</span>
                </div>
                <span class="lib-food-arrow">›</span>
              </div>
            </div>
            <div v-else-if="openLibCats.includes(cat.key)" class="lib-empty">
              No recipes tagged as {{ cat.label }} yet
            </div>
          </Transition>
        </div>
      </div>
    </section>

    <!-- Add Week Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddWeek" class="modal-overlay" @click.self="showAddWeek = false">
          <div class="modal-box">
            <h2 class="modal-title">Add New Week</h2>
            <p class="modal-sub">Start blank or copy meals from an existing week</p>

            <div class="form-group">
              <label class="form-label">Week Name</label>
              <input
                class="form-input"
                v-model="newWeekLabel"
                :placeholder="`Week ${store.weeks.length + 1}`"
                @keydown.enter="handleAddWeek"
                ref="weekLabelInput"
              />
            </div>

            <!-- Date range pickers -->
            <div class="form-group">
              <label class="form-label">
                Date Range
                <span class="form-label-hint">(optional — enables calendar sync)</span>
              </label>
              <div class="date-range-row">
                <div class="date-range-field">
                  <label class="form-sublabel">From</label>
                  <input type="date" class="form-input" v-model="newWeekFrom" />
                </div>
                <div class="date-range-field">
                  <label class="form-sublabel">To</label>
                  <input type="date" class="form-input" v-model="newWeekTo" />
                </div>
              </div>
              <!-- Retroactive sync preview -->
              <div v-if="newWeekFrom && newWeekTo && syncPreviewCount > 0" class="sync-preview-note">
                🔄 <strong>{{ syncPreviewCount }} calendar meal{{ syncPreviewCount !== 1 ? 's' : '' }}</strong>
                found in this range — they'll sync into this week automatically.
              </div>
              <div v-else-if="newWeekFrom && newWeekTo" class="sync-preview-note sync-preview-none">
                No meals currently on the calendar for this range. Add them later.
              </div>
            </div>

            <div class="form-group" v-if="store.weeks.length > 0">
              <label class="form-label">Copy meals from</label>
              <select class="form-select" v-model="copyFromWeekId">
                <option :value="null">— Start blank —</option>
                <option v-for="w in store.weeks" :key="w.id" :value="w.id">
                  {{ w.label }}{{ w.dates ? ` (${w.dates})` : '' }}
                </option>
              </select>
            </div>

            <div class="modal-actions">
              <button class="btn btn-secondary" @click="showAddWeek = false">Cancel</button>
              <button class="btn btn-primary" @click="handleAddWeek">
                {{ copyFromWeekId ? '📋 Copy & Add Week' : '＋ Add Week' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Edit Dates Modal (WeekCard → edit-dates) -->
      <Transition name="modal">
        <div v-if="editDatesWeek" class="modal-overlay" @click.self="editDatesWeek = null">
          <div class="modal-box" style="max-width: 420px;">
            <h2 class="modal-title">Set Date Range</h2>
            <p class="modal-sub">
              Link <strong>{{ editDatesWeek.label }}</strong> to a calendar date range so meals sync automatically.
            </p>

            <div class="form-group">
              <label class="form-label">Week Name</label>
              <input class="form-input" v-model="editDatesLabel" />
            </div>

            <div class="form-group">
              <label class="form-label">Date Range</label>
              <div class="date-range-row">
                <div class="date-range-field">
                  <label class="form-sublabel">From</label>
                  <input type="date" class="form-input" v-model="editDatesFrom" />
                </div>
                <div class="date-range-field">
                  <label class="form-sublabel">To</label>
                  <input type="date" class="form-input" v-model="editDatesTo" />
                </div>
              </div>
              <div v-if="editDatesFrom && editDatesTo && editSyncPreviewCount > 0" class="sync-preview-note">
                🔄 <strong>{{ editSyncPreviewCount }} calendar meal{{ editSyncPreviewCount !== 1 ? 's' : '' }}</strong>
                in this range will sync into this week.
              </div>
            </div>

            <div class="modal-actions">
              <button class="btn btn-secondary" @click="editDatesWeek = null">Cancel</button>
              <button
                class="btn btn-primary"
                @click="saveEditDates"
                :disabled="!editDatesFrom || !editDatesTo"
              >Save & Sync</button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Recipe Detail / Edit Modal -->
      <Transition name="modal">
        <div v-if="selectedRecipe" class="modal-overlay" @click.self="closeRecipeModal">
          <div class="modal-box">

            <!-- View / Edit toggle bar -->
            <div class="recipe-mode-bar">
              <button
                class="recipe-mode-btn"
                :class="{ active: recipeMode === 'view' }"
                @click="recipeMode = 'view'"
              >👁 View</button>
              <button
                class="recipe-mode-btn"
                :class="{ active: recipeMode === 'edit' }"
                @click="switchToEdit"
              >
                ✏️ Edit
                <span v-if="hasUnsavedChanges" class="unsaved-dot" title="Unsaved changes" />
              </button>
            </div>

            <!-- ── VIEW MODE ── -->
            <template v-if="recipeMode === 'view'">
              <div class="recipe-detail-emoji">{{ selectedRecipe.emoji }}</div>
              <h2 class="modal-title">{{ selectedRecipe.name }}</h2>
              <span
                v-if="selectedRecipe.category"
                class="recipe-cat-badge"
                :class="'badge-' + selectedRecipe.category"
              >
                {{ CAT_META[selectedRecipe.category]?.emoji }}
                {{ CAT_META[selectedRecipe.category]?.label }}
              </span>
              <p class="modal-sub">{{ selectedRecipe.ingredients.length }} ingredient{{ selectedRecipe.ingredients.length !== 1 ? 's' : '' }}</p>

              <ul class="recipe-ing-list">
                <li v-for="(ing, i) in selectedRecipe.ingredients" :key="i" class="recipe-ing-item">
                  <span class="ing-dot">·</span>
                  <span class="ing-label">{{ ing }}</span>
                  <StorePill
                    :model-value="store.recipeStores[selectedRecipe.id]?.[i] ?? null"
                    :stores="store.stores"
                    @update:model-value="id => store.setRecipeIngStore(selectedRecipe.id, i, id)"
                  />
                </li>
              </ul>

              <div class="modal-actions">
                <button class="btn btn-danger" @click="handleDeleteRecipe(selectedRecipe.id)">🗑 Delete</button>
                <button class="btn btn-secondary" @click="closeRecipeModal">Close</button>
                <button class="btn btn-primary" @click="openAddToModal(selectedRecipe)">＋ Add to Week / Calendar</button>
              </div>
            </template>

            <!-- ── EDIT MODE ── -->
            <template v-else>
              <div class="edit-notice">✏️ Changes will update this recipe in the library.</div>

              <!-- Emoji + Name -->
              <div class="name-row">
                <div class="form-group emoji-group">
                  <label class="form-label">Emoji</label>
                  <input class="form-input emoji-input" v-model="draft.emoji" maxlength="4" />
                </div>
                <div class="form-group name-group">
                  <label class="form-label">Recipe Name</label>
                  <input class="form-input" v-model="draft.name" placeholder="Recipe name" />
                </div>
              </div>

              <!-- Category -->
              <div class="form-group">
                <label class="form-label">Meal Category</label>
                <div class="cat-tag-row">
                  <button
                    v-for="cat in CATEGORIES"
                    :key="cat"
                    type="button"
                    class="cat-tag-btn"
                    :class="[CAT_META[cat].pillClass, { active: draft.category === cat }]"
                    @click="draft.category = draft.category === cat ? null : cat"
                  >
                    {{ CAT_META[cat].emoji }} {{ CAT_META[cat].label }}
                  </button>
                </div>
              </div>

              <!-- Ingredients editor -->
              <div class="form-group">
                <div class="ing-label-row">
                  <label class="form-label">Ingredients ({{ draft.ingredients.filter(i => i.trim()).length }})</label>
                  <span class="ing-hint">Enter to add · Backspace to remove empty</span>
                </div>
                <div class="ing-list-editor">
                  <div
                    v-for="(ing, i) in draft.ingredients"
                    :key="i"
                    class="ing-editor-row"
                  >
                    <span class="ing-num">{{ i + 1 }}</span>
                    <input
                      class="form-input ing-input"
                      :placeholder="`Ingredient ${i + 1}`"
                      v-model="draft.ingredients[i]"
                      :ref="el => { if (el) draftIngRefs[i] = el }"
                      @keydown.enter="addDraftIngAfter(i)"
                      @keydown.backspace="removeDraftIfEmpty(i, $event)"
                    />
                    <StorePill
                      :model-value="store.recipeStores[selectedRecipe.id]?.[i] ?? null"
                      :stores="store.stores"
                      @update:model-value="id => store.setRecipeIngStore(selectedRecipe.id, i, id)"
                    />
                    <button
                      class="btn-remove-ing"
                      @click="removeDraftIng(i)"
                      v-if="draft.ingredients.length > 1"
                    >✕</button>
                  </div>
                </div>
                <button class="btn-add-ing" @click="draft.ingredients.push('')">＋ Add ingredient</button>
              </div>

              <div class="modal-actions">
                <button
                  class="btn btn-primary"
                  @click="handleSaveEdit"
                  :disabled="!draft.name.trim()"
                  :class="{ 'btn-disabled': !draft.name.trim() }"
                >💾 Save Changes</button>
              </div>
            </template>

          </div>
        </div>
      </Transition>

      <!-- Delete Week Confirm -->
      <Transition name="modal">
        <div v-if="weekToDelete" class="modal-overlay" @click.self="weekToDelete = null">
          <div class="modal-box" style="max-width: 380px;">
            <h2 class="modal-title" style="color: #c0392b;">Delete Week?</h2>
            <p class="modal-sub" style="margin-bottom: 24px;">
              This will permanently remove <strong>{{ weekToDelete.label }}</strong> and all its meal data.
            </p>
            <div class="modal-actions">
              <button class="btn btn-secondary" @click="weekToDelete = null">Cancel</button>
              <button class="btn btn-danger" @click="handleDeleteWeek">Delete</button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Unified Add-To Modal -->
      <UnifiedAddToModal
        v-if="showAddToModal && addToRecipe"
        :recipe="addToRecipe"
        @close="showAddToModal = false"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from 'vue'
import { useMealStore, CAT_META, CATEGORIES } from '../stores/mealStore.js'
import WeekCard from './WeekCard.vue'
import StorePill from './StorePill.vue'
import CalendarView from './CalendarView.vue'
import UnifiedAddToModal from './UnifiedAddToModal.vue'

const store = useMealStore()
const emit  = defineEmits(['open-week', 'add-recipe'])

// ── Library category accordion ──
const openLibCats = ref(['breakfast']) // first panel open by default

const libCats = computed(() => [
  ...CATEGORIES.map(key => ({
    key,
    emoji: CAT_META[key].emoji,
    label: CAT_META[key].label,
    recipes: store.recipesByCategory[key] || [],
  })),
  {
    key: 'uncategorised',
    emoji: '🗂️',
    label: 'Uncategorised',
    recipes: store.recipesByCategory.uncategorised || [],
  },
].filter(c => c.key === 'uncategorised' ? c.recipes.length > 0 : true))

function toggleLibCat(key) {
  const idx = openLibCats.value.indexOf(key)
  if (idx >= 0) openLibCats.value.splice(idx, 1)
  else openLibCats.value.push(key)
}

const showAddWeek    = ref(false)
const newWeekLabel   = ref('')
const newWeekDates   = ref('')
const newWeekFrom    = ref('')   // ISO date string for dateFrom picker
const newWeekTo      = ref('')   // ISO date string for dateTo picker
const copyFromWeekId = ref(null)
const weekLabelInput = ref(null)
const selectedRecipe = ref(null)
const weekToDelete   = ref(null)

// Calendar tab
const activeTab      = ref('weeks')  // 'weeks' | 'calendar'

// Edit dates modal (for WeekCard edit-dates action)
const editDatesWeek  = ref(null)
const editDatesFrom  = ref('')
const editDatesTo    = ref('')
const editDatesLabel = ref('')

// Unified Add-To modal (recipe library → week/calendar)
const showAddToModal = ref(false)
const addToRecipe    = ref(null)

// ── Recipe view/edit modal ──
const recipeMode  = ref('view')  // 'view' | 'edit'
const draftIngRefs = ref([])
const draft = reactive({ name: '', emoji: '', category: null, ingredients: [] })

const hasUnsavedChanges = computed(() => {
  if (!selectedRecipe.value || recipeMode.value !== 'edit') return false
  return (
    draft.name !== selectedRecipe.value.name ||
    draft.emoji !== selectedRecipe.value.emoji ||
    draft.category !== (selectedRecipe.value.category || null) ||
    JSON.stringify(draft.ingredients) !== JSON.stringify(selectedRecipe.value.ingredients)
  )
})

function openRecipeModal(recipe) {
  selectedRecipe.value = recipe
  recipeMode.value = 'view'
}

function closeRecipeModal() {
  selectedRecipe.value = null
  recipeMode.value = 'view'
}

function switchToEdit() {
  draft.name = selectedRecipe.value.name
  draft.emoji = selectedRecipe.value.emoji
  draft.category = selectedRecipe.value.category || null
  draft.ingredients = [...selectedRecipe.value.ingredients]
  recipeMode.value = 'edit'
}

function addDraftIngAfter(index) {
  draft.ingredients.splice(index + 1, 0, '')
  nextTick(() => draftIngRefs.value[index + 1]?.focus())
}

function removeDraftIfEmpty(index, e) {
  if (draft.ingredients[index] === '' && draft.ingredients.length > 1) {
    e.preventDefault()
    draft.ingredients.splice(index, 1)
    nextTick(() => draftIngRefs.value[Math.max(0, index - 1)]?.focus())
  }
}

function removeDraftIng(index) {
  if (draft.ingredients.length <= 1) return
  draft.ingredients.splice(index, 1)
}

function handleSaveEdit() {
  if (!draft.name.trim()) return
  const updated = {
    ...selectedRecipe.value,
    name: draft.name.trim(),
    emoji: draft.emoji || '🍽️',
    category: draft.category,
    ingredients: draft.ingredients.filter(i => i.trim()),
  }
  store.updateRecipe(updated.id, updated)
  selectedRecipe.value = { ...updated }
  recipeMode.value = 'view'
}

function handleAddWeek() {
  const label    = newWeekLabel.value.trim() || `Week ${store.weeks.length + 1}`
  const dateFrom = newWeekFrom.value  || null
  const dateTo   = newWeekTo.value    || null
  let newWeek
  if (copyFromWeekId.value) {
    newWeek = store.copyWeek(copyFromWeekId.value)
    if (newWeek) {
      newWeek.label = label
      store.updateWeekLabel(newWeek.id, label, newWeekDates.value.trim(), dateFrom, dateTo)
    }
  } else {
    newWeek = store.addWeek(label, dateFrom, dateTo)
    if (newWeek && newWeekDates.value.trim() && !newWeek.dates) {
      store.updateWeekLabel(newWeek.id, label, newWeekDates.value.trim())
    }
  }
  newWeekLabel.value   = ''
  newWeekDates.value   = ''
  newWeekFrom.value    = ''
  newWeekTo.value      = ''
  copyFromWeekId.value = null
  showAddWeek.value    = false
}

function confirmDeleteWeek(week) {
  weekToDelete.value = week
}

function handleDeleteWeek() {
  if (!weekToDelete.value) return
  store.deleteWeek(weekToDelete.value.id)
  weekToDelete.value = null
}

function handleDeleteRecipe(id) {
  store.deleteRecipe(id)
  selectedRecipe.value = null
}

// ── Sync preview: count calendar meals in a candidate date range ──
function _countMealsInRange(fromStr, toStr) {
  if (!fromStr || !toStr) return 0
  const f = new Date(fromStr); f.setHours(0,0,0,0)
  const t = new Date(toStr);   t.setHours(0,0,0,0)
  if (f > t) return 0
  let count = 0
  const d = new Date(f)
  while (d <= t) {
    const key = store._dk(d)
    const day  = store.calendarMeals[key]
    if (day) count += Object.values(day).flat().length
    d.setDate(d.getDate() + 1)
  }
  return count
}

const syncPreviewCount = computed(() => _countMealsInRange(newWeekFrom.value, newWeekTo.value))
const editSyncPreviewCount = computed(() => _countMealsInRange(editDatesFrom.value, editDatesTo.value))
function openEditDates(week) {
  editDatesWeek.value  = week
  editDatesLabel.value = week.label
  editDatesFrom.value  = week.dateFrom ? store._dk(new Date(week.dateFrom)) : ''
  editDatesTo.value    = week.dateTo   ? store._dk(new Date(week.dateTo))   : ''
}

function saveEditDates() {
  const week = editDatesWeek.value
  if (!week) return
  store.updateWeekLabel(
    week.id,
    editDatesLabel.value.trim() || week.label,
    undefined,                   // keep existing dates string; store derives it
    editDatesFrom.value || null,
    editDatesTo.value   || null,
  )
  editDatesWeek.value = null
}

// ── Unified Add-To modal (recipe library → week / calendar day) ──
function openAddToModal(recipe) {
  addToRecipe.value    = recipe
  showAddToModal.value = true
}
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 80px;
}

/* ── Hero ── */
.hero {
  padding: 52px 40px 32px;
  text-align: center;
}

.hero-eyebrow {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--brown-lt);
  margin-bottom: 12px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(32px, 5vw, 46px);
  font-weight: 700;
  color: var(--charcoal);
  line-height: 1.12;
  margin-bottom: 14px;
}

.hero-title em {
  font-style: italic;
  color: var(--terracotta);
}

.hero-sub {
  font-size: 15px;
  color: var(--brown-mid);
  max-width: 440px;
  margin: 0 auto;
  line-height: 1.65;
}

/* ── Section ── */
.section {
  padding: 8px 40px 40px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--brown-lt);
}

/* ── Weeks Grid ── */
.weeks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
}

/* ── Add Week Button ── */
.btn-add-week {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 170px;
  background: transparent;
  border: 2px dashed var(--parchment);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.22s var(--ease);
  color: var(--brown-lt);
  font-family: var(--font-body);
}

.btn-add-week:hover {
  border-color: var(--terracotta);
  color: var(--terracotta);
  background: rgba(193,68,14,0.03);
  transform: translateY(-2px);
}

.add-week-icon { font-size: 22px; font-weight: 300; }
.add-week-label { font-size: 13px; font-weight: 600; }

/* ── Recipe Grid ── */
.recipes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
  gap: 14px;
}

.recipe-card {
  background: var(--warm-white);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg);
  padding: 20px 18px;
  cursor: pointer;
  transition: all 0.22s var(--ease);
  animation: fadeIn 0.3s var(--ease) both;
}

.recipe-card:hover {
  border-color: var(--sage);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px var(--shadow-md);
}

.recipe-emoji { font-size: 30px; margin-bottom: 10px; }
.recipe-name {
  font-family: var(--font-display);
  font-size: 15px; font-weight: 600;
  color: var(--charcoal);
  margin-bottom: 5px;
  line-height: 1.3;
}
.recipe-ing-count { font-size: 12px; color: var(--brown-lt); }

/* ── Recipe Detail Modal ── */
.recipe-detail-emoji { font-size: 44px; margin-bottom: 12px; }
.modal-title {
  font-family: var(--font-display);
  font-size: 24px; font-weight: 700;
  color: var(--charcoal); margin-bottom: 4px;
}
.modal-sub { font-size: 13px; color: var(--brown-lt); margin-bottom: 20px; }
.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
  justify-content: flex-end;
  flex-wrap: wrap;
}
/* Keep destructive action on the left, other buttons cluster right */
.modal-actions .btn-danger { margin-right: auto; }

.recipe-ing-list { list-style: none; margin-top: 4px; }
.recipe-ing-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(237,224,204,0.6);
  font-size: 14px;
}
.recipe-ing-item:last-child { border-bottom: none; }
.ing-dot { color: var(--terracotta); font-size: 18px; line-height: 1; flex-shrink: 0; }
.ing-label { flex: 1; font-size: 14px; }

/* ── Modal transitions ── */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-box,
.modal-leave-active .modal-box {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box { transform: scale(0.96) translateY(10px); }
.modal-leave-to   .modal-box { transform: scale(0.96) translateY(10px); opacity: 0; }

@media (max-width: 640px) {
  .hero { padding: 36px 20px 24px; }
  .section { padding: 8px 20px 32px; }
  .divider { margin: 0 20px; }
}

/* ── Library Category Accordion ── */
.lib-categories {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lib-cat-panel {
  background: var(--warm-white);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s;
}

.lib-cat-panel:hover { border-color: var(--parchment-dark); }

/* Header gradient variants */
.lib-breakfast .lib-cat-header { background: linear-gradient(90deg, #fff8f0, var(--warm-white)); }
.lib-lunch     .lib-cat-header { background: linear-gradient(90deg, #f0fff3, var(--warm-white)); }
.lib-dinner    .lib-cat-header { background: linear-gradient(90deg, #f0f2ff, var(--warm-white)); }
.lib-snacks    .lib-cat-header { background: linear-gradient(90deg, #fff0f5, var(--warm-white)); }
.lib-uncategorised .lib-cat-header { background: linear-gradient(90deg, #f5f0e8, var(--warm-white)); }

.lib-cat-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border: none;
  cursor: pointer;
  font-family: var(--font-body);
  transition: background 0.15s;
}
.lib-cat-header:hover { filter: brightness(0.97); }

.lib-cat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lib-cat-emoji { font-size: 18px; }

.lib-cat-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--charcoal);
}

.lib-cat-badge {
  background: var(--parchment);
  color: var(--brown-mid);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 22px;
  text-align: center;
}

.lib-chevron {
  font-size: 18px;
  color: var(--brown-lt);
  display: inline-block;
  transition: transform 0.22s var(--ease);
}
.lib-chevron.open { transform: rotate(90deg); }

/* ── Food row inside library ── */
.lib-food-list {
  border-top: 1px solid var(--parchment);
}

.lib-food-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 18px;
  cursor: pointer;
  transition: background 0.14s;
  border-bottom: 1px solid rgba(237,224,204,0.45);
}
.lib-food-row:last-child { border-bottom: none; }
.lib-food-row:hover { background: rgba(237,224,204,0.3); }

.lib-food-emoji { font-size: 20px; flex-shrink: 0; }

.lib-food-info { flex: 1; min-width: 0; }

.lib-food-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--charcoal);
}

.lib-food-ings {
  font-size: 12px;
  color: var(--brown-lt);
}

.lib-food-arrow {
  font-size: 16px;
  color: var(--parchment-dark);
  transition: transform 0.15s;
}
.lib-food-row:hover .lib-food-arrow { transform: translateX(3px); color: var(--terracotta); }

.lib-empty {
  padding: 14px 18px;
  font-size: 13px;
  color: var(--brown-lt);
  font-style: italic;
  border-top: 1px solid var(--parchment);
}

/* ── Recipe modal mode bar ── */
.recipe-mode-bar {
  display: flex;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: 10px;
  padding: 3px;
  gap: 3px;
  margin-bottom: 22px;
}
.recipe-mode-btn {
  flex: 1; padding: 7px 12px;
  border: none; border-radius: 7px;
  font-family: var(--font-body); font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.18s;
  background: transparent; color: var(--brown-lt);
  display: flex; align-items: center; justify-content: center; gap: 5px;
}
.recipe-mode-btn.active {
  background: var(--warm-white);
  color: var(--charcoal); font-weight: 600;
  box-shadow: 0 1px 4px var(--shadow);
}
.recipe-mode-btn:hover:not(.active) { color: var(--brown-mid); }

.unsaved-dot {
  display: inline-block; width: 7px; height: 7px;
  background: var(--terracotta); border-radius: 50%;
  flex-shrink: 0;
}

/* Category badge in view mode */
.recipe-cat-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
  margin: 4px 0 8px;
}
.badge-breakfast { background: #fff3e0; color: #e65100; }
.badge-lunch     { background: #e8f5e9; color: #2e7d32; }
.badge-dinner    { background: #e8eaf6; color: #283593; }
.badge-snacks    { background: #fce4ec; color: #880e4f; }

/* Edit mode notice */
.edit-notice {
  background: var(--terracotta-bg, #fff0ea);
  border: 1px solid rgba(193,68,14,0.2);
  border-radius: 8px; padding: 8px 12px;
  font-size: 12px; color: var(--terracotta);
  margin-bottom: 18px;
}

/* Name row (reuse from AddRecipeModal style) */
.name-row { display: flex; gap: 12px; }
.emoji-group { width: 90px; flex-shrink: 0; }
.emoji-input { text-align: center; font-size: 20px; padding: 8px; }
.name-group  { flex: 1; }

/* Category tag row */
.cat-tag-row { display: flex; flex-wrap: wrap; gap: 8px; }
.cat-tag-btn {
  padding: 6px 14px; border-radius: 20px; border: 2px solid transparent;
  font-family: var(--font-body); font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.18s var(--ease); opacity: 0.6;
}
.cat-tag-btn:hover { opacity: 0.85; transform: translateY(-1px); }
.cat-tag-btn.active {
  opacity: 1; border-color: currentColor; font-weight: 700;
  transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

/* Ingredient editor */
.ing-label-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ing-hint { font-size: 11px; color: var(--brown-lt); font-style: italic; }
.ing-list-editor { margin-bottom: 8px; }
.ing-editor-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
.ing-num { width: 20px; font-size: 12px; color: var(--brown-lt); text-align: right; flex-shrink: 0; }
.ing-input { flex: 1; padding: 8px 12px; font-size: 13px; }
.btn-remove-ing {
  background: none; border: none; font-size: 13px; color: var(--parchment-dark);
  cursor: pointer; width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4px; transition: all 0.15s; flex-shrink: 0;
}
.btn-remove-ing:hover { background: #fee; color: #c0392b; }
.btn-add-ing {
  width: 100%; background: transparent; border: 1.5px dashed var(--parchment);
  border-radius: var(--radius-md); padding: 8px;
  font-family: var(--font-body); font-size: 13px; color: var(--brown-lt);
  cursor: pointer; transition: all 0.18s;
}
.btn-add-ing:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-bg); }
.btn-disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Section tab group (Weeks / Calendar toggle) ── */
.section-tab-group {
  display: flex;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 3px;
}

.section-tab {
  padding: 6px 16px;
  border-radius: 9px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  background: transparent;
  color: var(--brown-lt);
  font-family: var(--font-body);
  transition: all 0.18s var(--ease);
}
.section-tab:hover:not(.active) { background: var(--parchment); color: var(--brown-mid); }
.section-tab.active {
  background: var(--warm-white);
  color: var(--terracotta);
  box-shadow: 0 1px 4px var(--shadow);
}

/* ── Date range row inside modals ── */
.date-range-row {
  display: flex;
  gap: 12px;
}
.date-range-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.form-sublabel {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brown-lt);
}
.form-label-hint {
  font-weight: 400;
  font-size: 11px;
  color: var(--brown-lt);
  text-transform: none;
  letter-spacing: 0;
}

/* ── Sync preview note ── */
.sync-preview-note {
  margin-top: 10px;
  padding: 9px 13px;
  border-radius: var(--radius-md);
  font-size: 13px;
  background: var(--sage-bg, #edf5ee);
  border: 1.5px solid var(--sage-lt, #8ab890);
  color: var(--sage, #5e8c65);
}
.sync-preview-note.sync-preview-none {
  background: var(--cream);
  border-color: var(--parchment);
  color: var(--brown-lt);
  font-style: italic;
}
.lib-expand-enter-active, .lib-expand-leave-active {
  transition: all 0.25s var(--ease);
  overflow: hidden;
}
.lib-expand-enter-from, .lib-expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.lib-expand-enter-to, .lib-expand-leave-from {
  opacity: 1;
  max-height: 600px;
}
</style>
