<template>
  <div class="app-shell" :class="{ 'modal-open': hasOpenModal }">
    <!-- Background atmosphere -->
    <div class="bg-atmosphere" aria-hidden="true">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <!-- ── Connect screen (shown until Supabase is connected) ── -->
    <ConnectView v-if="!isConnected" @connected="onConnected" />

    <!-- ── Main app ── -->
    <template v-else>
      <!-- Sync status bar -->
      <Transition name="sync-bar">
        <div v-if="store.syncStatus === 'saving'" class="sync-bar sync-saving">⏳ Syncing…</div>
        <div v-else-if="store.syncStatus === 'saved'" class="sync-bar sync-saved">✓ Saved</div>
        <div v-else-if="store.syncStatus === 'offline'" class="sync-bar sync-offline">⚠ Offline — changes may not be saved</div>
      </Transition>

      <!-- Header -->
      <AppHeader
        @add-recipe="showAddRecipe = true"
        @go-home="goHome"
        @manage-stores="showStores = true"
        :in-week="currentView === 'week'"
        :week-label="activeWeek?.label"
        @disconnect="handleDisconnect"
        @open-settings="showSettings = true" 
      />

      <!-- Views -->
      <main class="main-content">
        <Transition name="view" mode="out-in">
          <HomeView
            v-if="currentView === 'home'"
            key="home"
            @open-week="openWeek"
            @add-recipe="showAddRecipe = true"
          />
          <WeekDetailView
            v-else-if="currentView === 'week' && activeWeek"
            key="week"
            :week="activeWeek"
            @back="goHome"
            @add-food="handleAddFoodRequest"
          />
        </Transition>
      </main>

      <!-- Modals -->
      <Teleport to="body">
        <AddRecipeModal v-if="showAddRecipe" @close="showAddRecipe = false" />
        <AddFoodModal
          v-if="addFoodContext"
          :week-id="addFoodContext.weekId"
          :category="addFoodContext.category"
          @close="addFoodContext = null"
        />
        <StoresModal v-if="showStores" @close="showStores = false" />
      <SettingsPanel
        :open="showSettings"
        @close="showSettings = false"
        @disconnected="handleDisconnect"
      />
        <ToastNotification />
      </Teleport>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMealStore } from './stores/mealStore.js'
import {
  loadStoredCredentials, initClient, clearClient, clearCredentials,
  parseShareLink,
} from './lib/supabase.js'
import ConnectView      from './components/ConnectView.vue'
import AppHeader        from './components/AppHeader.vue'
import HomeView         from './components/HomeView.vue'
import WeekDetailView   from './components/WeekDetailView.vue'
import AddRecipeModal   from './components/AddRecipeModal.vue'
import AddFoodModal     from './components/AddFoodModal.vue'
import StoresModal      from './components/StoresModal.vue'
import ToastNotification from './components/ToastNotification.vue'

const store = useMealStore()

const isConnected   = ref(false)
const currentView   = ref('home')
const activeWeekId  = ref(null)
const showAddRecipe = ref(false)
const showStores    = ref(false)
const showSettings  = ref(false)
const addFoodContext = ref(null)

const activeWeek = computed(() =>
  store.weeks.find(w => w.id === activeWeekId.value) || null
)
const hasOpenModal = computed(() =>
  showAddRecipe.value || !!addFoodContext.value || showStores.value || showSettings.value
)

onMounted(async () => {
  // Check for share link in hash first (takes priority over stored creds)
  const shareData = parseShareLink(window.location.hash)
  if (shareData) {
    // Don't auto-connect from share link — let ConnectView handle it
    // (it will pre-fill and the user confirms)
    isConnected.value = false
    return
  }

  // Try to auto-connect from stored credentials
  const { url, key } = loadStoredCredentials()
  if (url && key) {
    initClient(url, key)
    isConnected.value = true
    await store.initFromServer()
  }
})

async function onConnected() {
  isConnected.value = true
  await store.initFromServer()
}

function handleDisconnect() {
  clearCredentials()
  clearClient()
  isConnected.value = false
  // Reset store state
  store.recipes.length = 0
  store.weeks.length   = 0
}

function openWeek(weekId) {
  activeWeekId.value = weekId
  currentView.value  = 'week'
  store.checkAutoClear(weekId)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goHome() {
  currentView.value = 'home'
  activeWeekId.value = null
}

function handleAddFoodRequest({ weekId, category }) {
  addFoodContext.value = { weekId, category }
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* ── Background ── */
.bg-atmosphere {
  position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.bg-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.5; }
.bg-orb-1 { width:600px;height:600px; top:-200px;left:-100px; background:radial-gradient(circle,rgba(193,68,14,.07),transparent 70%); }
.bg-orb-2 { width:500px;height:500px; bottom:-150px;right:-80px; background:radial-gradient(circle,rgba(94,140,101,.08),transparent 70%); }
.bg-orb-3 { width:400px;height:400px; top:50%;left:50%; transform:translate(-50%,-50%); background:radial-gradient(circle,rgba(196,136,10,.05),transparent 70%); }

/* ── Main ── */
.main-content { position:relative; z-index:1; min-height:calc(100vh - 68px); }

/* ── Sync bar ── */
.sync-bar {
  position:fixed; top:68px; left:50%; transform:translateX(-50%);
  z-index:200; padding:5px 18px; border-radius:0 0 10px 10px;
  font-size:12px; font-weight:500; white-space:nowrap;
  pointer-events:none; box-shadow:0 3px 10px rgba(0,0,0,.1);
}
.sync-saving  { background:#fff8e1;color:#b7860b;border:1px solid #ffe082;border-top:none; }
.sync-saved   { background:#e8f5e9;color:#2e7d32;border:1px solid #a5d6a7;border-top:none; }
.sync-offline { background:#fff3e0;color:#e65100;border:1px solid #ffcc80;border-top:none; }
.sync-bar-enter-active,.sync-bar-leave-active { transition:opacity .25s,transform .25s; }
.sync-bar-enter-from,.sync-bar-leave-to { opacity:0;transform:translateX(-50%) translateY(-6px); }

/* ── View transitions ── */
.view-enter-active,.view-leave-active { transition:opacity .25s ease,transform .25s ease; }
.view-enter-from { opacity:0;transform:translateX(12px); }
.view-leave-to   { opacity:0;transform:translateX(-12px); }

/* ── Modal scroll-lock ── */
.modal-open { overflow:hidden; }
</style>
