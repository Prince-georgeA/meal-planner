<template>
  <div class="cal-view">

    <!-- Toolbar -->
    <div class="cal-toolbar">
      <div class="cal-month-nav">
        <button class="icon-btn" @click="changeMonth(-1)">‹</button>
        <div class="cal-month-title">{{ monthLabel }}</div>
        <button class="icon-btn" @click="changeMonth(1)">›</button>
      </div>
      <div class="cal-toolbar-right">
        <button class="today-btn" @click="goToday">Today</button>
        <div class="view-toggle">
          <button class="toggle-btn" :class="{ active: view === 'month' }" @click="view = 'month'">🗓 Month</button>
          <button class="toggle-btn" :class="{ active: view === 'agenda' }" @click="view = 'agenda'">📋 Agenda</button>
        </div>
      </div>
    </div>

    <!-- Month grid -->
    <div v-if="view === 'month'" class="cal-layout">
      <div>
        <div class="cal-grid-wrap">
          <div class="cal-weekdays">
            <div v-for="d in ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']" :key="d" class="cal-weekday">{{ d }}</div>
          </div>
          <div class="cal-days">
            <div
              v-for="cell in calCells"
              :key="cell.key"
              class="cal-cell"
              :class="{
                'other-month':   cell.otherMonth,
                'is-today':      cell.isToday,
                'is-selected':   cell.isSelected,
                'in-week-range': cell.inRange,
              }"
              @click="selectDay(cell.date)"
            >
              <div class="cell-date-num">{{ cell.date.getDate() }}</div>
              <div class="cell-chips">
                <template v-for="(chip, i) in cell.chips" :key="i">
                  <div class="cell-chip" :class="chip.cat">{{ chip.emoji }} {{ chip.name }}</div>
                </template>
                <div v-if="cell.moreCount > 0" class="cell-more">+{{ cell.moreCount }} more</div>
              </div>
              <div v-if="cell.inRange && !cell.otherMonth" class="week-range-bar"></div>
            </div>
          </div>
        </div>
        <div class="cal-legend">
          <div class="legend-item"><div class="legend-dot"></div> Today</div>
          <div class="legend-item"><div class="legend-box"></div> Selected</div>
          <div class="legend-item"><div class="legend-bar"></div> Week range</div>
        </div>
      </div>

      <!-- Day detail panel -->
      <div class="day-detail-panel">
        <div class="ddp-head">
          <div class="ddp-date">{{ selectedDateLabel }}</div>
          <div class="ddp-dayname">{{ selectedDayName }}</div>
          <button
            v-if="selectedWeek"
            class="ddp-week-pill"
            @click="$emit('open-week', selectedWeek.id)"
          >📋 {{ selectedWeek.label }} → View Week</button>
          <button
            v-else
            class="ddp-week-pill unlinked"
            @click="showLinkModal = true"
          >+ Link to a week plan</button>
        </div>
        <div class="ddp-body">
          <div v-if="selectedWeek && hasDayMeals" class="sync-note">
            🔄 <span><strong>Syncing to "{{ selectedWeek.label }}"</strong> — meals here auto-populate that week's categories.</span>
          </div>
          <div v-for="cat in CATEGORIES" :key="cat" class="meal-slot">
            <div class="slot-head" :class="cat" @click="openPicker(cat)">
              <div class="slot-label" :class="cat">
                {{ CAT_META[cat].emoji }} {{ CAT_META[cat].label }}
                <span v-if="dayMeals[cat]?.length" class="slot-count" :class="cat">{{ dayMeals[cat].length }}</span>
              </div>
              <button
                class="slot-add-btn"
                :style="{ background: catAddBg[cat] }"
                @click.stop="openPicker(cat)"
              >+</button>
            </div>
            <div v-if="dayMeals[cat]?.length" class="slot-items">
              <div v-for="(item, i) in dayMeals[cat]" :key="i" class="slot-item">
                <span>{{ item.emoji }}</span>
                <span class="slot-item-name">{{ item.name }}</span>
                <button class="slot-remove-btn" @click="removeMeal(cat, i)">✕</button>
              </div>
            </div>
            <div v-else class="slot-empty">Tap + to add a recipe</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Agenda view -->
    <div v-else class="agenda-list">
      <div
        v-for="day in agendaDays"
        :key="day.key"
        class="agenda-day"
        :class="{ 'is-today': day.isToday }"
      >
        <div class="agenda-day-head">
          <div class="agenda-day-num">{{ day.date.getDate() }}</div>
          <div class="agenda-day-meta">
            <div class="agenda-day-name">{{ day.shortDay }}{{ day.isToday ? ' · Today' : '' }}</div>
            <div class="agenda-day-sub">{{ day.monthYear }}{{ day.week ? ' · ' + day.week.label : '' }}</div>
          </div>
          <div class="agenda-chips">
            <template v-for="cat in CATEGORIES" :key="cat">
              <span v-if="day.meals[cat]?.length" class="agenda-chip" :class="cat">
                {{ CAT_META[cat].emoji }} {{ day.meals[cat].length }}
              </span>
            </template>
          </div>
        </div>
        <div class="agenda-body">
          <div v-for="cat in CATEGORIES" :key="cat" class="agenda-slot">
            <span class="agenda-slot-icon">{{ CAT_META[cat].emoji }}</span>
            <div class="agenda-slot-content">
              <div class="agenda-slot-lbl">{{ CAT_META[cat].label }}</div>
              <div v-for="item in day.meals[cat]" :key="item.recipeId" class="agenda-slot-item">
                <span>{{ item.emoji }}</span><span>{{ item.name }}</span>
              </div>
              <span v-if="!day.meals[cat]?.length" class="agenda-slot-none">Nothing planned</span>
            </div>
            <button class="agenda-slot-add" @click="selectDay(day.date); openPicker(cat)">+</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Recipe picker modal (Teleport to body) -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showLinkModal" class="modal-overlay" @click.self="showLinkModal = false">
          <div class="modal-box" style="max-width:420px;">
            <button class="modal-close-btn" @click="showLinkModal = false">✕</button>
            <div class="modal-head">
              <div class="modal-title">Link to a Week Plan</div>
              <div class="modal-sub">
                {{ selectedDateLabel }} isn't in any week's date range yet.
                Set a date range on an existing week, or create a new one.
              </div>
            </div>
            <div class="link-week-body">
              <div class="link-week-list">
                <div
                  v-for="week in store.weeks"
                  :key="week.id"
                  class="link-week-row"
                  :class="{ 'has-dates': week.dates }"
                >
                  <div class="lwr-info">
                    <div class="lwr-label">{{ week.label }}</div>
                    <div class="lwr-dates">{{ week.dates || 'No dates set yet' }}</div>
                  </div>
                  <button
                    v-if="!week.dates"
                    class="btn btn-secondary lwr-btn"
                    @click="goSetDates(week)"
                  >Set dates →</button>
                  <span v-else class="lwr-mismatch">Doesn't include this day</span>
                </div>
                <div v-if="!store.weeks.length" class="lwr-empty">
                  No weeks yet. Go to "Your Weeks" tab to create one.
                </div>
              </div>
              <div class="lwr-hint">
                💡 To include {{ selectedDateLabel }} in a week: go to <strong>Your Weeks</strong>, click
                <strong>📅 Set dates</strong> on a week, and set a range that covers this date.
              </div>
            </div>
            <div class="modal-foot">
              <div></div>
              <button class="btn btn-secondary" @click="showLinkModal = false">Close</button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="modal">
        <div v-if="pickerCat" class="modal-overlay" @click.self="pickerCat = null">
          <div class="modal-box picker-box">
            <div class="modal-head">
              <div class="modal-title">Add to {{ CAT_META[pickerCat]?.label }}</div>
              <div class="modal-sub">{{ selectedDateLabel }} · pick from your recipe library</div>
            </div>
            <!-- Search -->
            <div class="picker-search-wrap">
              <input
                ref="searchEl"
                class="picker-search"
                v-model="pickerQuery"
                placeholder="Search recipes…"
              />
            </div>
            <!-- Cat filter -->
            <div class="picker-filters">
              <button
                v-for="f in pickerFilters"
                :key="f.key"
                class="pk-filter"
                :class="{ active: pickerFilter === f.key }"
                @click="pickerFilter = f.key"
              >{{ f.label }}</button>
            </div>
            <!-- List -->
            <div class="picker-list">
              <div v-if="!filteredRecipes.length" class="picker-empty">No recipes found</div>
              <div
                v-for="r in filteredRecipes"
                :key="r.id"
                class="recipe-pick-row"
                :class="{ 'is-picked': pickerPicked.has(r.id) }"
                @click="togglePick(r.id)"
              >
                <span class="rpr-emoji">{{ r.emoji }}</span>
                <div class="rpr-info">
                  <div class="rpr-name">{{ r.name }}</div>
                  <div class="rpr-ings">{{ r.ingredients.slice(0,3).join(', ') }}</div>
                </div>
                <div class="rpr-check">{{ pickerPicked.has(r.id) ? '✓' : '' }}</div>
              </div>
            </div>
            <div class="modal-foot">
              <span class="picker-sel-info">
                <template v-if="pickerAddCount > 0 && pickerRemoveCount > 0">
                  <strong class="adding">+{{ pickerAddCount }}</strong> adding &nbsp;·&nbsp;
                  <strong class="removing">−{{ pickerRemoveCount }}</strong> removing
                </template>
                <template v-else-if="pickerAddCount > 0">
                  <strong class="adding">+{{ pickerAddCount }}</strong> recipe{{ pickerAddCount !== 1 ? 's' : '' }} to add
                </template>
                <template v-else-if="pickerRemoveCount > 0">
                  <strong class="removing">−{{ pickerRemoveCount }}</strong> recipe{{ pickerRemoveCount !== 1 ? 's' : '' }} to remove
                </template>
                <template v-else>{{ pickerPicked.size || 'No' }} selected</template>
              </span>
              <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary" @click="pickerCat = null">Cancel</button>
                <button class="btn btn-primary" :disabled="pickerAddCount === 0 && pickerRemoveCount === 0" @click="confirmPick">
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useMealStore, CAT_META, CATEGORIES } from '../stores/mealStore.js'

