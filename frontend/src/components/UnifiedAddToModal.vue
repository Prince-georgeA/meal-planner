<template>
  <Teleport to="body">
    <Transition name="modal">
      <div class="modal-overlay" @click.self="$emit('close')">
        <div class="modal-box add-modal-box">
          <button class="modal-close" @click="$emit('close')">✕</button>

          <!-- Head -->
          <div class="modal-head">
            <div class="modal-title">Add "{{ recipe.name }}"</div>
            <div class="modal-sub">Choose where to add this recipe</div>
          </div>

          <!-- Destination tabs -->
          <div class="dest-tabs">
            <button class="dest-tab" :class="{ active: dest === 'week' }" @click="dest = 'week'">
              📋 Add to Week
            </button>
            <button class="dest-tab" :class="{ active: dest === 'cal' }" @click="dest = 'cal'">
              📅 Add to Calendar Day
            </button>
          </div>

          <!-- ── WEEK PANEL ── -->
          <div v-if="dest === 'week'" class="dest-panel">
            <!-- Recipe strip -->
            <div class="add-recipe-strip">
              <span class="ars-emoji">{{ recipe.emoji }}</span>
              <div>
                <div class="ars-name">{{ recipe.name }}</div>
                <div class="ars-cat">{{ recipe.category ? `${CAT_META[recipe.category].emoji} ${CAT_META[recipe.category].label}` : 'Uncategorised' }}</div>
              </div>
            </div>

            <!-- Week picker -->
            <div>
              <div class="picker-lbl">Select a week plan</div>
              <div class="week-pick-list">
                <div
                  v-for="week in store.weeks"
                  :key="week.id"
                  class="week-pick-row"
                  :class="{ selected: atWeekId === week.id }"
                  @click="pickWeek(week.id)"
                >
                  <div class="wpr-info">
                    <div class="wpr-label">{{ week.label }}</div>
                    <div class="wpr-dates">{{ week.dates || 'No dates set' }}</div>
                  </div>
                  <div class="wpr-radio">
                    <div class="wpr-radio-dot"></div>
                  </div>
                </div>
                <div v-if="!store.weeks.length" class="no-weeks-hint">
                  No weeks yet — create one first.
                </div>
              </div>
            </div>

            <!-- Category picker -->
            <div>
              <div class="picker-lbl">Meal category</div>
              <div class="cat-picker-grid">
                <button
                  v-for="cat in CATEGORIES"
                  :key="cat"
                  class="cat-pick-btn"
                  :class="atWeekId && atWeekCat === cat ? `sel-${cat}` : ''"
                  @click="atWeekCat = cat"
                >
                  {{ CAT_META[cat].emoji }} {{ CAT_META[cat].label }}
                </button>
              </div>
            </div>

            <!-- Day picker (only if week has a date range) -->
            <div v-if="selectedWeekHasRange">
              <div class="range-info-callout">
                <strong>📅 {{ selectedWeek.label }}</strong> runs <strong>{{ selectedWeek.dates }}</strong>.
                Pick which calendar day this recipe should appear on too.
              </div>
              <div class="picker-lbl" style="margin-top:12px;">Which day?</div>
              <div class="range-day-grid">
                <button
                  v-for="d in rangeDays"
                  :key="store._dk(d)"
                  class="range-day-btn"
                  :class="{
                    sel:      atRangeDay && sameDay(d, atRangeDay),
                    'is-today': sameDay(d, today),
                  }"
                  @click="atRangeDay = d"
                >
                  <div class="rdb-day">{{ DAYS_S[d.getDay()] }}</div>
                  <div class="rdb-date">{{ d.getDate() }}</div>
                </button>
              </div>
            </div>

            <!-- Summary -->
            <div v-if="wSummaryReady" class="confirm-strip">
              ✅ <span v-html="wSummaryText"></span>
            </div>
          </div>

          <!-- ── CALENDAR PANEL ── -->
          <div v-else class="dest-panel">
            <div class="add-recipe-strip">
              <span class="ars-emoji">{{ recipe.emoji }}</span>
              <div>
                <div class="ars-name">{{ recipe.name }}</div>
                <div class="ars-cat">{{ recipe.category ? `${CAT_META[recipe.category].emoji} ${CAT_META[recipe.category].label}` : 'Uncategorised' }}</div>
              </div>
            </div>

            <div>
              <div class="picker-lbl">Select a date</div>
              <input type="date" class="date-pick-input" v-model="atCalDateStr" />
            </div>

            <div>
              <div class="picker-lbl">Meal category</div>
              <div class="cat-picker-grid">
                <button
                  v-for="cat in CATEGORIES"
                  :key="cat"
                  class="cat-pick-btn"
                  :class="atCalCat === cat ? `sel-${cat}` : ''"
                  @click="atCalCat = cat"
                >
                  {{ CAT_META[cat].emoji }} {{ CAT_META[cat].label }}
                </button>
              </div>
            </div>

            <div v-if="cSummaryReady" class="confirm-strip">
              ✅ Will add <strong>{{ recipe.emoji }} {{ recipe.name }}</strong>
              to <strong>{{ calDateLabel }}</strong> → {{ CAT_META[atCalCat].emoji }} {{ CAT_META[atCalCat].label }}
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-foot">
            <span class="at-hint" :style="{ color: addReady ? 'var(--sage)' : 'var(--brown-lt)' }">{{ hintText }}</span>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
              <button class="btn btn-primary" :disabled="!addReady" @click="confirm">Add Recipe</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMealStore, CAT_META, CATEGORIES } from '../stores/mealStore.js'

