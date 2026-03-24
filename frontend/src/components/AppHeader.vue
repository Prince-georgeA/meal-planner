<template>
  <header class="app-header">
    <div class="header-inner">

      <!-- Brand -->
      <button class="brand" @click="$emit('go-home')" aria-label="Go home">
        <span class="brand-icon">🥘</span>
        <span class="brand-name">Meal<em>Planner</em></span>
      </button>

      <!-- Breadcrumb when in week view -->
      <Transition name="crumb">
        <div v-if="inWeek && weekLabel" class="breadcrumb">
          <span class="crumb-sep">›</span>
          <span class="crumb-label">{{ weekLabel }}</span>
        </div>
      </Transition>

      <!-- Actions -->
      <div class="header-actions">
        <button class="btn-add-recipe" @click="$emit('add-recipe')" aria-label="Add recipe to library">
          <span class="btn-icon">＋</span>
          <span class="btn-text">Add Recipe</span>
        </button>
        <button class="btn-stores" @click="$emit('manage-stores')" aria-label="Manage stores">
          🏪 <span class="btn-text">Stores</span>
        </button>
        <button class="btn-settings" @click="$emit('open-settings')" title="Settings" aria-label="Settings">
          ⚙️
        </button>
      </div>

    </div>
  </header>
</template>

<script setup>
defineProps({
  inWeek:     { type: Boolean, default: false },
  weekLabel:  { type: String,  default: '' },
})

defineEmits(['add-recipe', 'go-home', 'manage-stores', 'open-settings'])
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--charcoal);
  box-shadow: 0 2px 20px rgba(44,36,22,0.3);
  /* Extend header behind iOS status bar — fills the transparent area */
  padding-top: env(safe-area-inset-top, 0px);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 68px;
  padding: 0 32px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ── Brand ── */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 0;
  text-decoration: none;
  flex-shrink: 0;
}

.brand-icon {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--terracotta), var(--mustard));
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--cream);
  letter-spacing: 0.01em;
}

.brand-name em {
  font-style: italic;
  color: var(--mustard-lt);
}

/* ── Breadcrumb ── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.crumb-sep {
  color: rgba(255,255,255,0.25);
  font-size: 18px;
}

.crumb-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255,255,255,0.6);
}

.crumb-enter-active, .crumb-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.crumb-enter-from { opacity: 0; transform: translateX(-8px); }
.crumb-leave-to   { opacity: 0; transform: translateX(8px); }

/* ── Spacer ── */
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Add Recipe Btn ── */
.btn-add-recipe {
  display: flex;
  align-items: center;
  gap: 7px;
  background: var(--terracotta);
  color: #fff;
  border: none;
  padding: 8px 18px;
  border-radius: 9px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.02em;
}

.btn-add-recipe:hover {
  background: var(--terracotta-lt);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(193,68,14,0.4);
}

/* ── Stores Btn ── */
.btn-stores {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.85);
  border: 1px solid rgba(255,255,255,0.2);
  padding: 8px 14px;
  border-radius: 9px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-stores:hover {
  background: rgba(255,255,255,0.18);
  color: white;
}

.btn-icon { font-size: 15px; }

.btn-settings {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px; height: 34px;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.7);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.btn-settings:hover {
  background: rgba(255,255,255,0.18);
  color: white;
}

@media (max-width: 500px) {
  .header-inner { padding: 0 16px; }
  .btn-text { display: none; }
  .btn-add-recipe { padding: 9px 12px; }
  .btn-stores { padding: 9px 10px; }
  .brand-name { font-size: 17px; }
}
</style>
