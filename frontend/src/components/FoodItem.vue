<template>
  <div class="food-item-wrapper">

    <!-- Food Row -->
    <div class="food-row" @click="toggleExpanded" role="button" :aria-expanded="expanded">
      <!-- Ingredient progress checkbox -->
      <div
        class="food-check"
        :class="{ 'all-checked': checkedCount > 0 && checkedCount === ingredients.length, 'some-checked': checkedCount > 0 && checkedCount < ingredients.length }"
        @click.stop="toggleAllIngredients"
        :title="checkedCount > 0 ? 'Uncheck all ingredients' : 'Check all ingredients'"
        role="checkbox"
        :aria-checked="checkedCount === ingredients.length"
        :aria-label="`${checkedCount} of ${ingredients.length} ingredients selected for ${food.name}`"
      >
        <span v-if="checkedCount === ingredients.length && ingredients.length > 0">✓</span>
        <span v-else-if="checkedCount > 0" class="partial-check">–</span>
      </div>

      <!-- Name & progress -->
      <div class="food-info">
        <span class="food-name">{{ food.emoji || '🍽️' }} {{ food.name }}</span>
        <span class="food-progress" v-if="ingredients.length > 0">
          {{ checkedCount }}/{{ ingredients.length }}
        </span>
      </div>

      <!-- Expand toggle -->
      <button class="expand-btn" :class="{ expanded }">
        <span class="expand-chevron">›</span>
      </button>

      <!-- Remove button -->
      <button
        class="remove-btn"
        @click.stop="handleRemove"
        title="Remove from week"
        aria-label="Remove food item"
      >✕</button>
    </div>

    <!-- Ingredient List (expandable) -->
    <Transition name="expand">
      <div v-if="expanded" class="ingredients-panel">
        <div class="ing-panel-header-row">
          <p class="ing-panel-header">Ingredients to pick up:</p>
          <p class="ing-store-hint">Tap pill to change store</p>
        </div>
        <ul class="ing-list">
          <li
            v-for="(ing, idx) in ingredients"
            :key="idx"
            class="ing-item"
            role="checkbox"
            :aria-checked="store.isIngredientChecked(weekId, food.id, idx)"
          >
            <div
              class="ing-checkbox"
              :class="{ checked: store.isIngredientChecked(weekId, food.id, idx) }"
              @click="store.toggleIngredient(weekId, food.id, idx)"
            >
              <span v-if="store.isIngredientChecked(weekId, food.id, idx)">✓</span>
            </div>
            <span
              class="ing-text"
              :class="{ 'ing-checked': store.isIngredientChecked(weekId, food.id, idx) }"
              @click="store.toggleIngredient(weekId, food.id, idx)"
            >{{ ing }}</span>
            <button
              class="ing-comment-btn"
              :class="{ 'has-comment': !!store.getIngredientComment(weekId, food.id, idx) }"
              @click.stop="openComment(idx)"
              title="Add a comment"
              aria-label="Add comment"
            >✏️</button>
            <StorePill
              :model-value="store.resolveIngStore(weekId, food.id, idx, food.recipeId)"
              :stores="store.stores"
              @update:model-value="id => store.setIngStore(weekId, food.id, idx, food.recipeId, id)"
            />
          </li>
        </ul>
        <p v-if="ingredients.length === 0" class="no-ing">No ingredients listed for this item.</p>
      </div>
    </Transition>

  </div>

  <!-- Ingredient comment modal -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="commentOpen" class="modal-overlay" @click.self="closeComment">
        <div class="modal-box comment-box">
          <div class="comment-head">
            <div>
              <div class="comment-title">Comment</div>
              <div class="comment-sub">{{ food.name }} · {{ activeIngredient }}</div>
            </div>
            <button class="comment-close" @click="closeComment" aria-label="Close">✕</button>
          </div>
          <div class="comment-body">
            <textarea
              class="comment-input"
              v-model="commentDraft"
              rows="3"
              placeholder="e.g. Get ripe ones / 2 packets / low sugar…"
            />
            <div class="comment-hint">Comments auto-remove after 2 days</div>
          </div>
          <div class="comment-actions">
            <button class="btn btn-secondary" @click="closeComment">Cancel</button>
            <button class="btn btn-ghost" @click="clearComment" :disabled="!commentDraft.trim()">Clear</button>
            <button class="btn btn-primary" @click="saveComment" :disabled="!canSaveComment">Save</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMealStore } from '../stores/mealStore.js'
import StorePill from './StorePill.vue'

const props = defineProps({
  food:     { type: Object, required: true },
  weekId:   { type: Number, required: true },
  category: { type: String, required: true },
})

const store = useMealStore()

const expanded = ref(false)

const ingredients = computed(() => store.getFoodIngredients(props.food))

const checkedCount = computed(() => store.getCheckedCountForFood(props.weekId, props.food.id))

// Ingredient comments
const commentOpen = ref(false)
const commentIdx = ref(null)
const commentDraft = ref('')

const activeIngredient = computed(() => {
  const idx = commentIdx.value
  if (idx == null) return ''
  return ingredients.value[idx] || ''
})

const canSaveComment = computed(() => commentDraft.value.trim().length > 0)

function openComment(idx) {
  commentIdx.value = idx
  commentDraft.value = store.getIngredientComment(props.weekId, props.food.id, idx) || ''
  commentOpen.value = true
}

function closeComment() {
  commentOpen.value = false
  commentIdx.value = null
  commentDraft.value = ''
}

function saveComment() {
  if (commentIdx.value == null) return
  store.setIngredientComment(props.weekId, props.food.id, commentIdx.value, commentDraft.value)
  closeComment()
}