const props = defineProps({ recipe: { type: Object, required: true } })
const emit  = defineEmits(['close'])
const store = useMealStore()

const DAYS_S   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
const MONTHS_S = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

const today = new Date(); today.setHours(0,0,0,0)

// Tab
const dest = ref('week')

// Week panel state
const atWeekId   = ref(null)
const atWeekCat  = ref(props.recipe.category || null)
const atRangeDay = ref(null)

// Calendar panel state
const atCalDateStr = ref(store._dk(today))
const atCalCat     = ref(props.recipe.category || null)

// ── Week helpers ──────────────────────────────────────────────────────────
const selectedWeek = computed(() => store.weeks.find(w => w.id === atWeekId.value) || null)

const selectedWeekHasRange = computed(() =>
  !!(selectedWeek.value?.dateFrom && selectedWeek.value?.dateTo)
)

const rangeDays = computed(() => {
  const w = selectedWeek.value
  if (!w?.dateFrom || !w?.dateTo) return []
  const days = []
  const d = new Date(w.dateFrom)
  while (d.getTime() <= w.dateTo) {
    days.push(new Date(d))
    d.setDate(d.getDate() + 1)
  }
  return days
})

function pickWeek(id) {
  atWeekId.value   = id
  atRangeDay.value = null
}

function sameDay(a, b) {
  if (!a || !b) return false
  return a.getFullYear() === b.getFullYear() &&
         a.getMonth()    === b.getMonth()    &&
         a.getDate()     === b.getDate()
}

function fmtDate(d) {
  return `${d.getDate()} ${MONTHS_S[d.getMonth()]} ${d.getFullYear()}`
}

// ── Summary / validation ──────────────────────────────────────────────────
const dayRequired = computed(() => selectedWeekHasRange.value)

const wSummaryReady = computed(() =>
  !!(atWeekId.value && atWeekCat.value && (!dayRequired.value || atRangeDay.value))
)

const wSummaryText = computed(() => {
  if (!wSummaryReady.value) return ''
  const w = selectedWeek.value
  const dayNote = atRangeDay.value
    ? ` · Appears on <strong>${fmtDate(atRangeDay.value)}</strong> in Calendar`
    : ` · <em>No date range — won't sync to Calendar</em>`
  return `Will add <strong>${props.recipe.emoji} ${props.recipe.name}</strong> to <strong>${w.label}</strong> → ${CAT_META[atWeekCat.value].emoji} ${CAT_META[atWeekCat.value].label}${dayNote}`
})

const calDateLabel = computed(() => {
  if (!atCalDateStr.value) return ''
  const [y, m, d] = atCalDateStr.value.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  return fmtDate(date)
})

