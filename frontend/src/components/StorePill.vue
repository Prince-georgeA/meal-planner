<template>
  <div class="store-pill-wrapper" ref="wrapperRef">
    <button
      class="store-pill"
      :style="pillStyle"
      @click.stop="toggleOpen"
      :title="store ? `Store: ${store.name} — tap to change` : 'Tap to tag a store'"
      type="button"
    >
      <span v-if="store">{{ store.emoji }} {{ store.name }}</span>
      <span v-else class="pill-untagged">＋ Tag store</span>
    </button>

    <!-- Teleported to body — escapes any parent overflow:hidden -->
    <Teleport to="body">
      <Transition name="pop">
        <div
          v-if="open"
          class="store-popover-fixed"
          :style="popoverStyle"
          @click.stop
          ref="popoverRef"
        >
          <p class="popover-label">Source Store</p>
          <div
            v-for="s in stores"
            :key="s.id"
            class="popover-option"
            :class="{ active: s.id === modelValue }"
            @click="select(s.id)"
          >
            <span class="option-dot" :style="{ background: s.color }" />
            {{ s.emoji }} {{ s.name }}
            <span v-if="s.id === modelValue" class="option-check">✓</span>
          </div>
          <div v-if="modelValue" class="popover-clear" @click="select(null)">
            ✕ Remove tag
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: null },
  stores:     { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue'])

const open       = ref(false)
const flipUp     = ref(false)
const wrapperRef = ref(null)
const popoverRef = ref(null)

const POPOVER_HEIGHT = 28 + 32 * (props.stores.length + 1) + 20

const store = computed(() => props.stores.find(s => s.id === props.modelValue) ?? null)

const pillStyle = computed(() => {
  if (!store.value) return {}
  return {
    background:  store.value.color + '22',
    color:       store.value.color,
    borderColor: store.value.color + '55',
  }
})

const popoverPos = ref({ top: 0, right: 0, openUp: false })

const popoverStyle = computed(() => {
  const { top, right, openUp } = popoverPos.value
  return {
    position: 'fixed',
    right:    `${right}px`,
    top:      openUp ? 'auto' : `${top}px`,
    bottom:   openUp ? `${window.innerHeight - top + 8}px` : 'auto',
    zIndex:   9999,
  }
})

function calcPosition() {
  if (!wrapperRef.value) return
  const rect        = wrapperRef.value.getBoundingClientRect()
  const spaceBelow  = window.innerHeight - rect.bottom
  const rightOffset = window.innerWidth  - rect.right
  popoverPos.value  = {
    top:    rect.bottom + 5,
    right:  Math.max(4, rightOffset),
    openUp: spaceBelow < POPOVER_HEIGHT + 12,
  }
}

function toggleOpen() {
  if (open.value) { open.value = false; return }
  calcPosition()
  open.value = true
}

function select(id) {
  emit('update:modelValue', id)
  open.value = false
}

function onOutsideClick(e) {
  const w = wrapperRef.value, p = popoverRef.value
  if (w && !w.contains(e.target) && p && !p.contains(e.target)) {
    open.value = false
  }
}

function onScrollOrResize() { if (open.value) calcPosition() }

onMounted(() => {
  document.addEventListener('mousedown', onOutsideClick)
  window.addEventListener('scroll',  onScrollOrResize, true)
  window.addEventListener('resize',  onScrollOrResize)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onOutsideClick)
  window.removeEventListener('scroll',  onScrollOrResize, true)
  window.removeEventListener('resize',  onScrollOrResize)
})
</script>

<style scoped>
.store-pill-wrapper { position: relative; display: inline-flex; flex-shrink: 0; }

.store-pill {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 9px; border-radius: 20px;
  border: 1.5px solid var(--parchment-dark, #d9c9ae);
  background: var(--parchment, #ede0cc);
  color: var(--brown-lt, #a07850);
  font-family: var(--font-body, 'DM Sans', sans-serif);
  font-size: 11px; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: all 0.15s;
  user-select: none; line-height: 1; min-height: 22px;
}
.store-pill:hover { filter: brightness(0.93); transform: translateY(-1px); }
.pill-untagged { opacity: 0.65; font-weight: 500; }
</style>

<style>
.store-popover-fixed {
  background: var(--warm-white, #fff9f2);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(44,36,22,0.22);
  padding: 8px; min-width: 172px;
}
.store-popover-fixed .popover-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--brown-lt, #a07850);
  padding: 2px 6px 7px;
}
.store-popover-fixed .popover-option {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 8px; border-radius: 7px; font-size: 13px;
  cursor: pointer; transition: background 0.12s;
  font-family: var(--font-body, 'DM Sans', sans-serif);
}
.store-popover-fixed .popover-option:hover  { background: var(--parchment, #ede0cc); }
.store-popover-fixed .popover-option.active { font-weight: 700; background: var(--cream, #faf6ef); }
.store-popover-fixed .option-dot {
  width: 9px; height: 9px; border-radius: 50%;
  flex-shrink: 0; display: inline-block;
}
.store-popover-fixed .option-check {
  margin-left: auto; font-size: 11px; color: var(--sage, #6b8f71); font-weight: 700;
}
.store-popover-fixed .popover-clear {
  display: flex; align-items: center; gap: 7px; padding: 6px 8px;
  border-radius: 7px; font-size: 12px; color: var(--brown-lt, #a07850);
  font-style: italic; cursor: pointer; margin-top: 3px;
  border-top: 1px solid var(--parchment, #ede0cc);
  transition: background 0.12s;
  font-family: var(--font-body, 'DM Sans', sans-serif);
}
.store-popover-fixed .popover-clear:hover { background: var(--parchment, #ede0cc); }
.pop-enter-active, .pop-leave-active { transition: opacity 0.13s ease, transform 0.13s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px) scale(0.97); }
</style>