function clearComment() {
  if (commentIdx.value == null) return
  store.setIngredientComment(props.weekId, props.food.id, commentIdx.value, '')
  closeComment()
}

function toggleExpanded() {
  expanded.value = !expanded.value
}

function toggleAllIngredients() {
  const ings = ingredients.value
  if (ings.length === 0) return

  if (checkedCount.value > 0) {
    // Uncheck all
    ings.forEach((_, idx) => {
      if (store.isIngredientChecked(props.weekId, props.food.id, idx)) {
        store.toggleIngredient(props.weekId, props.food.id, idx)
      }
    })
  } else {
    // Check all
    ings.forEach((_, idx) => {
      if (!store.isIngredientChecked(props.weekId, props.food.id, idx)) {
        store.toggleIngredient(props.weekId, props.food.id, idx)
      }
    })
    if (!expanded.value) expanded.value = true
  }
}

function handleRemove() {
  store.removeFoodFromWeek(props.weekId, props.category, props.food.id)
}
</script>

<style scoped>
.food-item-wrapper {
  border-bottom: 1px solid rgba(237,224,204,0.5);
  animation: fadeIn 0.2s var(--ease) both;
}
.food-item-wrapper:last-child { border-bottom: none; }

/* ── Food Row ── */
.food-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px 11px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.food-row:hover { background: rgba(237,224,204,0.25); }

/* ── Food Checkbox ── */
.food-check {
  width: 20px; height: 20px;
  border: 2px solid var(--parchment-dark);
  border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: all 0.18s;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.food-check:hover { border-color: var(--sage); }
.food-check.some-checked {
  background: var(--sage-lt);
  border-color: var(--sage);
  color: #fff;
}
.food-check.all-checked {
  background: var(--sage);
  border-color: var(--sage);
  color: #fff;
}

.partial-check { font-size: 13px; }

/* ── Food info ── */
.food-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.food-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--charcoal);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.food-progress {
  font-size: 11px;
  color: var(--brown-lt);
  background: var(--parchment);
  padding: 2px 7px;
  border-radius: 10px;
  flex-shrink: 0;
}

/* ── Expand button ── */
.expand-btn {
  background: none; border: none;
  cursor: pointer;
  width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
  color: var(--parchment-dark);
  transition: all 0.2s;
  flex-shrink: 0;
}
.expand-btn:hover { color: var(--brown-lt); }
.expand-btn.expanded .expand-chevron { transform: rotate(90deg); }

.expand-chevron {
  font-size: 16px;
  display: inline-block;
  transition: transform 0.2s var(--ease);
}

/* ── Remove button ── */
.remove-btn {
  background: none; border: none;
  cursor: pointer;
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  color: var(--parchment-dark);
  border-radius: 4px;
  transition: all 0.15s;
  flex-shrink: 0;
  opacity: 0;
}
.food-row:hover .remove-btn { opacity: 1; }
.remove-btn:hover { background: #fee; color: #c0392b; }

/* ── Ingredients Panel ── */
.ingredients-panel {
  background: rgba(250,246,239,0.7);
  border-top: 1px dashed var(--parchment);
  padding: 12px 16px 14px 48px;
}

.ing-panel-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.ing-panel-header {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--brown-lt);
}

.ing-store-hint {
  font-size: 10px;
  color: var(--brown-lt);
  font-style: italic;
}

.ing-list { list-style: none; }

.ing-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 0;
  border-bottom: 1px solid rgba(237,224,204,0.4);
}
.ing-item:last-child { border-bottom: none; }

/* ── Ingredient Checkbox ── */
.ing-checkbox {
  width: 18px; height: 18px;
  border: 2px solid var(--parchment-dark);
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  transition: all 0.18s;
  cursor: pointer;
}
.ing-checkbox.checked {
  background: var(--mustard);
  border-color: var(--mustard);
}

.ing-text {
  font-size: 13.5px;
  color: var(--charcoal);
  transition: all 0.18s;
  flex: 1;
  cursor: pointer;
}
.ing-checked {
  text-decoration: line-through;
  color: var(--brown-lt);
}

.ing-comment-btn {
  background: none;
  border: none;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 8px;
  color: var(--brown-lt);
  transition: all 0.15s var(--ease);
  flex-shrink: 0;
  opacity: 0.7;
}
.ing-comment-btn:hover {
  opacity: 1;
  background: var(--cream);
  color: var(--terracotta);
}
.ing-comment-btn.has-comment {
  opacity: 1;
  color: var(--terracotta);
}

.no-ing { font-size: 12px; color: var(--brown-lt); font-style: italic; }

/* ── Expand animation ── */
.expand-enter-active, .expand-leave-active {
  transition: all 0.25s var(--ease);
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to, .expand-leave-from {
  opacity: 1;
  max-height: 400px;
}

/* ── Comment modal ── */
.comment-box {
  max-width: 480px;
}
.comment-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 22px 12px;
  border-bottom: 1.5px solid var(--parchment);
}
.comment-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--charcoal);
}
.comment-sub {
  font-size: 12.5px;
  color: var(--brown-lt);
  margin-top: 3px;
}
.comment-close {
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
.comment-close:hover { background: var(--parchment); color: var(--charcoal); }

.comment-body {
  padding: 14px 18px 0;
}
.comment-input {
  width: 100%;
  resize: vertical;
  min-height: 80px;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-family: var(--font-body);
  font-size: 13.5px;
  color: var(--charcoal);
  outline: none;
}
.comment-input:focus {
  border-color: var(--terracotta);
  box-shadow: 0 0 0 3px rgba(193, 68, 14, 0.1);
}
.comment-hint {
  font-size: 11.5px;
  color: var(--brown-lt);
  font-style: italic;
  margin-top: 8px;
}
.comment-actions {
  padding: 12px 18px 16px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