const cSummaryReady = computed(() => !!(atCalDateStr.value && atCalCat.value))

const addReady = computed(() =>
  dest.value === 'week' ? wSummaryReady.value : cSummaryReady.value
)

const hintText = computed(() => {
  if (dest.value === 'week') {
    if (!atWeekId.value)  return 'Select a week plan'
    if (!atWeekCat.value) return 'Select a meal category'
    if (dayRequired.value && !atRangeDay.value) return 'Pick a day within the week range'
    return 'Ready to add ✓'
  } else {
    if (!atCalDateStr.value || !atCalCat.value) return 'Pick a date and category'
    return 'Ready to add ✓'
  }
})

// ── Confirm ───────────────────────────────────────────────────────────────
function confirm() {
  if (!addReady.value) return
  const r = props.recipe
  if (dest.value === 'week') {
    const calDateStr = atRangeDay.value ? store._dk(atRangeDay.value) : null
    store.addRecipeToWeek(atWeekId.value, atWeekCat.value, r.id, calDateStr)
    if (calDateStr) {
      store.showToast(`✅ ${r.emoji} ${r.name} → ${selectedWeek.value.label} / ${CAT_META[atWeekCat.value].label} · also on ${fmtDate(atRangeDay.value)}`)
    }
  } else {
    store.addRecipeToDay(atCalDateStr.value, atCalCat.value, r)
  }
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(44,36,22,0.52);
  display: flex; align-items: center; justify-content: center; z-index: 400;
  backdrop-filter: blur(5px); animation: ovIn 0.18s var(--ease) both;
}
@keyframes ovIn { from { opacity:0; } to { opacity:1; } }

.modal-box {
  background: var(--warm-white); border-radius: var(--radius-xl);
  width: 560px; max-width: calc(100vw - 32px); max-height: 90vh;
  overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 24px 60px rgba(44,36,22,0.25), 0 0 0 1px rgba(255,255,255,0.5) inset;
  animation: mIn 0.22s var(--ease) both; position: relative;
}
@keyframes mIn { from { opacity:0; transform:scale(0.96) translateY(12px); } to { opacity:1; transform:scale(1) translateY(0); } }

.modal-close {
  position: absolute; top: 14px; right: 14px; width: 30px; height: 30px;
  border-radius: 50%; border: none; background: var(--cream); color: var(--brown-lt);
  font-size: 17px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.12s; z-index: 1;
}
.modal-close:hover { background: var(--parchment); }

.modal-head { padding: 20px 22px 14px; border-bottom: 1.5px solid var(--parchment); flex-shrink: 0; }
.modal-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; color: var(--charcoal); }
.modal-sub   { font-size: 12.5px; color: var(--brown-lt); margin-top: 3px; }

/* Destination tabs */
.dest-tabs { display: flex; border-bottom: 1.5px solid var(--parchment); flex-shrink: 0; background: var(--cream); }
.dest-tab {
  flex: 1; padding: 12px 16px; border: none; background: transparent;
  font-family: var(--font-body); font-size: 13.5px; font-weight: 600;
  cursor: pointer; color: var(--brown-lt);
  border-bottom: 2.5px solid transparent; transition: all 0.18s var(--ease);
  display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: -1.5px;
}
.dest-tab:hover:not(.active) { color: var(--brown-mid); background: var(--parchment); }
.dest-tab.active { color: var(--terracotta); border-bottom-color: var(--terracotta); background: var(--warm-white); }

/* Panels */
.dest-panel { padding: 16px 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 16px; }

/* Recipe strip */
.add-recipe-strip {
  display: flex; align-items: center; gap: 10px;
  background: var(--cream); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md); padding: 10px 14px; flex-shrink: 0;
}
.ars-emoji { font-size: 24px; }
.ars-name  { font-size: 14px; font-weight: 700; color: var(--charcoal); }
.ars-cat   { font-size: 11.5px; color: var(--brown-lt); }

/* Picker labels */
.picker-lbl { font-size: 10.5px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--brown-lt); margin-bottom: 8px; }

