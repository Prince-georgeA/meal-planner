<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">
      <h2 class="modal-title">🏪 Manage Stores</h2>
      <p class="modal-sub">Your go-to shopping spots. Tag ingredients to each store.</p>

      <!-- Existing stores list -->
      <div class="stores-list">
        <div v-for="s in store.stores" :key="s.id" class="store-row">
          <span class="store-swatch" :style="{ background: s.color }" />
          <span class="store-emoji">{{ s.emoji }}</span>
          <span class="store-name">{{ s.name }}</span>
          <span class="store-usage">
            {{ store.storeUsageCount(s.id) }} ingredient{{ store.storeUsageCount(s.id) !== 1 ? 's' : '' }} tagged
          </span>
          <button
            class="btn-edit-store"
            @click="startEdit(s)"
            title="Edit store"
          >✎</button>
          <button
            class="btn-del-store"
            @click="handleDeleteClick(s)"
            :title="store.storeUsageCount(s.id) === 0 ? 'Delete store' : 'Reassign & delete store'"
          >✕</button>
        </div>
      </div>

      <!-- Add new store -->
      <div class="add-store-box">
        <p class="form-label">Add New Store</p>
        <div class="add-store-row">
          <div class="add-field add-emoji">
            <p class="field-sub">Emoji</p>
            <input class="form-input" v-model="newEmoji" maxlength="4" />
          </div>
          <div class="add-field add-name">
            <p class="field-sub">Name</p>
            <input class="form-input" v-model="newName" placeholder="e.g. IGA" @keydown.enter="handleAdd" />
          </div>
          <div class="add-field add-color">
            <p class="field-sub">Colour</p>
            <input type="color" class="color-input" v-model="newColor" />
          </div>
          <button class="btn btn-primary add-btn" @click="handleAdd">＋ Add</button>
        </div>
      </div>

      <!-- Edit store -->
      <div v-if="editingStore" class="edit-store-box">
        <p class="form-label">Edit Store</p>
        <div class="add-store-row edit-store-row">
          <div class="add-field add-emoji">
            <p class="field-sub">Emoji</p>
            <input class="form-input" v-model="editEmoji" maxlength="4" />
          </div>
          <div class="add-field add-name">
            <p class="field-sub">Name</p>
            <input class="form-input" v-model="editName" @keydown.enter="saveEdit" />
          </div>
          <div class="add-field add-color">
            <p class="field-sub">Colour</p>
            <input type="color" class="color-input" v-model="editColor" />
          </div>
          <div class="edit-actions">
            <button class="btn btn-primary add-btn" @click="saveEdit">Save</button>
            <button class="btn btn-secondary add-btn" @click="cancelEdit">Cancel</button>
          </div>
        </div>
      </div>

      <!-- Reassign & delete dialog -->
      <div v-if="storeToDelete" class="reassign-box">
        <p class="form-label">Reassign &amp; Delete Store</p>
        <p class="reassign-text">
          <span class="reassign-name">"{{ storeToDelete.name }}"</span>
          is currently tagged on
          {{ store.storeUsageCount(storeToDelete.id) }} ingredient{{ store.storeUsageCount(storeToDelete.id) === 1 ? '' : 's' }}.
          Choose another store to move those tags to, then delete.
        </p>
        <div v-if="otherStores.length">
          <select class="form-select" v-model="reassignToId">
            <option v-for="s in otherStores" :key="s.id" :value="s.id">
              {{ s.emoji }} {{ s.name }}
            </option>
          </select>
          <div class="reassign-actions">
            <button class="btn btn-secondary" @click="cancelReassign">Cancel</button>
            <button
              class="btn btn-danger"
              @click="confirmReassign"
              :disabled="!reassignToId"
            >
              Reassign & Delete
            </button>
          </div>
        </div>
        <div v-else class="reassign-empty">
          You need at least one other store to reassign to before deleting this one.
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn btn-primary" @click="$emit('close')">Done</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMealStore } from '../stores/mealStore.js'

defineEmits(['close'])

const store    = useMealStore()
const newName  = ref('')
const newEmoji = ref('🏬')
const newColor = ref('#888888')

const editingStore = ref(null)
const editName     = ref('')
const editEmoji    = ref('🏬')
const editColor    = ref('#888888')

const storeToDelete = ref(null)
const reassignToId  = ref(null)

const otherStores = computed(() => {
  if (!storeToDelete.value) return []
  return store.stores.filter(s => s.id !== storeToDelete.value.id)
})

function handleAdd() {
  if (!newName.value.trim()) return
  store.addStore({ name: newName.value, emoji: newEmoji.value, color: newColor.value })
  newName.value  = ''
  newEmoji.value = '🏬'
  newColor.value = '#888888'
}