const emit   = defineEmits(['open-week', 'go-weeks'])
const store  = useMealStore()

// ── Calendar state ──────────────────────────────────────────────
const MONTHS   = ['January','February','March','April','May','June','July','August','September','October','November','December']
const MONTHS_S = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const DAYS_S   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

const today = new Date(); today.setHours(0,0,0,0)
const curMonth  = ref(new Date(today.getFullYear(), today.getMonth(), 1))
const selDate   = ref(new Date(today))
const view      = ref('month')

const monthLabel = computed(() => `${MONTHS[curMonth.value.getMonth()]} ${curMonth.value.getFullYear()}`)

function changeMonth(dir) {
  curMonth.value = new Date(curMonth.value.getFullYear(), curMonth.value.getMonth() + dir, 1)
}
function goToday() {
  curMonth.value = new Date(today.getFullYear(), today.getMonth(), 1)
  selDate.value  = new Date(today)
}
function selectDay(date) {
  selDate.value = new Date(date)
  selDate.value.setHours(0,0,0,0)
}

// ── Helpers ─────────────────────────────────────────────────────
function sameDay(a, b) {
  return a.getFullYear() === b.getFullYear() &&
         a.getMonth()    === b.getMonth()    &&
         a.getDate()     === b.getDate()
}
function getWeekForDay(d) {
  const ts = d.getTime()
  return store.weeks.find(w =>
    w.dateFrom != null && w.dateTo != null && ts >= w.dateFrom && ts <= w.dateTo
  ) || null
}
function inWeekRange(d) { return !!getWeekForDay(d) }

