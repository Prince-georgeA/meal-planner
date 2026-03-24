<template>
  <Teleport to="body">
    <Transition name="panel">
      <div v-if="open" class="settings-overlay" @click.self="$emit('close')">
        <div class="settings-drawer">

          <!-- Header -->
          <div class="drawer-head">
            <span class="drawer-title">⚙️ Settings</span>
            <button class="drawer-close" @click="$emit('close')">✕</button>
          </div>

          <!-- ── Section: Database ── -->
          <div class="section">
            <p class="section-label">Database</p>

            <div class="setting-row">
              <div class="setting-info">
                <span class="setting-name">Connected DB</span>
                <span class="setting-val">{{ shortUrl }}</span>
              </div>
              <span class="status-dot connected" title="Connected" />
            </div>

            <button class="danger-btn" @click="confirmDisconnect = true">
              🔌 Disconnect Database
            </button>

            <!-- Confirm disconnect -->
            <div v-if="confirmDisconnect" class="confirm-box">
              <p class="confirm-text">
                This will sign you out on this device. Your data stays safe in Supabase.
              </p>
              <div class="confirm-actions">
                <button class="btn-cancel" @click="confirmDisconnect = false">Cancel</button>
                <button class="btn-confirm-danger" @click="doDisconnect">Yes, disconnect</button>
              </div>
            </div>
          </div>

          <!-- ── Section: Bulk Import API ── -->
          <div class="section">
            <p class="section-label">Bulk Recipe Import</p>
            <p class="section-desc">
              Pre-load recipes into your Supabase DB from the API docs page.
            </p>

            <div class="copy-row">
              <span class="copy-label">API Docs URL</span>
              <div class="copy-field">
                <span class="copy-value">{{ apiDocsUrl }}</span>
                <button class="copy-btn" @click="copy(apiDocsUrl, 'api')">
                  {{ copied === 'api' ? '✓' : '📋' }}
                </button>
              </div>
            </div>

            <a :href="apiDocsUrl" target="_blank" rel="noopener" class="open-link">
              Open API Docs ↗
            </a>
          </div>

          <!-- ── Section: Share / Connect Another Device ── -->
          <div class="section">
            <p class="section-label">Connect Another Device</p>
            <p class="section-desc">
              Scan or share this link to connect your Supabase DB on another device instantly.
            </p>

            <!-- Security note -->
            <div class="security-note">
              ⚠ <strong>Keep this private.</strong> The link contains your Supabase anon key.
              The anon key is designed for client-side use and is not a secret password —
              but anyone with it can read and write your meal plans.
              Share only with your own devices via a private channel.
            </div>

            <!-- Share link -->
            <div class="copy-row" style="margin-top: 12px;">
              <span class="copy-label">Share Link</span>
              <div class="copy-field">
                <span class="copy-value">{{ shareLink }}</span>
                <button class="copy-btn" @click="copy(shareLink, 'link')">
                  {{ copied === 'link' ? '✓' : '📋' }}
                </button>
              </div>
            </div>

            <!-- QR Code -->
            <div class="qr-section">
              <p class="qr-label">Scan with your phone:</p>
              <div v-if="qrDataUrl" class="qr-wrap">
                <img :src="qrDataUrl" alt="QR code for DB connection" class="qr-img" />
              </div>
              <div v-else class="qr-placeholder">Generating QR…</div>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { loadStoredCredentials, buildShareLink, clearCredentials, clearClient } from '../lib/supabase.js'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit  = defineEmits(['close', 'disconnected'])

const confirmDisconnect = ref(false)
const copied            = ref('')
const qrDataUrl         = ref('')

const creds = computed(() => loadStoredCredentials())

const shortUrl = computed(() => {
  try { return new URL(creds.value.url).hostname } catch { return creds.value.url || '—' }
})

// API docs URL — same origin /api/docs
const apiDocsUrl = computed(() => `${window.location.origin}/api/docs`)

// Share link using the supabase.js helper
const shareLink = computed(() => {
  if (!creds.value.url || !creds.value.key) return ''
  return buildShareLink(creds.value.url, creds.value.key)
})

// Generate QR when panel opens
watch(() => props.open, async (isOpen) => {
  if (!isOpen || qrDataUrl.value) return
  try {
    const QRCode = (await import('qrcode')).default
    qrDataUrl.value = await QRCode.toDataURL(shareLink.value, {
      width: 180,
      margin: 2,
      color: { dark: '#2c2416', light: '#fff9f2' },
    })
  } catch { qrDataUrl.value = '' }
})

async function copy(text, key) {
  if (!text) return
  await navigator.clipboard.writeText(text)
  copied.value = key
  setTimeout(() => { copied.value = '' }, 2000)
}

