<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="modal-head">
        <div>
          <h2 class="modal-title">Add Recipe</h2>
          <p class="modal-sub">Save a dish and its ingredients to your library</p>
        </div>
        <button class="close-btn" @click="$emit('close')" aria-label="Close">✕</button>
      </div>

      <!-- Emoji + Name row -->
      <div class="name-row">
        <div class="form-group emoji-group">
          <label class="form-label">Emoji</label>
          <input
            class="form-input emoji-input"
            v-model="form.emoji"
            maxlength="4"
            placeholder="🍽️"
          />
        </div>
        <div class="form-group name-group">
          <label class="form-label">Recipe Name *</label>
          <input
            class="form-input"
            v-model="form.name"
            placeholder="e.g. Pasta Carbonara"
            ref="nameInput"
            @keydown.enter="focusFirstIng"
          />
        </div>
      </div>

      <!-- Category Tag -->
      <div class="form-group">
        <label class="form-label">Meal Category</label>
        <div class="cat-tag-row">
          <button
            v-for="cat in categories"
            :key="cat"
            type="button"
            class="cat-tag-btn"
            :class="[CAT_META[cat].pillClass, { active: form.category === cat }]"
            @click="form.category = form.category === cat ? null : cat"
          >
            {{ CAT_META[cat].emoji }} {{ CAT_META[cat].label }}
          </button>
        </div>
      </div>

      <!-- Ingredients -->
      <div class="form-group">
        <div class="ing-label-row">
          <label class="form-label">Ingredients</label>
          <span class="ing-hint">Press Enter to add more</span>
        </div>

        <div class="ing-list-editor">
          <TransitionGroup name="ing-row">
            <div
              v-for="(ing, i) in form.ingredients"
              :key="i"
              class="ing-editor-row"
            >
              <span class="ing-num">{{ i + 1 }}</span>
              <input
                class="form-input ing-input"
                :placeholder="`Ingredient ${i + 1}`"
                v-model="form.ingredients[i]"
                :ref="el => { if (el) ingRefs[i] = el }"
                @keydown.enter="addIngredientAfter(i)"
                @keydown.backspace="removeIfEmpty(i, $event)"
              />
              <button
                class="btn-remove-ing"
                @click="removeIngredient(i)"
                v-if="form.ingredients.length > 1"
                aria-label="Remove ingredient"
              >✕</button>
            </div>
          </TransitionGroup>
        </div>

        <button class="btn-add-ing" @click="addIngredient">
          ＋ Add ingredient
        </button>
      </div>

      <!-- Actions -->
      <div class="modal-actions">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button
          class="btn btn-primary"
          @click="handleSave"
          :disabled="!form.name.trim()"
          :class="{ 'btn-disabled': !form.name.trim() }"
        >
          💾 Save Recipe
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useMealStore, CAT_META, CATEGORIES as categories } from '../stores/mealStore.js'

const emit = defineEmits(['close'])
const store = useMealStore()

const nameInput = ref(null)
const ingRefs   = ref([])

const form = reactive({
  emoji: '🍽️',
  name: '',
  category: null,
  ingredients: ['', ''],
})

onMounted(() => {
  nextTick(() => nameInput.value?.focus())
})

function focusFirstIng() {
  nextTick(() => ingRefs.value[0]?.focus())
}

function addIngredient() {
  form.ingredients.push('')
  nextTick(() => ingRefs.value[form.ingredients.length - 1]?.focus())
}

function addIngredientAfter(index) {
  form.ingredients.splice(index + 1, 0, '')
  nextTick(() => ingRefs.value[index + 1]?.focus())
}

function removeIngredient(index) {
  if (form.ingredients.length <= 1) return
  form.ingredients.splice(index, 1)
}

function removeIfEmpty(index, e) {
  if (form.ingredients[index] === '' && form.ingredients.length > 1) {
    e.preventDefault()
    removeIngredient(index)
    nextTick(() => ingRefs.value[Math.max(0, index - 1)]?.focus())
  }
}

function handleSave() {
  if (!form.name.trim()) return
  store.addRecipe({
    name: form.name,
    emoji: form.emoji || '🍽️',
    category: form.category,
    ingredients: form.ingredients.filter(i => i.trim()),
  })
  emit('close')
}
</script>

<style scoped>
/* ── Modal Head ── */
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 24px; font-weight: 700;
  color: var(--charcoal);
  margin-bottom: 3px;
}
.modal-sub { font-size: 13px; color: var(--brown-lt); }

.close-btn {
  background: none; border: none;
  font-size: 15px; cursor: pointer;
  color: var(--brown-lt);
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.close-btn:hover { background: var(--parchment); color: var(--charcoal); }

/* ── Name Row ── */
.name-row {
  display: flex;
  gap: 12px;
}

.emoji-group { width: 90px; flex-shrink: 0; }
.emoji-input { text-align: center; font-size: 20px; padding: 8px; }
.name-group  { flex: 1; }

/* ── Ingredient Editor ── */
.ing-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.form-label { margin-bottom: 0; }
.ing-hint { font-size: 11px; color: var(--brown-lt); font-style: italic; }

.ing-list-editor { margin-bottom: 8px; }

.ing-editor-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
}

.ing-num {
  width: 20px;
  font-size: 12px;
  color: var(--brown-lt);
  text-align: right;
  flex-shrink: 0;
}

.ing-input { flex: 1; padding: 8px 12px; font-size: 13px; }

.btn-remove-ing {
  background: none; border: none;
  font-size: 13px;
  color: var(--parchment-dark);
  cursor: pointer;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.btn-remove-ing:hover { background: #fee; color: #c0392b; }

.btn-add-ing {
  width: 100%;
  background: transparent;
  border: 1.5px dashed var(--parchment);
  border-radius: var(--radius-md);
  padding: 8px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--brown-lt);
  cursor: pointer;
  transition: all 0.18s;
}
.btn-add-ing:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-bg); }

/* ── Actions ── */
.modal-actions { display: flex; gap: 10px; margin-top: 24px; justify-content: flex-end; }

.btn-disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Ingredient row transitions ── */
.ing-row-enter-active, .ing-row-leave-active {
  transition: all 0.2s var(--ease);
}
.ing-row-enter-from { opacity: 0; transform: translateX(-10px); }
.ing-row-leave-to   { opacity: 0; transform: translateX(-10px); }

/* ── Category tag row ── */
.cat-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cat-tag-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 2px solid transparent;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s var(--ease);
  opacity: 0.6;
}

.cat-tag-btn:hover { opacity: 0.85; transform: translateY(-1px); }

.cat-tag-btn.active {
  opacity: 1;
  border-color: currentColor;
  font-weight: 700;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
</style>