// ── Calendar cells ───────────────────────────────────────────────
const calCells = computed(() => {
  const yr  = curMonth.value.getFullYear()
  const mo  = curMonth.value.getMonth()
  const firstWeekDay = new Date(yr, mo, 1).getDay()
  const daysInMonth  = new Date(yr, mo + 1, 0).getDate()
  const prevMonthEnd = new Date(yr, mo, 0).getDate()
  const cells = []

  // prev month tail
  for (let i = firstWeekDay - 1; i >= 0; i--) {
    const d = new Date(yr, mo - 1, prevMonthEnd - i); d.setHours(0,0,0,0)
    cells.push(makeCell(d, true))
  }
  // current month
  for (let i = 1; i <= daysInMonth; i++) {
    const d = new Date(yr, mo, i); d.setHours(0,0,0,0)
    cells.push(makeCell(d, false))
  }
  // next month fill
  const remainder = (firstWeekDay + daysInMonth) % 7
  for (let i = 1; i <= (remainder ? 7 - remainder : 0); i++) {
    const d = new Date(yr, mo + 1, i); d.setHours(0,0,0,0)
    cells.push(makeCell(d, true))
  }
  return cells
})

function makeCell(d, otherMonth) {
  const key   = store._dk(d)
  const meals = store.calendarMeals[key] || {}
  const all   = CATEGORIES.flatMap(c => (meals[c] || []).map(m => ({ ...m, cat: c })))
  const chips = all.slice(0, 2)
  return {
    key, date: d, otherMonth,
    isToday:    sameDay(d, today),
    isSelected: sameDay(d, selDate.value),
    inRange:    inWeekRange(d),
    chips,
    moreCount:  Math.max(0, all.length - 2),
  }
}