/* Week list */
.week-pick-list { display: flex; flex-direction: column; gap: 7px; }
.week-pick-row {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  border: 2px solid var(--parchment); border-radius: var(--radius-md);
  cursor: pointer; transition: all 0.15s var(--ease); background: var(--cream);
}
.week-pick-row:hover { border-color: var(--parchment-dark); background: var(--warm-white); }
.week-pick-row.selected { border-color: var(--terracotta); background: var(--terracotta-bg, #fff0ea); }
.wpr-info { flex: 1; }
.wpr-label { font-size: 14px; font-weight: 700; color: var(--charcoal); }
.wpr-dates { font-size: 11.5px; color: var(--brown-lt); margin-top: 1px; }
.wpr-radio { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--parchment-dark); display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.15s; }
.week-pick-row.selected .wpr-radio { border-color: var(--terracotta); background: var(--terracotta); }
.wpr-radio-dot { width: 7px; height: 7px; border-radius: 50%; background: #fff; display: none; }
.week-pick-row.selected .wpr-radio-dot { display: block; }
.no-weeks-hint { font-size: 13px; color: var(--brown-lt); font-style: italic; padding: 8px 0; }

/* Category picker grid */
.cat-picker-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.cat-pick-btn {
  padding: 9px 14px; border-radius: var(--radius-md); border: 2px solid var(--parchment);
  cursor: pointer; font-family: var(--font-body); font-size: 13px; font-weight: 600;
  display: flex; align-items: center; gap: 7px; transition: all 0.16s var(--ease);
  background: var(--cream); color: var(--charcoal);
}
.cat-pick-btn:hover { border-color: var(--parchment-dark); background: var(--warm-white); }
.sel-breakfast { background:#fff3e0; border-color:#b84e00; color:#b84e00; }
.sel-lunch     { background:#e8f5e9; border-color:#2a6e30; color:#2a6e30; }
.sel-dinner    { background:#e8eaf6; border-color:#283593; color:#283593; }
.sel-snacks    { background:#fce4ec; border-color:#880e4f; color:#880e4f; }

/* Range day picker */
.range-info-callout {
  background: var(--mustard-bg, #fff8e1); border: 1.5px solid var(--mustard-lt, #f5c842);
  border-radius: var(--radius-md); padding: 9px 13px; font-size: 12.5px; color: var(--mustard, #c4880a);
}
.range-day-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 6px; }
.range-day-btn {
  padding: 8px 4px; border-radius: var(--radius-sm); border: 2px solid var(--parchment);
  background: var(--cream); font-family: var(--font-body); cursor: pointer;
  text-align: center; transition: all 0.14s var(--ease);
}
.range-day-btn:hover { border-color: var(--parchment-dark); background: var(--warm-white); }
.range-day-btn.sel { border-color: var(--terracotta); background: var(--terracotta-bg, #fff0ea); color: var(--terracotta); }
.range-day-btn.is-today { border-color: var(--mustard, #c4880a); font-weight: 800; }
.rdb-day  { font-size: 9.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; opacity: 0.7; }
.rdb-date { font-size: 15px; font-weight: 700; margin-top: 2px; }

/* Confirm strip */
.confirm-strip {
  background: var(--sage-bg, #edf5ee); border: 1.5px solid var(--sage-lt, #8ab890);
  border-radius: var(--radius-md); padding: 10px 14px; font-size: 12.5px;
  color: var(--sage, #5e8c65); display: flex; align-items: flex-start; gap: 8px;
  animation: fadeUp 0.18s var(--ease) both;
}
@keyframes fadeUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

/* Date input */
.date-pick-input {
  width: 100%; background: var(--cream); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md); padding: 9px 14px; font-family: var(--font-body);
  font-size: 14px; color: var(--charcoal); outline: none; transition: border-color 0.18s; cursor: pointer;
}
.date-pick-input:focus { border-color: var(--terracotta); box-shadow: 0 0 0 3px rgba(193,68,14,0.1); }

/* Footer */
.modal-foot {
  padding: 12px 20px; border-top: 1.5px solid var(--parchment);
  display: flex; align-items: center; justify-content: space-between;
  flex-shrink: 0; background: var(--cream);
}
.at-hint { font-size: 12px; transition: color 0.2s; }

/* Transitions */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
