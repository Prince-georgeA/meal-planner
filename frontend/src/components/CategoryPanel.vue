<template>
  <div class="category-panel" :class="`cat-${category}`">

    <!-- Panel Header -->
    <div class="panel-header">
      <div class="panel-header-left">
        <span class="cat-emoji">{{ meta.emoji }}</span>
        <span class="cat-name">{{ meta.label }}</span>
        <span class="cat-count" v-if="foods.length > 0">{{ foods.length }}</span>
      </div>
      <button class="btn-add-food" @click="$emit('add-food')" :aria-label="`Add food to ${meta.label}`">
        <span>＋</span>
      </button>
    </div>

    <!-- Food List -->
    <div class="food-list" v-if="foods.length > 0">
      <FoodItem
        v-for="food in foods"
        :key="food.id"
        :food="food"
        :week-id="weekId"
        :category="category"
      />
    </div>

    <div class="empty-state" v-else>
      <div class="empty-icon">{{ meta.emoji }}</div>
      <p class="empty-text">No {{ meta.label.toLowerCase() }} planned</p>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CAT_META } from '../stores/mealStore.js'
import FoodItem from './FoodItem.vue'

const props = defineProps({
  weekId:   { type: Number, required: true },
  category: { type: String, required: true },
  foods:    { type: Array,  default: () => [] },
})

defineEmits(['add-food'])

const meta = computed(() => CAT_META[props.category])
</script>

<style scoped>
.category-panel {
  background: var(--warm-white);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.35s var(--ease) both;
}

/* ── Header colour variants ── */
.cat-breakfast .panel-header { background: linear-gradient(90deg, #fff8f0 0%, var(--warm-white) 100%); }
.cat-lunch     .panel-header { background: linear-gradient(90deg, #f0fff3 0%, var(--warm-white) 100%); }
.cat-dinner    .panel-header { background: linear-gradient(90deg, #f0f2ff 0%, var(--warm-white) 100%); }
.cat-snacks    .panel-header { background: linear-gradient(90deg, #fff0f5 0%, var(--warm-white) 100%); }

/* ── Panel Header ── */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--parchment);
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 9px;
}

.cat-emoji { font-size: 18px; }

.cat-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--charcoal);
}

.cat-count {
  background: var(--parchment);
  color: var(--brown-mid);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
}

/* ── Add Food Button ── */
.btn-add-food {
  width: 28px; height: 28px;
  background: none;
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  color: var(--brown-lt);
  cursor: pointer;
  transition: all 0.18s var(--ease);
}
.btn-add-food:hover {
  background: var(--terracotta-bg);
  border-color: var(--terracotta);
  color: var(--terracotta);
}

/* ── Food list ── */
.food-list { flex: 1; }

/* ── Empty State ── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  gap: 6px;
}
.empty-icon { font-size: 26px; opacity: 0.35; }
.empty-text { font-size: 12px; color: var(--brown-lt); font-style: italic; }
</style>
