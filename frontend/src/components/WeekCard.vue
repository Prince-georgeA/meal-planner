<template>
  <div class="week-card" @click="$emit('click')" role="button" tabindex="0" @keydown.enter="$emit('click')">
    <!-- Accent bar -->
    <div class="card-accent"></div>

    <!-- Top row -->
    <div class="card-top">
      <div>
        <p class="card-num">{{ week.label }}</p>
        <p class="card-dates" v-if="week.dates">
          {{ week.dates }}
          <span v-if="calSynced" class="cal-synced-badge">📅 Cal Synced</span>
        </p>
        <p class="card-dates empty-dates" v-else>No dates set</p>
      </div>
      <div class="card-badge" v-if="totalItems > 0">{{ totalItems }}</div>
    </div>

    <!-- Category pills -->
    <div class="card-pills" v-if="totalItems > 0">
      <span
        v-for="[cat, foods] in filledCategories"
        :key="cat"
        class="pill"
        :class="CAT_META[cat].pillClass"
      >
        {{ CAT_META[cat].emoji }} {{ foods.length }}
      </span>
    </div>
    <p v-else class="no-meals-hint">No meals planned yet</p>

    <!-- Card actions -->
    <div class="card-actions" @click.stop>
      <button
        class="card-action-btn dates-btn"
        @click="$emit('edit-dates', week)"
        :title="week.dates ? 'Edit date range' : 'Set date range for calendar sync'"
      >
        📅 {{ week.dates ? 'Edit dates' : 'Set dates' }}
      </button>
      <button class="card-action-btn" @click="$emit('copy')" title="Copy to new week">
        📋 Copy
      </button>
      <button class="card-action-btn danger" @click="$emit('delete')" title="Delete week">
        🗑
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMealStore, CAT_META } from '../stores/mealStore.js'

const props = defineProps({
  week: { type: Object, required: true },
})

defineEmits(['click', 'copy', 'delete', 'edit-dates'])

const store = useMealStore()

const totalItems = computed(() =>
  Object.values(props.week.categories).reduce((s, arr) => s + arr.length, 0)
)

const filledCategories = computed(() =>
  Object.entries(props.week.categories).filter(([, foods]) => foods.length > 0)
)

const calSynced = computed(() => store.weekHasCalendarData(props.week.id))
</script>

<style scoped>
.week-card {
  background: var(--warm-white);
  border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg);
  padding: 0 0 14px;
  cursor: pointer;
  transition: all 0.25s var(--ease);
  position: relative;
  overflow: hidden;
  animation: slideDown 0.3s var(--ease) both;
  display: flex;
  flex-direction: column;
  min-height: 170px;
}

.week-card:hover {
  border-color: var(--terracotta);
  transform: translateY(-4px);
  box-shadow: 0 10px 28px var(--shadow-md);
}

.card-accent {
  height: 4px;
  background: linear-gradient(90deg, var(--terracotta), var(--mustard));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s var(--ease);
}
.week-card:hover .card-accent,
.week-card:focus .card-accent { transform: scaleX(1); }

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 12px;
}

.card-num {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--charcoal);
  margin-bottom: 3px;
}

.card-dates {
  font-size: 12px;
  color: var(--brown-lt);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.empty-dates { font-style: italic; }

.cal-synced-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: var(--mustard-bg, #fff8e1);
  color: var(--mustard, #c4880a);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  letter-spacing: 0.04em;
}

.card-badge {
  width: 28px; height: 28px;
  background: var(--terracotta);
  color: #fff;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  flex-shrink: 0;
}

.card-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 20px;
  flex: 1;
}

.no-meals-hint {
  font-size: 12px;
  color: var(--parchment-dark);
  padding: 0 20px;
  font-style: italic;
  flex: 1;
}

.card-actions {
  display: flex;
  gap: 6px;
  padding: 10px 20px 0;
  margin-top: auto;
  opacity: 0;
  transition: opacity 0.2s;
  flex-wrap: wrap;
}
.week-card:hover .card-actions { opacity: 1; }

.card-action-btn {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  background: var(--cream);
  border: 1px solid var(--parchment);
  border-radius: var(--radius-sm);
  padding: 5px 10px;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--brown-mid);
}
.card-action-btn:hover        { background: var(--parchment); }
.card-action-btn.danger:hover { background: #fee; color: #c0392b; border-color: #fcc; }
.card-action-btn.dates-btn:hover {
  background: var(--mustard-bg, #fff8e1);
  color: var(--mustard, #c4880a);
  border-color: var(--mustard-lt, #f5c842);
}
</style>
