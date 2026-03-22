<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box picker-box">
      <div class="modal-head">
        <div>
          <div class="modal-title">Add to {{ meta.label }}</div>
          <div class="modal-sub">{{ weekLabel }} · pick from your recipe library</div>
        </div>
        <button class="close-btn" @click="$emit('close')" aria-label="Close">✕</button>
      </div>

      <!-- Tab: Library vs Custom (same as calendar flow when Library) -->
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: mode === 'library' }"
          @click="mode = 'library'"
        >
          📖 From Library
        </button>
        <button
          class="tab"
          :class="{ active: mode === 'custom' }"
          @click="mode = 'custom'"
        >
          ✏️ Custom Item
        </button>
      </div>

      <!-- Library Mode — matches calendar picker UI -->
      <template v-if="mode === 'library'">
        <div class="picker-search-wrap">
          <input
            ref="searchInput"
            class="picker-search"
            v-model="searchQuery"
            placeholder="Search recipes…"
          />
        </div>
        <div class="picker-filters">
          <button
            v-for="f in pickerFilters"
            :key="f.key"
            class="pk-filter"
            :class="{ active: pickerFilter === f.key }"
            @click="pickerFilter = f.key"
          >{{ f.label }}</button>
        </div>
        <div class="picker-list">
          <div v-if="!filteredRecipes.length" class="picker-empty">No recipes found</div>
          <div
            v-for="r in filteredRecipes"
            :key="r.id"
            class="recipe-pick-row"
            :class="{ 'is-picked': selectedIds.has(r.id) }"
            @click="toggleRecipe(r.id)"
          >
            <span class="rpr-emoji">{{ r.emoji }}</span>
            <div class="rpr-info">
              <div class="rpr-name">{{ r.name }}</div>
              <div class="rpr-ings">{{ (r.ingredients || []).slice(0, 3).join(', ') }}</div>
            </div>
            <div class="rpr-check">{{ selectedIds.has(r.id) ? '✓' : '' }}</div>
          </div>
        </div>
        <p class="library-hint" v-if="store.recipes.length === 0">
          Your library is empty. Use "Add Recipe" to build it first, or switch to Custom Item below.
        </p>
      </template>

      <!-- Custom Mode -->
      <div v-else class="custom-body">
        <div class="name-row">
          <div class="form-group emoji-group">
            <label class="form-label">Emoji</label>
            <input class="form-input emoji-input" v-model="customEmoji" maxlength="4" placeholder="🍽️" />
          </div>
          <div class="form-group name-group">
            <label class="form-label">Item Name *</label>
            <input
              class="form-input"
              v-model="customName"
              placeholder="e.g. Overnight Oats"
              ref="customInput"
            />
          </div>
        </div>

        <div class="form-group">
          <div class="ing-label-row">
            <label class="form-label">Ingredients (optional)</label>
            <span class="ing-hint">For the shopping list</span>
          </div>
          <div class="ing-editor">
            <div v-for="(ing, i) in customIngredients" :key="i" class="ing-editor-row">
              <span class="ing-num">{{ i + 1 }}</span>
              <input
                class="form-input ing-input"
                :placeholder="`Ingredient ${i + 1}`"
                v-model="customIngredients[i]"
                @keydown.enter="customIngredients.push('')"
              />
              <button
                class="btn-remove-ing"
                @click="customIngredients.splice(i, 1)"
                v-if="customIngredients.length > 1"
              >✕</button>
            </div>
          </div>
          <button class="btn-add-ing" @click="customIngredients.push('')">＋ Add ingredient</button>
        </div>
      </div>

      <!-- Footer — matches calendar picker -->
      <div class="modal-foot">
        <span class="picker-sel-info" v-if="mode === 'library'">
          <template v-if="selectedIds.size > 0">
            <strong class="adding">{{ selectedIds.size }}</strong> recipe{{ selectedIds.size !== 1 ? 's' : '' }} to add
          </template>
          <template v-else>No recipe selected</template>
        </span>
        <span v-else class="picker-sel-info"></span>
        <div class="modal-foot-actions">
          <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
          <button
            class="btn btn-primary"
            @click="handleAdd"
            :disabled="!canAdd"
            :class="{ 'btn-disabled': !canAdd }"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useMealStore, CAT_META, CATEGORIES } from '../stores/mealStore.js'

