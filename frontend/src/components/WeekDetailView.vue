<template>
  <div class="week-detail">

    <!-- Top bar -->
    <div class="detail-topbar">
      <div class="topbar-left">
        <button class="back-btn" @click="$emit('back')">
          ← <span>All Weeks</span>
        </button>
        <div class="detail-title-group">
          <h1
            class="detail-title"
            @click="openDatesModal"
            title="Click to rename or set dates"
          >
            {{ week.label }}
            <span class="edit-hint">✏️</span>
          </h1>
          <p
            class="detail-dates"
            @click="openDatesModal"
            :title="week.dates ? 'Edit date range' : 'Set date range for calendar sync'"
          >
            {{ week.dates || 'Set dates →' }} &nbsp;·&nbsp; 🛒 Market day: Fri / Sat
          </p>
        </div>
      </div>

      <div class="topbar-actions" v-if="checkedCount > 0">
        <button class="btn btn-ghost btn-clear" @click="confirmClear = true">
          ↺ Clear all
        </button>
        <button class="btn btn-whatsapp" @click="shareWhatsApp">
          <span>📱</span> Send via WhatsApp
          <span class="wapp-count">{{ checkedCount }}</span>
        </button>
      </div>
    </div>

    <!-- Shopping summary bar (when items selected) -->
    <Transition name="fade">
      <div class="shopping-bar" v-if="checkedCount > 0">
        <span class="shopping-bar-icon">🛒</span>
        <span class="shopping-bar-text">
          <strong>{{ checkedCount }}</strong> ingredient{{ checkedCount !== 1 ? 's' : '' }} selected for market day
        </span>
        <div class="shopping-bar-actions">
          <button class="btn btn-whatsapp btn-sm" @click="shareWhatsApp">
            📱 Send to WhatsApp
          </button>
        </div>
      </div>
    </Transition>

    <!-- Categories 2x2 grid -->
    <div class="categories-grid">
      <CategoryPanel
        v-for="cat in categories"
        :key="cat"
        :week-id="week.id"
        :category="cat"
        :foods="week.categories[cat]"
        @add-food="$emit('add-food', { weekId: week.id, category: cat })"
      />
    </div>

    <!-- Confirm clear modal + Set dates modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="confirmClear" class="modal-overlay" @click.self="confirmClear = false">
          <div class="modal-box" style="max-width: 360px;">
            <h2 class="modal-title">Clear All Selections?</h2>
            <p style="font-size: 14px; color: var(--brown-mid); margin: 12px 0 24px;">
              This will uncheck all ingredients for {{ week.label }}.
            </p>
            <div class="modal-actions" style="justify-content: flex-end;">
              <button class="btn btn-secondary" @click="confirmClear = false">Cancel</button>
              <button class="btn btn-danger" @click="handleClear">Clear All</button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="modal">
        <div v-if="showDatesModal" class="modal-overlay" @click.self="showDatesModal = false">
          <div class="modal-box" style="max-width: 420px;">
            <h2 class="modal-title">Set Date Range</h2>
            <p class="modal-sub">
              Link <strong>{{ datesLabel }}</strong> to a calendar date range so meals sync automatically.
            </p>

            <div class="form-group">
              <label class="form-label">Week Name</label>
              <input class="form-input" v-model="datesLabel" />
            </div>

            <div class="form-group">
              <label class="form-label">Date Range</label>
              <div class="date-range-row">
                <div class="date-range-field">
                  <label class="form-sublabel">From</label>
                  <input type="date" class="form-input" v-model="datesFrom" />
                </div>
                <div class="date-range-field">
                  <label class="form-sublabel">To</label>
                  <input type="date" class="form-input" v-model="datesTo" />
                </div>
              </div>
            </div>

            <div class="modal-actions">
              <button class="btn btn-secondary" @click="showDatesModal = false">Cancel</button>
              <button
                class="btn btn-primary"
                @click="saveDates"
                :disabled="!datesFrom || !datesTo"
              >
                Save &amp; Sync
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMealStore } from '../stores/mealStore.js'
import CategoryPanel from './CategoryPanel.vue'

const props = defineProps({
  week: { type: Object, required: true }
})

const emit = defineEmits(['back', 'add-food'])

const store = useMealStore()