function doDisconnect() {
  clearCredentials()
  clearClient()
  confirmDisconnect.value = false
  emit('disconnected')
  emit('close')
}
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44,36,22,0.45);
  z-index: 400;
  display: flex;
  justify-content: flex-end;
  backdrop-filter: blur(3px);
}

.settings-drawer {
  background: var(--warm-white, #fff9f2);
  width: 340px;
  max-width: 92vw;
  height: 100%;
  overflow-y: auto;
  box-shadow: -8px 0 40px rgba(44,36,22,0.22);
  display: flex;
  flex-direction: column;
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

/* ── Header ── */
.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1.5px solid var(--parchment, #ede0cc);
  background: var(--cream, #faf6ef);
  position: sticky;
  top: 0;
  z-index: 1;
}
.drawer-title {
  font-family: var(--font-display, serif);
  font-size: 18px;
  font-weight: 700;
  color: var(--charcoal, #2c2416);
}
.drawer-close {
  width: 30px; height: 30px;
  background: none; border: none;
  font-size: 15px; cursor: pointer;
  color: var(--brown-lt, #a07850);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s;
}
.drawer-close:hover { background: var(--parchment, #ede0cc); }

/* ── Sections ── */
.section {
  padding: 18px 20px;
  border-bottom: 1.5px solid var(--parchment, #ede0cc);
}
.section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--brown-lt, #a07850);
  margin-bottom: 12px;
}
.section-desc {
  font-size: 12.5px;
  color: var(--brown-lt, #a07850);
  line-height: 1.6;
  margin-bottom: 12px;
}

/* ── DB row ── */
.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--cream, #faf6ef);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 10px;
  margin-bottom: 12px;
}
.setting-info { flex: 1; }
.setting-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--charcoal, #2c2416);
  display: block;
}
.setting-val {
  font-size: 11px;
  color: var(--brown-lt, #a07850);
  font-family: monospace;
  word-break: break-all;
}
.status-dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.connected { background: #4caf50; box-shadow: 0 0 6px rgba(76,175,80,0.5); }

/* ── Danger button ── */
.danger-btn {
  width: 100%;
  padding: 10px;
  background: #fff5f5;
  border: 1.5px solid #fcc;
  border-radius: 10px;
  color: #c0392b;
  font-family: var(--font-body, sans-serif);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.danger-btn:hover { background: #fee; }

/* ── Confirm box ── */
.confirm-box {
  margin-top: 12px;
  background: #fff5f5;
  border: 1.5px solid #fcc;
  border-radius: 10px;
  padding: 12px;
}
.confirm-text {
  font-size: 12.5px;
  color: #c0392b;
  line-height: 1.5;
  margin-bottom: 10px;
}
.confirm-actions { display: flex; gap: 8px; justify-content: flex-end; }
.btn-cancel {
  padding: 7px 14px;
  background: var(--cream, #faf6ef);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  color: var(--brown-lt, #a07850);
}
.btn-confirm-danger {
  padding: 7px 14px;
  background: #c0392b;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
}

/* ── Copy row ── */
.copy-row { margin-bottom: 10px; }
.copy-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--brown-lt, #a07850);
  display: block;
  margin-bottom: 5px;
}
.copy-field {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--cream, #faf6ef);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 8px;
  padding: 7px 10px;
}
.copy-value {
  flex: 1;
  font-size: 11px;
  font-family: monospace;
  color: var(--charcoal, #2c2416);
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.12s;
}
.copy-btn:hover { background: var(--parchment, #ede0cc); }

.open-link {
  display: inline-block;
  font-size: 12.5px;
  color: var(--terracotta, #c1440e);
  text-decoration: none;
  font-weight: 600;
}
.open-link:hover { text-decoration: underline; }

/* ── Security note ── */
.security-note {
  background: #fff8e1;
  border: 1.5px solid #ffe082;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  color: #b7860b;
  line-height: 1.6;
}
.security-note strong { color: #8a6400; }

/* ── QR ── */
.qr-section { margin-top: 14px; text-align: center; }
.qr-label {
  font-size: 12px;
  color: var(--brown-lt, #a07850);
  margin-bottom: 10px;
}
.qr-wrap {
  display: inline-block;
  padding: 8px;
  background: var(--warm-white, #fff9f2);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 12px;
}
.qr-img { display: block; border-radius: 6px; }
.qr-placeholder {
  font-size: 12px;
  color: var(--parchment-dark, #d9c9ae);
  padding: 20px;
}

/* ── Slide-in transition ── */
.panel-enter-active, .panel-leave-active {
  transition: opacity 0.25s ease;
}
.panel-enter-active .settings-drawer,
.panel-leave-active .settings-drawer {
  transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
.panel-enter-from, .panel-leave-to { opacity: 0; }
.panel-enter-from .settings-drawer,
.panel-leave-to .settings-drawer { transform: translateX(100%); }
</style>