const props = defineProps({
  weekId:   { type: Number, required: true },
  category: { type: String, required: true },
})

const emit = defineEmits(['close'])
const store = useMealStore()

const meta = computed(() => CAT_META[props.category])
const mode = ref(store.recipes.length > 0 ? 'library' : 'custom')

// Week label for subtitle (same pattern as calendar date)
const weekLabel = computed(() => {
  const w = store.weeks.find(x => x.id === props.weekId)
  return w?.label ?? 'Week'
})

// Library mode — same as calendar: search + meal-type filter + multi-select
const searchQuery = ref('')
const pickerFilter = ref('all')
const selectedIds = ref(new Set())
const searchInput = ref(null)

const pickerFilters = computed(() => [
  { key: 'all', label: 'All' },
  ...CATEGORIES.map(k => ({ key: k, label: `${CAT_META[k].emoji} ${CAT_META[k].label}` })),
])

// When modal opens for a category, default filter to that category (like calendar)
watch(() => [props.weekId, props.category], () => {
  pickerFilter.value = props.category
}, { immediate: true })

function toggleRecipe(id) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

// Custom mode
const customEmoji       = ref('🍽️')
const customName        = ref('')
const customIngredients = ref([''])
const customInput       = ref(null)

const filteredRecipes = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return store.recipes.filter(r =>
    (pickerFilter.value === 'all' || r.category === pickerFilter.value) &&
    (!q || (r.name || '').toLowerCase().includes(q))
  )
})

const canAdd = computed(() => {
  if (mode.value === 'library') return selectedIds.value.size > 0
  return !!customName.value.trim()
})

onMounted(() => {
  nextTick(() => {
    if (mode.value === 'library') searchInput.value?.focus()
    else customInput.value?.focus()
  })
})

function handleAdd() {
  if (!canAdd.value) return

  if (mode.value === 'library') {
    selectedIds.value.forEach(id => {
      const recipe = store.getRecipeById(id)
      if (!recipe) return
      // Dedup: skip if already in this week/category
      const week = store.weeks.find(w => w.id === props.weekId)
      if (week?.categories[props.category]?.find(f => f.recipeId === id)) return
      store.addFoodToWeek(props.weekId, props.category, {
        name: recipe.name,
        emoji: recipe.emoji,
        recipeId: recipe.id,
        customIngredients: [],
      })
    })
  } else {
    store.addFoodToWeek(props.weekId, props.category, {
      name: customName.value.trim(),
      emoji: customEmoji.value || '🍽️',
      recipeId: null,
      customIngredients: customIngredients.value.filter(i => i.trim()),
    })
  }
  emit('close')
}
</script>

<style scoped>
/* ── Picker layout (match calendar) ── */
.picker-box {
  max-width: 500px;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 22px 12px;
  border-bottom: 1.5px solid var(--parchment);
  flex-shrink: 0;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--charcoal);
}
.modal-sub {
  font-size: 12.5px;
  color: var(--brown-lt);
  margin-top: 3px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 15px;
  cursor: pointer;
  color: var(--brown-lt);
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.close-btn:hover { background: var(--parchment); color: var(--charcoal); }

/* ── Tabs ── */
.tabs {
  display: flex;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md);
  padding: 3px;
  margin: 12px 18px 0;
  gap: 3px;
  flex-shrink: 0;
}

.tab {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: calc(var(--radius-md) - 3px);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: var(--brown-lt);
}

.tab.active {
  background: var(--warm-white);
  color: var(--charcoal);
  font-weight: 600;
  box-shadow: 0 1px 4px var(--shadow-sm);
}

/* ── Search (match calendar) ── */
.picker-search-wrap {
  padding: 10px 18px;
  border-bottom: 1px solid var(--parchment);
  flex-shrink: 0;
}
.picker-search {
  width: 100%;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-family: var(--font-body);
  font-size: 13.5px;
  color: var(--charcoal);
  outline: none;
}
.picker-search:focus {
  border-color: var(--terracotta);
  box-shadow: 0 0 0 3px rgba(193, 68, 14, 0.1);
}