const categories    = ['breakfast', 'lunch', 'dinner', 'snacks']
const confirmClear  = ref(false)
const showDatesModal = ref(false)
const datesLabel     = ref(props.week.label)
const datesFrom      = ref('')
const datesTo        = ref('')

const checkedCount = computed(() => store.getCheckedCountForWeek(props.week.id))

function handleClear() {
  store.clearWeekSelections(props.week.id)
  confirmClear.value = false
}

function shareWhatsApp() {
  const text = store.buildWhatsAppText(props.week.id)
  window.open(`https://wa.me/?text=${text}`, '_blank', 'noopener')
}

function openDatesModal() {
  const w = props.week
  datesLabel.value = w.label
  if (w.dateFrom) {
    const from = new Date(w.dateFrom)
    from.setHours(0, 0, 0, 0)
    datesFrom.value = store._dk(from)
  } else {
    datesFrom.value = ''
  }
  if (w.dateTo) {
    const to = new Date(w.dateTo)
    to.setHours(0, 0, 0, 0)
    datesTo.value = store._dk(to)
  } else {
    datesTo.value = ''
  }
  showDatesModal.value = true
}

function saveDates() {
  const label = datesLabel.value?.trim() || props.week.label
  store.updateWeekLabel(
    props.week.id,
    label,
    undefined,                // let store derive dates string
    datesFrom.value || null,
    datesTo.value   || null,
  )
  showDatesModal.value = false
}
</script>

<style scoped>
.week-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 40px 80px;
}

/* ── Top bar ── */
.detail-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 28px 0 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.topbar-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-btn {
  display: flex; align-items: center; gap: 5px;
  background: none; border: none;
  font-family: var(--font-body);
  font-size: 14px; color: var(--brown-lt);
  cursor: pointer; padding: 6px 0;
  transition: color 0.2s;
  white-space: nowrap;
  margin-top: 4px;
}
.back-btn:hover { color: var(--terracotta); }
.back-btn span { display: none; }

.detail-title-group { flex: 1; }

.detail-title {
  font-family: var(--font-display);
  font-size: clamp(26px, 4vw, 34px);
  font-weight: 700;
  color: var(--charcoal);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  line-height: 1.1;
  margin-bottom: 5px;
  transition: color 0.2s;
}
.detail-title:hover { color: var(--terracotta); }

.edit-hint {
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s;
}
.detail-title:hover .edit-hint { opacity: 1; }

.detail-dates {
  font-size: 13px;
  color: var(--brown-lt);
  cursor: pointer;
  transition: color 0.2s;
}
.detail-dates:hover { color: var(--brown-mid); }

/* ── Topbar Actions ── */
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-clear {
  font-size: 13px;
  padding: 8px 14px;
  color: var(--brown-mid);
}

.btn-whatsapp {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: #25d366;
  color: #fff;
  border: none;
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-whatsapp:hover { background: #1ebe5a; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(37,211,102,0.4); }

.wapp-count {
  background: rgba(0,0,0,0.2);
  border-radius: 10px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 700;
}

.btn-sm { padding: 7px 14px; font-size: 12px; }

/* ── Shopping bar ── */
.shopping-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--charcoal);
  border-radius: var(--radius-lg);
  padding: 14px 20px;
  margin-bottom: 24px;
  animation: slideDown 0.25s var(--ease) both;
}

.shopping-bar-icon { font-size: 20px; }

.shopping-bar-text {
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  flex: 1;
}

.shopping-bar-text strong { color: var(--mustard-lt); }

/* ── Categories Grid ── */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

/* ── Animations ── */
.slide-enter-active, .slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.slide-enter-from { opacity: 0; transform: translateY(-8px); }
.slide-leave-to   { opacity: 0; transform: translateY(-8px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

/* ── Modal shared ── */
.modal-title {
  font-family: var(--font-display);
  font-size: 22px; font-weight: 700; color: var(--charcoal);
  margin-bottom: 4px;
}
.modal-sub {
  font-size: 13px;
  color: var(--brown-lt);
  margin-bottom: 18px;
}
.modal-actions { display: flex; gap: 10px; }

/* Date range fields (match Home view styling) */
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

@media (max-width: 768px) {
  .week-detail { padding: 0 20px 60px; }
  .categories-grid { grid-template-columns: 1fr; }
  .back-btn span { display: inline; }
}

@media (max-width: 480px) {
  .topbar-left { flex-direction: column; gap: 8px; }
}
</style>