// ── Selected day ─────────────────────────────────────────────────
const selectedDateLabel = computed(() => {
  const d = selDate.value
  return `${d.getDate()} ${MONTHS_S[d.getMonth()]} ${d.getFullYear()}`
})
const selectedDayName = computed(() => {
  return DAYS_S[selDate.value.getDay()] + (sameDay(selDate.value, today) ? ' · Today' : '')
})
const selectedWeek = computed(() => getWeekForDay(selDate.value))
const dayMeals     = computed(() => store.getDayMeals(store._dk(selDate.value)))
const hasDayMeals  = computed(() => CATEGORIES.some(c => dayMeals.value[c]?.length > 0))

function removeMeal(cat, idx) {
  store.removeRecipeFromDay(store._dk(selDate.value), cat, idx)
}

// ── Agenda ───────────────────────────────────────────────────────
const agendaDays = computed(() => {
  const yr = curMonth.value.getFullYear()
  const mo = curMonth.value.getMonth()
  const dim = new Date(yr, mo + 1, 0).getDate()
  return Array.from({ length: dim }, (_, i) => {
    const d = new Date(yr, mo, i + 1); d.setHours(0,0,0,0)
    const key = store._dk(d)
    return {
      key, date: d,
      isToday:   sameDay(d, today),
      shortDay:  DAYS_S[d.getDay()],
      monthYear: `${MONTHS_S[mo]} ${yr}`,
      meals:     store.calendarMeals[key] || { breakfast:[], lunch:[], dinner:[], snacks:[] },
      week:      getWeekForDay(d),
    }
  })
})

// ── Recipe Picker ─────────────────────────────────────────────────
const pickerCat      = ref(null)
const pickerQuery    = ref('')
const pickerFilter   = ref('all')
const pickerPicked   = ref(new Set())
const pickerOriginal = ref(new Set())   // snapshot of what was on the day when picker opened
const searchEl       = ref(null)
const showLinkModal  = ref(false)

// "Link to week" helper — switches to Weeks tab via parent emit
function goSetDates(week) {
  showLinkModal.value = false
  // Emit so App.vue/HomeView can switch to weeks tab
  emit('go-weeks', week.id)
}

const pickerFilters = computed(() => [
  { key: 'all', label: 'All' },
  ...CATEGORIES.map(k => ({ key: k, label: `${CAT_META[k].emoji} ${CAT_META[k].label}` })),
])

const filteredRecipes = computed(() => {
  const q = pickerQuery.value.toLowerCase()
  return store.recipes.filter(r =>
    (pickerFilter.value === 'all' || r.category === pickerFilter.value) &&
    (!q || r.name.toLowerCase().includes(q))
  )
})

function openPicker(cat) {
  pickerCat.value    = cat
  pickerQuery.value  = ''
  pickerFilter.value = cat
  // Pre-populate with recipeIds already on this day/category
  const existing = (dayMeals.value[cat] || [])
    .map(i => i.recipeId)
    .filter(Boolean)
  pickerPicked.value   = new Set(existing)
  pickerOriginal.value = new Set(existing)   // snapshot to detect removals
  nextTick(() => searchEl.value?.focus())
}

function togglePick(id) {
  const s = new Set(pickerPicked.value)
  s.has(id) ? s.delete(id) : s.add(id)
  pickerPicked.value = s
}