/* ── Meal type filters (match calendar) ── */
.picker-filters {
  display: flex;
  gap: 5px;
  padding: 8px 18px;
  border-bottom: 1px solid var(--parchment);
  overflow-x: auto;
  flex-shrink: 0;
}
.pk-filter {
  padding: 4px 12px;
  border-radius: 20px;
  border: 1.5px solid var(--parchment);
  background: transparent;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: var(--font-body);
  color: var(--brown-lt);
  transition: all 0.14s;
}
.pk-filter.active {
  border-color: var(--terracotta);
  background: var(--terracotta-bg);
  color: var(--terracotta);
}
.pk-filter:hover:not(.active) { background: var(--cream); }

/* ── Recipe list (match calendar) ── */
.picker-list {
  overflow-y: auto;
  flex: 1;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 200px;
  max-height: 350px;
}
.picker-empty {
  padding: 28px;
  text-align: center;
  color: var(--brown-lt);
  font-style: italic;
  font-size: 13px;
}
.recipe-pick-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 11px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.13s;
  border: 1.5px solid transparent;
}
.recipe-pick-row:hover {
  background: var(--terracotta-bg);
  border-color: rgba(193, 68, 14, 0.18);
}
.recipe-pick-row.is-picked {
  background: var(--terracotta-bg);
  border-color: var(--terracotta);
}
.rpr-emoji { font-size: 22px; flex-shrink: 0; }
.rpr-info { flex: 1; min-width: 0; }
.rpr-name { font-size: 13.5px; font-weight: 600; color: var(--charcoal); }
.rpr-ings { font-size: 11.5px; color: var(--brown-lt); }
.rpr-check {
  width: 21px;
  height: 21px;
  border-radius: 50%;
  border: 2px solid var(--parchment);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
  transition: all 0.14s;
}
.recipe-pick-row.is-picked .rpr-check {
  background: var(--terracotta);
  border-color: var(--terracotta);
  color: #fff;
}

/* ── Footer (match calendar) ── */
.modal-foot {
  padding: 12px 18px;
  border-top: 1.5px solid var(--parchment);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: var(--cream);
}
.picker-sel-info {
  font-size: 12px;
  color: var(--brown-lt);
}
.picker-sel-info .adding {
  color: var(--sage, #5e8c65);
}
.modal-foot-actions {
  display: flex;
  gap: 8px;
}

.library-hint {
  font-size: 12px;
  color: var(--brown-lt);
  font-style: italic;
  margin: 8px 18px 12px;
  padding: 10px;
  background: var(--parchment);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.custom-body { flex-shrink: 0; padding: 0 18px 12px; }

/* ── Custom ── */
.name-row { display: flex; gap: 12px; }
.emoji-group { width: 90px; flex-shrink: 0; }
.emoji-input { text-align: center; font-size: 20px; padding: 8px; }
.name-group { flex: 1; }

.ing-label-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ing-hint { font-size: 11px; color: var(--brown-lt); font-style: italic; }
.form-label { margin-bottom: 0; }

.ing-editor { margin-bottom: 8px; }
.ing-editor-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
.ing-num { width: 20px; font-size: 12px; color: var(--brown-lt); text-align: right; flex-shrink: 0; }
.ing-input { flex: 1; padding: 8px 12px; font-size: 13px; }
.btn-remove-ing {
  background: none; border: none; font-size: 13px;
  color: var(--parchment-dark); cursor: pointer;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4px; transition: all 0.15s; flex-shrink: 0;
}
.btn-remove-ing:hover { background: #fee; color: #c0392b; }

.btn-add-ing {
  width: 100%; background: transparent;
  border: 1.5px dashed var(--parchment); border-radius: var(--radius-md);
  padding: 8px; font-family: var(--font-body); font-size: 13px;
  color: var(--brown-lt); cursor: pointer; transition: all 0.18s;
}
.btn-add-ing:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-bg); }

.recipe-option.already-added {
  border-color: var(--sage-lt, #8ab890);
  background: var(--sage-bg, #edf5ee);
  opacity: 0.75;
}

.ro-badge {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--sage, #5e8c65);
  background: rgba(94,140,101,0.12);
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── Actions ── */
.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
  justify-content: flex-end;
  align-items: center;
}

.sel-count {
  font-size: 12px;
  color: var(--terracotta);
  font-weight: 600;
  margin-right: auto;
}
.btn-disabled { opacity: 0.5; cursor: not-allowed; }

.empty-state { padding: 24px; gap: 6px; }
</style>