function startEdit(s) {
  // Only show one panel at a time
  storeToDelete.value = null
  reassignToId.value  = null
  editingStore.value = s
  editName.value  = s.name
  editEmoji.value = s.emoji
  editColor.value = s.color
}

function cancelEdit() {
  editingStore.value = null
}

function saveEdit() {
  if (!editingStore.value) return
  if (!editName.value.trim()) return
  store.updateStore(editingStore.value.id, {
    name:  editName.value,
    emoji: editEmoji.value,
    color: editColor.value,
  })
  editingStore.value = null
}

function handleDeleteClick(s) {
  // Only show one panel at a time
  editingStore.value = null
  const usage = store.storeUsageCount(s.id)
  if (usage === 0) {
    store.deleteStore(s.id)
    return
  }
  storeToDelete.value = s
  reassignToId.value = otherStores.value[0]?.id || null
}

function cancelReassign() {
  storeToDelete.value = null
  reassignToId.value  = null
}

function confirmReassign() {
  if (!storeToDelete.value || !reassignToId.value) return
  store.reassignStore(storeToDelete.value.id, reassignToId.value)
  store.deleteStore(storeToDelete.value.id)
  storeToDelete.value = null
  reassignToId.value  = null
}
</script>

<style scoped>
/* Overlay + box — reuse global modal styles from style.css */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44,36,22,0.48);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
  backdrop-filter: blur(4px);
}

.modal-box {
  background: var(--warm-white);
  border-radius: 20px;
  padding: 32px;
  width: 480px;
  max-width: 92vw;
  max-height: 88vh;
  overflow-y: auto;
  box-shadow: 0 24px 60px rgba(44,36,22,0.28);
  animation: slideUp 0.2s ease;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--charcoal);
  margin-bottom: 4px;
}

.modal-sub {
  font-size: 13px;
  color: var(--brown-lt);
  margin-bottom: 20px;
}

/* Stores list */
.stores-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.store-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: 10px;
}

.store-swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.store-emoji { font-size: 15px; }

.store-name {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
  color: var(--charcoal);
}

.store-usage {
  font-size: 11px;
  color: var(--brown-lt);
  flex-shrink: 0;
}

.btn-edit-store {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--brown-lt);
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.btn-edit-store:hover { background: var(--parchment); color: var(--charcoal); }

.btn-del-store {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--parchment-dark);
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.btn-del-store:hover { background: #fee; color: #c0392b; }

/* Add new store */
.add-store-box {
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
}

.add-store-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-top: 10px;
}

.add-field { display: flex; flex-direction: column; gap: 4px; }
.add-emoji { width: 60px; }
.add-name  { flex: 1; }
.add-color { width: 46px; }

.field-sub {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--brown-lt);
}

.color-input {
  width: 100%;
  height: 40px;
  border: 1.5px solid var(--parchment);
  border-radius: 8px;
  cursor: pointer;
  padding: 3px;
  background: var(--warm-white);
}

.add-btn {
  white-space: nowrap;
  flex-shrink: 0;
  padding: 10px 14px;
  font-size: 13px;
}

/* Edit store panel */
.edit-store-box {
  background: var(--warm-white);
  border: 1.5px solid var(--parchment);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
}

.edit-actions {
  display: flex;
  gap: 10px;
}

/* Mobile: ensure emoji/text visible, move Save/Cancel to next line */
@media (max-width: 520px) {
  .store-row { gap: 8px; }
  .store-name { font-size: 13.5px; }
  .store-usage { display: none; } /* keep rows readable on narrow screens */

  .edit-store-row {
    flex-wrap: wrap;
    gap: 10px;
    align-items: flex-start;
  }
  .edit-store-row .add-emoji { width: 76px; }
  .edit-store-row .add-color { width: 70px; }
  .edit-store-row .add-name  { flex: 1; min-width: 150px; }

  .edit-actions {
    width: 100%;
    flex-basis: 100%;
    justify-content: flex-end;
    margin-top: 2px;
  }
}

/* Reassign & delete section */
.reassign-box {
  background: var(--cream);
  border: 1.5px solid var(--parchment);
  border-radius: 12px;
  padding: 14px 16px 16px;
  margin-bottom: 20px;
}

.reassign-text {
  font-size: 13px;
  color: var(--brown-mid);
  line-height: 1.5;
  margin: 6px 0 12px;
}

.reassign-name {
  font-weight: 600;
  color: var(--charcoal);
}

.reassign-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.reassign-empty {
  font-size: 12px;
  color: var(--brown-lt);
  font-style: italic;
  margin-top: 6px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
</style>
