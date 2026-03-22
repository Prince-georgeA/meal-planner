<template>
  <Transition name="toast">
    <div
      v-if="store.toast"
      class="toast"
      :class="`toast-${store.toast.type || 'success'}`"
      role="status"
      aria-live="polite"
    >
      <span class="toast-icon">
        {{ icons[store.toast.type || 'success'] }}
      </span>
      <span class="toast-msg">{{ store.toast.message }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { useMealStore } from '../stores/mealStore.js'

const store = useMealStore()

const icons = {
  success: '✓',
  info:    'ℹ',
  warning: '⚠',
  error:   '✕',
}
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 22px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  z-index: 500;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  pointer-events: none;
  max-width: calc(100vw - 40px);
}

.toast-success { background: var(--sage);      color: #fff; }
.toast-info    { background: var(--brown-mid); color: #fff; }
.toast-warning { background: var(--mustard);   color: #fff; }
.toast-error   { background: #c0392b;          color: #fff; }

.toast-icon {
  width: 22px; height: 22px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.toast-msg {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Transition ── */
.toast-enter-active {
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px) scale(0.9);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}
</style>