function confirmPick() {
  const dateStr = store._dk(selDate.value)
  const cat     = pickerCat.value
  const orig    = pickerOriginal.value
  const now     = pickerPicked.value
  const meals   = store.getDayMeals(dateStr)

  // Remove recipes that were originally there but are now deselected
  orig.forEach(id => {
    if (!now.has(id)) {
      const idx = (meals[cat] || []).findIndex(i => i.recipeId === id)
      if (idx !== -1) store.removeRecipeFromDay(dateStr, cat, idx)
    }
  })

  // Add recipes that are newly selected (not in original)
  now.forEach(id => {
    if (!orig.has(id)) {
      const r = store.recipes.find(x => x.id === id)
      if (r) store.addRecipeToDay(dateStr, cat, r)
    }
  })

  pickerCat.value = null
}

const catAddBg = { breakfast:'#ff9800', lunch:'#4caf50', dinner:'#5c6bc0', snacks:'#e91e8c' }

// How many recipes will be added vs removed vs original
const pickerAddCount    = computed(() => [...pickerPicked.value].filter(id => !pickerOriginal.value.has(id)).length)
const pickerRemoveCount = computed(() => [...pickerOriginal.value].filter(id => !pickerPicked.value.has(id)).length)
</script>

<style scoped>
.cal-view { animation: fadeUp 0.22s var(--ease) both; }
@keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }

/* ── Toolbar ── */
.cal-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.cal-month-nav { display: flex; align-items: center; gap: 10px; }
.cal-month-title {
  font-family: var(--font-display); font-size: 20px; font-weight: 700;
  color: var(--charcoal); min-width: 190px; text-align: center;
}
.icon-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1.5px solid var(--parchment); background: var(--warm-white);
  cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s var(--ease); color: var(--brown-mid); font-family: var(--font-body);
}
.icon-btn:hover { background: var(--parchment); }
.cal-toolbar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.today-btn {
  padding: 7px 14px; border-radius: var(--radius-md);
  border: 1.5px solid var(--parchment); background: var(--warm-white);
  font-size: 12.5px; font-weight: 600; color: var(--brown-mid); cursor: pointer;
  font-family: var(--font-body); transition: all 0.15s var(--ease);
}
.today-btn:hover { background: var(--terracotta-bg); color: var(--terracotta); border-color: var(--terracotta); }
.view-toggle {
  display: flex; background: var(--cream);
  border: 1.5px solid var(--parchment); border-radius: var(--radius-md);
  padding: 3px; gap: 3px;
}
.toggle-btn {
  padding: 5px 12px; border-radius: 8px; border: none;
  font-size: 12px; font-weight: 600; cursor: pointer;
  background: transparent; color: var(--brown-lt); font-family: var(--font-body);
  transition: all 0.15s var(--ease);
}
.toggle-btn.active { background: var(--warm-white); color: var(--terracotta); box-shadow: 0 1px 4px var(--shadow); }
.toggle-btn:hover:not(.active) { color: var(--brown-mid); }

/* ── Month grid layout ── */
.cal-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 18px;
  align-items: start;
}
@media (max-width: 860px) {
  .cal-layout {
    grid-template-columns: 1fr;
  }
  /* On mobile, stack the day detail panel below the calendar instead of hiding it */
  .day-detail-panel {
    position: static;
    margin-top: 14px;
  }
}

.cal-grid-wrap {
  background: var(--warm-white); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg); overflow: hidden; box-shadow: 0 2px 14px var(--shadow-sm);
}
.cal-weekdays { display: grid; grid-template-columns: repeat(7,1fr); background: var(--cream); border-bottom: 1.5px solid var(--parchment); }
.cal-weekday { padding: 9px 4px; text-align: center; font-size: 10.5px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--brown-lt); }
.cal-days { display: grid; grid-template-columns: repeat(7,1fr); }
.cal-cell {
  min-height: 82px; border-right: 1px solid var(--parchment); border-bottom: 1px solid var(--parchment);
  padding: 5px; cursor: pointer; transition: background 0.13s var(--ease); position: relative; overflow: hidden;
}
.cal-cell:nth-child(7n) { border-right: none; }
.cal-cell:hover { background: var(--terracotta-bg); }
.cal-cell.other-month { opacity: 0.35; pointer-events: none; }
.cal-cell.is-today { background: #fff3ee; }
.cal-cell.is-selected { background: #fde8df; box-shadow: inset 0 0 0 2px var(--terracotta); }
.cal-cell.in-week-range { background: #fffcf0; }
.cal-cell.in-week-range.is-selected { background: #fde8df; }
.cell-date-num {
  font-size: 12px; font-weight: 600; color: var(--brown-mid);
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; margin-bottom: 2px;
}
.is-today .cell-date-num { background: var(--terracotta); color: #fff; }
.cell-chips { display: flex; flex-direction: column; gap: 1px; }
.cell-chip { font-size: 9.5px; font-weight: 500; padding: 1px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.4; }
.cell-chip.breakfast { background: #fff3e0; color: #b84e00; }
.cell-chip.lunch     { background: #e8f5e9; color: #2a6e30; }
.cell-chip.dinner    { background: #e8eaf6; color: #283593; }
.cell-chip.snacks    { background: #fce4ec; color: #880e4f; }
.cell-more { font-size: 9px; color: var(--brown-lt); padding: 0 2px; }
.week-range-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 2.5px; background: var(--mustard); opacity: 0.5; }

/* Legend */
.cal-legend { display: flex; gap: 16px; margin-top: 10px; padding: 0 2px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 10.5px; color: var(--brown-lt); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--terracotta); }
.legend-bar { width: 14px; height: 4px; border-radius: 2px; background: var(--mustard); opacity: 0.6; }
.legend-box { width: 10px; height: 10px; border-radius: 2px; background: #fde8df; border: 1.5px solid var(--terracotta); }

/* ── Day Detail Panel ── */
.day-detail-panel {
  background: var(--warm-white); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-lg); overflow: hidden;
  box-shadow: 0 2px 14px var(--shadow-sm); position: sticky; top: 86px;
}
.ddp-head {
  padding: 16px 18px 13px; background: var(--cream);
  border-bottom: 1.5px solid var(--parchment);
  display: flex; flex-direction: column; gap: 4px;
}
.ddp-date { font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--charcoal); line-height: 1.1; }
.ddp-dayname { font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--brown-lt); }
.ddp-week-pill {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--mustard-bg, #fff8e1); color: var(--mustard, #c4880a);
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; margin-top: 5px;
  cursor: pointer; border: none; font-family: var(--font-body); transition: opacity 0.15s; width: fit-content;
}
.ddp-week-pill:hover { opacity: 0.75; }
.ddp-week-pill.unlinked { background: var(--cream); color: var(--brown-lt); border: 1.5px dashed var(--parchment-dark); cursor: default; }
.ddp-body { padding: 10px; display: flex; flex-direction: column; gap: 7px; }

.sync-note {
  background: var(--mustard-bg, #fff8e1); border: 1.5px solid var(--mustard-lt, #f5c842);
  border-radius: var(--radius-sm); padding: 7px 11px; font-size: 11.5px; color: var(--mustard, #c4880a);
  display: flex; align-items: flex-start; gap: 7px;
}

/* Meal slots */
.meal-slot { border: 1.5px solid var(--parchment); border-radius: var(--radius-md); overflow: hidden; }
.slot-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; cursor: pointer; transition: filter 0.12s;
}
.slot-head:hover { filter: brightness(0.97); }
.slot-head.breakfast { background: #fff3e0; } .slot-head.lunch { background: #e8f5e9; }
.slot-head.dinner    { background: #e8eaf6; } .slot-head.snacks { background: #fce4ec; }
.slot-label { display: flex; align-items: center; gap: 7px; font-size: 11.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.slot-label.breakfast { color: #b84e00; } .slot-label.lunch  { color: #2a6e30; }
.slot-label.dinner    { color: #283593; } .slot-label.snacks { color: #880e4f; }
.slot-count { font-size: 9.5px; font-weight: 700; min-width: 16px; height: 16px; border-radius: 8px; padding: 0 4px; display: flex; align-items: center; justify-content: center; }
.slot-count.breakfast { background:#ffe0b2;color:#b84e00; } .slot-count.lunch { background:#c8e6c9;color:#2a6e30; }
.slot-count.dinner    { background:#c5cae9;color:#283593; } .slot-count.snacks { background:#f8bbd9;color:#880e4f; }
.slot-add-btn {
  width: 22px; height: 22px; border-radius: 50%; border: none;
  font-size: 17px; font-weight: 300; line-height: 1; cursor: pointer;
  display: flex; align-items: center; justify-content: center; color: #fff;
  transition: transform 0.18s var(--ease);
}
.slot-add-btn:hover { transform: scale(1.18) rotate(90deg); }
.slot-items { background: var(--warm-white); padding: 5px 8px 7px; display: flex; flex-direction: column; gap: 3px; }
.slot-item {
  display: flex; align-items: center; gap: 8px; padding: 4px 6px;
  border-radius: var(--radius-sm); background: var(--cream); font-size: 12.5px; font-weight: 500;
  transition: background 0.12s;
}
.slot-item:hover { background: var(--parchment); }
.slot-item-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.slot-remove-btn {
  width: 16px; height: 16px; border-radius: 50%; border: none;
  background: transparent; color: var(--brown-lt); cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.12s, background 0.12s;
}
.slot-item:hover .slot-remove-btn { opacity: 1; }
.slot-remove-btn:hover { background: #fee; color: #c0392b; }
.slot-empty { background: var(--warm-white); padding: 6px 12px 8px; font-size: 11.5px; color: var(--parchment-dark); font-style: italic; }

/* ── Agenda view ── */
.agenda-list { display: flex; flex-direction: column; gap: 12px; }
.agenda-day { background: var(--warm-white); border: 1.5px solid var(--parchment); border-radius: var(--radius-lg); overflow: hidden; box-shadow: 0 2px 10px var(--shadow-sm); animation: fadeUp 0.2s var(--ease) both; }
.agenda-day.is-today { border-color: rgba(193,68,14,0.3); }
.agenda-day-head { display: flex; align-items: center; gap: 14px; padding: 13px 18px; background: var(--cream); border-bottom: 1.5px solid var(--parchment); }
.agenda-day-num { font-family: var(--font-display); font-size: 26px; font-weight: 700; color: var(--charcoal); line-height: 1; min-width: 32px; }
.agenda-day.is-today .agenda-day-num { color: var(--terracotta); }
.agenda-day-meta { flex: 1; }
.agenda-day-name { font-size: 13.5px; font-weight: 600; color: var(--charcoal); }
.agenda-day.is-today .agenda-day-name { color: var(--terracotta); }
.agenda-day-sub { font-size: 11px; color: var(--brown-lt); margin-top: 1px; }
.agenda-chips { display: flex; gap: 4px; flex-wrap: wrap; }
.agenda-chip { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 500; }
.agenda-chip.breakfast { background:#fff3e0;color:#b84e00; } .agenda-chip.lunch { background:#e8f5e9;color:#2a6e30; }
.agenda-chip.dinner    { background:#e8eaf6;color:#283593; } .agenda-chip.snacks { background:#fce4ec;color:#880e4f; }
.agenda-body { padding: 10px 14px; display: flex; flex-direction: column; gap: 5px; }
.agenda-slot { display: flex; gap: 10px; align-items: flex-start; padding: 7px 0; border-bottom: 1px solid var(--parchment); }
.agenda-slot:last-child { border-bottom: none; }
.agenda-slot-icon { font-size: 15px; margin-top: 1px; flex-shrink: 0; }
.agenda-slot-content { flex: 1; }
.agenda-slot-lbl { font-size: 10px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--brown-lt); margin-bottom: 3px; }
.agenda-slot-item { display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 500; color: var(--charcoal); }
.agenda-slot-none { font-size: 12px; color: var(--parchment-dark); font-style: italic; }
.agenda-slot-add {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
  border: 1.5px dashed var(--parchment-dark); background: transparent;
  color: var(--brown-lt); cursor: pointer; font-size: 17px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s var(--ease); margin-top: 1px;
}
.agenda-slot-add:hover { border-color: var(--terracotta); color: var(--terracotta); background: var(--terracotta-bg); transform: scale(1.12); }

/* ── Picker modal ── */
.picker-box { max-width: 500px; }
.modal-head { padding: 18px 22px 12px; border-bottom: 1.5px solid var(--parchment); flex-shrink: 0; }
.modal-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; color: var(--charcoal); }
.modal-sub { font-size: 12.5px; color: var(--brown-lt); margin-top: 3px; }
.picker-search-wrap { padding: 10px 18px; border-bottom: 1px solid var(--parchment); flex-shrink: 0; }
.picker-search {
  width: 100%; background: var(--cream); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md); padding: 8px 12px;
  font-family: var(--font-body); font-size: 13.5px; color: var(--charcoal); outline: none;
}
.picker-search:focus { border-color: var(--terracotta); box-shadow: 0 0 0 3px rgba(193,68,14,0.1); }
.picker-filters { display: flex; gap: 5px; padding: 8px 18px; border-bottom: 1px solid var(--parchment); overflow-x: auto; flex-shrink: 0; }
.pk-filter {
  padding: 4px 12px; border-radius: 20px; border: 1.5px solid var(--parchment);
  background: transparent; font-size: 11.5px; font-weight: 600; cursor: pointer;
  white-space: nowrap; font-family: var(--font-body); color: var(--brown-lt); transition: all 0.14s;
}
.pk-filter.active { border-color: var(--terracotta); background: var(--terracotta-bg); color: var(--terracotta); }
.pk-filter:hover:not(.active) { background: var(--cream); }
.picker-list { overflow-y: auto; flex: 1; padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; min-height: 200px; max-height: 350px; }
.picker-empty { padding: 28px; text-align: center; color: var(--brown-lt); font-style: italic; font-size: 13px; }
.recipe-pick-row {
  display: flex; align-items: center; gap: 12px; padding: 9px 11px;
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.13s;
  border: 1.5px solid transparent;
}
.recipe-pick-row:hover { background: var(--terracotta-bg); border-color: rgba(193,68,14,0.18); }
.recipe-pick-row.is-picked { background: var(--terracotta-bg); border-color: var(--terracotta); }
.rpr-emoji { font-size: 22px; flex-shrink: 0; }
.rpr-info { flex: 1; min-width: 0; }
.rpr-name { font-size: 13.5px; font-weight: 600; color: var(--charcoal); }
.rpr-ings { font-size: 11.5px; color: var(--brown-lt); }
.rpr-check {
  width: 21px; height: 21px; border-radius: 50%; border: 2px solid var(--parchment);
  display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; transition: all 0.14s;
}
.recipe-pick-row.is-picked .rpr-check { background: var(--terracotta); border-color: var(--terracotta); color: #fff; }
.modal-foot {
  padding: 12px 18px; border-top: 1.5px solid var(--parchment);
  display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
  background: var(--cream);
}
.picker-sel-info { font-size: 12px; color: var(--brown-lt); }
.picker-sel-info .adding   { color: var(--sage, #5e8c65); }
.picker-sel-info .removing { color: var(--terracotta); }

/* Shared modal transitions */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

/* ── Link Week Modal ── */
.modal-close-btn {
  position: absolute; top: 14px; right: 14px; width: 30px; height: 30px;
  border-radius: 50%; border: none; background: var(--cream); color: var(--brown-lt);
  font-size: 17px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.12s; z-index: 1;
}
.modal-close-btn:hover { background: var(--parchment); }

.link-week-body {
  padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto;
}
.link-week-list { display: flex; flex-direction: column; gap: 8px; }
.link-week-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 14px; background: var(--cream); border: 1.5px solid var(--parchment);
  border-radius: var(--radius-md);
}
.lwr-info { flex: 1; }
.lwr-label { font-size: 14px; font-weight: 600; color: var(--charcoal); }
.lwr-dates { font-size: 11.5px; color: var(--brown-lt); margin-top: 2px; }
.lwr-btn { font-size: 12px; padding: 5px 12px; white-space: nowrap; flex-shrink: 0; }
.lwr-mismatch { font-size: 11px; color: var(--parchment-dark); font-style: italic; flex-shrink: 0; }
.lwr-empty { font-size: 13px; color: var(--brown-lt); font-style: italic; padding: 8px 0; }
.lwr-hint {
  background: var(--mustard-bg, #fff8e1); border: 1.5px solid var(--mustard-lt, #f5c842);
  border-radius: var(--radius-md); padding: 10px 14px; font-size: 12.5px; color: var(--mustard, #c4880a); line-height: 1.5;
}
</style>
