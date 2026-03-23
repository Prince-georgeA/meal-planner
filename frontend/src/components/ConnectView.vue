<template>
  <div class="connect-shell">
    <div class="connect-card">

      <!-- ── Brand ── -->
      <div class="brand">
        <span class="brand-logo">🥘</span>
        <div>
          <h1 class="brand-name">Meal<span>Planner</span></h1>
          <p class="brand-tagline">Your personal weekly menu tracker</p>
        </div>
      </div>

      <!-- ════════════════════════════════════════
           STEP 1 — Enter credentials
      ═══════════════════════════════════════════ -->
      <template v-if="step === 'connect'">
        <h2 class="step-title">Connect your database</h2>
        <p class="step-sub">
          Your data lives in your own free
          <a href="https://supabase.com" target="_blank" rel="noopener">Supabase</a>
          project — we never store it on our servers.
        </p>

        <!-- Pre-filled from share link -->
        <div class="prefill-banner" v-if="prefilled">
          🔗 Credentials pre-filled from a share link. Click Connect to continue.
        </div>

        <div class="form-group">
          <label class="form-label">Project URL</label>
          <input
            class="form-input"
            v-model="inputUrl"
            placeholder="https://xxxxxxxxxxxx.supabase.co"
            autocomplete="off"
            spellcheck="false"
            @keydown.enter="handleConnect"
          />
        </div>

        <div class="form-group">
          <label class="form-label">
            Anon (public) Key
            <span class="label-hint">— safe to share, not a secret</span>
          </label>
          <div class="key-row">
            <input
              class="form-input key-input"
              v-model="inputKey"
              :type="showKey ? 'text' : 'password'"
              placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              autocomplete="off"
              spellcheck="false"
              @keydown.enter="handleConnect"
            />
            <button class="btn-toggle-key" @click="showKey = !showKey" type="button">
              {{ showKey ? '🙈' : '👁' }}
            </button>
          </div>
        </div>

        <!-- Error -->
        <div class="error-box" v-if="error">⚠ {{ error }}</div>

        <!-- Actions -->
        <button class="btn btn-primary connect-btn" @click="handleConnect" :disabled="connecting">
          <span v-if="connecting" class="spinner">⏳</span>
          {{ connecting ? 'Connecting…' : '🔌 Connect & Continue' }}
        </button>

        <!-- How to get credentials -->
        <!-- Setup accordion -->
        <div class="setup-accordion">

          <!-- Step 1: Get credentials -->
          <details class="setup-panel" open>
            <summary class="setup-panel-head">
              <span class="setup-panel-num">1</span>
              <span class="setup-panel-title">Create a free Supabase project</span>
              <span class="setup-chevron">›</span>
            </summary>
            <div class="panel-body">
              <ol class="step-list">
                <li>Go to <a href="https://supabase.com" target="_blank" rel="noopener">supabase.com</a> and sign up for free</li>
                <li>Click <strong>New Project</strong>, give it any name, and wait ~1 min</li>
                <li>Go to <strong>Project Settings → API</strong></li>
                <li>Copy <strong>Project URL</strong> and paste it in the field above</li>
                <li>Copy the <strong>anon / public</strong> key and paste it above</li>
              </ol>
            </div>
          </details>

          <!-- Step 2: Run schema SQL -->
          <details class="setup-panel">
            <summary class="setup-panel-head">
              <span class="setup-panel-num">2</span>
              <span class="setup-panel-title">
                Set up the database tables
                <span class="required-badge">Required</span>
              </span>
              <span class="setup-chevron">›</span>
            </summary>
            <div class="panel-body">
              <p class="panel-desc">
                Run this SQL once in your Supabase project to create the tables the app needs.
              </p>
              <ol class="step-list" style="margin-bottom: 14px;">
                <li>Open your <a :href="supabaseEditorUrl" target="_blank" rel="noopener">Supabase SQL Editor ↗</a></li>
                <li>Click <strong>New query</strong>, paste the SQL below, then click <strong>Run</strong></li>
                <li>Return here and click <strong>Connect & Continue</strong></li>
              </ol>
              <div class="sql-box">
                <div class="sql-header">
                  <span class="sql-label">schema.sql</span>
                  <button class="btn-copy-sql" @click="copySqlInline" type="button">
                    {{ sqlInlineCopied ? "✓ Copied!" : "📋 Copy SQL" }}
                  </button>
                </div>
                <pre class="sql-code">{{ SCHEMA_SQL }}</pre>
              </div>
            </div>
          </details>

          <!-- Step 3: Connect -->
          <details class="setup-panel">
            <summary class="setup-panel-head">
              <span class="setup-panel-num">3</span>
              <span class="setup-panel-title">Click Connect & Continue</span>
              <span class="setup-chevron">›</span>
            </summary>
            <div class="panel-body">
              <p class="panel-desc">
                The app will verify your credentials and confirm all tables are ready.
                Your data lives exclusively in your own Supabase project — we never see or store it.
              </p>
            </div>
          </details>

        </div>
      </template>

      <!-- ════════════════════════════════════════
           STEP 2 — Database setup needed
      ═══════════════════════════════════════════ -->
      <template v-else-if="step === 'setup'">
        <h2 class="step-title">One-time database setup</h2>
        <p class="step-sub">
          Your Supabase project is connected but needs the MealPlanner tables.
          Run the SQL below — takes about 30 seconds.
        </p>

        <div class="setup-steps">
          <div class="setup-step">
            <span class="step-num">1</span>
            <span>Open your <a :href="supabaseEditorUrl" target="_blank">Supabase SQL Editor ↗</a></span>
          </div>
          <div class="setup-step">
            <span class="step-num">2</span>
            <span>Click <strong>New query</strong>, paste the SQL below, click <strong>Run</strong></span>
          </div>
          <div class="setup-step">
            <span class="step-num">3</span>
            <span>Come back here and click <strong>I've done it</strong></span>
          </div>
        </div>

        <div class="sql-box">
          <div class="sql-header">
            <span class="sql-label">schema.sql</span>
            <button class="btn-copy-sql" @click="copySql">
              {{ sqlCopied ? '✓ Copied!' : '📋 Copy SQL' }}
            </button>
          </div>
          <pre class="sql-code">{{ SCHEMA_SQL }}</pre>
        </div>

        <div class="setup-actions">
          <button class="btn btn-secondary" @click="step = 'connect'">← Back</button>
          <button class="btn btn-primary" @click="checkSetup" :disabled="checking">
            {{ checking ? '⏳ Checking…' : "✓ I've done it" }}
          </button>
        </div>
        <div class="error-box" v-if="error">⚠ {{ error }}</div>
      </template>

      <!-- ════════════════════════════════════════
           STEP 3 — Share link
      ═══════════════════════════════════════════ -->
      <template v-else-if="step === 'share'">
        <div class="success-banner">✓ Connected successfully!</div>
        <h2 class="step-title">Access from other devices</h2>
        <p class="step-sub">
          Share this link to connect another device instantly — no re-entering credentials.
        </p>

        <div class="share-warning">
          ⚠ <strong>Keep this link private.</strong> Anyone with it can access your meal plans.
          Send it only to your own devices via a private message or your password manager.
        </div>

        <div class="share-link-box">
          <input class="form-input share-input" :value="shareLink" readonly />
          <button class="btn btn-secondary btn-copy" @click="copyLink">
            {{ linkCopied ? '✓ Copied!' : '📋 Copy' }}
          </button>
        </div>

        <!-- QR code for mobile -->
        <div class="qr-section">
          <p class="qr-label">Or scan with your phone:</p>
          <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR code" class="qr-code" />
          <div v-else class="qr-loading">Generating QR…</div>
        </div>

        <button class="btn btn-primary continue-btn" @click="$emit('connected')">
          🚀 Open MealPlanner
        </button>
        <button class="skip-link" @click="$emit('connected')">Skip — I'll do this later</button>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  testConnection, initClient, saveCredentials,
  buildShareLink, parseShareLink, CRED_URL_KEY, CRED_KEY_KEY,
} from '../lib/supabase.js'
import SCHEMA_SQL_RAW from '../lib/schema.sql?raw'

defineEmits(['connected'])

const SCHEMA_SQL = SCHEMA_SQL_RAW

const step       = ref('connect')
const inputUrl   = ref('')
const inputKey   = ref('')
const showKey    = ref(false)
const prefilled  = ref(false)
const connecting = ref(false)
const checking   = ref(false)
const error      = ref('')
const sqlCopied       = ref(false)
const sqlInlineCopied = ref(false)
const linkCopied = ref(false)
const shareLink  = ref('')
const qrDataUrl  = ref('')

const supabaseEditorUrl = computed(() => {
  try {
    const host = new URL(inputUrl.value).hostname  // xxxx.supabase.co
    const ref  = host.split('.')[0]
    return `https://supabase.com/dashboard/project/${ref}/sql/new`
  } catch { return 'https://supabase.com/dashboard' }
})

// ── On mount: check for share link in URL hash ──────────────────────────────
onMounted(() => {
  const parsed = parseShareLink(window.location.hash)
  if (parsed) {
    inputUrl.value = parsed.url
    inputKey.value = parsed.key
    prefilled.value = true
    // Clean the hash so it's not visible or bookmarked accidentally
    history.replaceState(null, '', window.location.pathname)
  }
})

// ── Connect ──────────────────────────────────────────────────────────────────
async function handleConnect() {
  const url = inputUrl.value.trim().replace(/\/$/, '')
  const key = inputKey.value.trim()
  error.value = ''

  if (!url || !key) {
    error.value = 'Both fields are required.'
    return
  }

  connecting.value = true
  const result = await testConnection(url, key)
  connecting.value = false

  if (!result.ok) {
    error.value = result.error
    return
  }

  // Save + initialise client
  saveCredentials(url, key)
  initClient(url, key)

  if (result.needsSetup) {
    step.value = 'setup'
  } else {
    await goToShare(url, key)
  }
}

// ── Setup check ──────────────────────────────────────────────────────────────
async function checkSetup() {
  error.value = ''
  checking.value = true
  const result = await testConnection(inputUrl.value.trim(), inputKey.value.trim())
  checking.value = false

  if (!result.ok) { error.value = result.error; return }
  if (result.needsSetup) {
    error.value = 'Tables not found yet — make sure you ran the full SQL and clicked Run.'
    return
  }

  await goToShare(inputUrl.value.trim(), inputKey.value.trim())
}

// ── Build share link + QR ────────────────────────────────────────────────────
async function goToShare(url, key) {
  shareLink.value = buildShareLink(url, key)
  step.value = 'share'
  generateQR(shareLink.value)
}

async function generateQR(url) {
  try {
    // Use QRCode from cdn — loaded via importmap in index.html fallback
    // We import dynamically to keep the bundle lean
    const QRCode = (await import('qrcode')).default
    qrDataUrl.value = await QRCode.toDataURL(url, {
      width: 200,
      margin: 2,
      color: { dark: '#2c2416', light: '#fff9f2' },
    })
  } catch {
    qrDataUrl.value = ''  // QR silently unavailable, link still works
  }
}

async function copySqlInline() {
  await navigator.clipboard.writeText(SCHEMA_SQL)
  sqlInlineCopied.value = true
  setTimeout(() => { sqlInlineCopied.value = false }, 2500)
}

async function copySql() {
  await navigator.clipboard.writeText(SCHEMA_SQL)
  sqlCopied.value = true
  setTimeout(() => { sqlCopied.value = false }, 2500)
}

async function copyLink() {
  await navigator.clipboard.writeText(shareLink.value)
  linkCopied.value = true
  setTimeout(() => { linkCopied.value = false }, 2500)
}
</script>

<style scoped>
.connect-shell {
  min-height: 100vh;
  background: linear-gradient(135deg, #fdf6ec 0%, #f5ede0 50%, #ede0cc 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.connect-card {
  background: var(--warm-white, #fff9f2);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(44,36,22,0.14);
  padding: 36px 32px;
  width: 480px;
  max-width: 100%;
  animation: slideUp 0.3s ease;
}

/* ── Brand ── */
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}
.brand-logo { font-size: 40px; }
.brand-name {
  font-family: var(--font-display, Georgia, serif);
  font-size: 26px;
  font-weight: 700;
  color: var(--charcoal, #2c2416);
}
.brand-name span { color: var(--terracotta, #c1440e); }
.brand-tagline { font-size: 13px; color: var(--brown-lt, #a07850); }

/* ── Step headings ── */
.step-title {
  font-family: var(--font-display, serif);
  font-size: 19px;
  font-weight: 700;
  color: var(--charcoal, #2c2416);
  margin-bottom: 6px;
}
.step-sub {
  font-size: 13px;
  color: var(--brown-lt, #a07850);
  margin-bottom: 22px;
  line-height: 1.6;
}
.step-sub a { color: var(--terracotta, #c1440e); }

/* ── Form ── */
.form-group { margin-bottom: 16px; }
.form-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brown-lt, #a07850);
  margin-bottom: 6px;
}
.label-hint {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--parchment-dark, #d9c9ae);
  font-size: 11px;
}
.key-row { display: flex; gap: 8px; }
.key-input { flex: 1; font-family: monospace; font-size: 12px; }
.btn-toggle-key {
  background: var(--cream, #faf6ef);
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 8px;
  padding: 0 12px;
  cursor: pointer;
  font-size: 16px;
  flex-shrink: 0;
  transition: background 0.15s;
}
.btn-toggle-key:hover { background: var(--parchment, #ede0cc); }

/* ── Prefill banner ── */
.prefill-banner {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  color: #2e7d32;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 16px;
}

/* ── Error ── */
.error-box {
  background: #fff5f5;
  border: 1px solid #fcc;
  color: #c0392b;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 14px;
}

/* ── Connect button ── */
.connect-btn {
  width: 100%;
  padding: 13px;
  font-size: 15px;
  margin-bottom: 16px;
}

/* ── How-to ── */
.how-to {
  font-size: 13px;
  color: var(--brown-lt, #a07850);
  border: 1px solid var(--parchment, #ede0cc);
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
}
.how-to summary { font-weight: 600; cursor: pointer; user-select: none; }
.how-steps {
  margin: 10px 0 0 16px;
  line-height: 2;
  color: var(--charcoal, #2c2416);
}
.how-steps a { color: var(--terracotta, #c1440e); }

/* ── Setup steps ── */
.setup-steps { margin-bottom: 18px; }
.setup-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--parchment, #ede0cc);
  font-size: 14px;
  color: var(--charcoal, #2c2416);
}
.setup-step:last-child { border-bottom: none; }
.setup-step a { color: var(--terracotta, #c1440e); }
.step-num {
  width: 24px; height: 24px;
  background: var(--terracotta, #c1440e);
  color: #fff;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  flex-shrink: 0;
}

/* ── SQL box ── */
.sql-box {
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 18px;
}
.sql-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--cream, #faf6ef);
  padding: 8px 14px;
  border-bottom: 1px solid var(--parchment, #ede0cc);
}
.sql-label { font-size: 12px; font-weight: 600; color: var(--brown-lt, #a07850); font-family: monospace; }
.btn-copy-sql {
  background: var(--warm-white, #fff9f2);
  border: 1px solid var(--parchment, #ede0cc);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-copy-sql:hover { background: var(--parchment, #ede0cc); }
.sql-code {
  font-size: 11px;
  font-family: 'Fira Code', 'Courier New', monospace;
  color: var(--charcoal, #2c2416);
  padding: 14px;
  max-height: 220px;
  overflow-y: auto;
  white-space: pre;
  line-height: 1.6;
  background: var(--warm-white, #fff9f2);
}

.setup-actions { display: flex; gap: 10px; }

/* ── Share / Success ── */
.success-banner {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  color: #2e7d32;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 18px;
  text-align: center;
}

.share-warning {
  background: #fff8e1;
  border: 1px solid #ffe082;
  color: #b7860b;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
  margin-bottom: 14px;
}

.share-link-box { display: flex; gap: 8px; margin-bottom: 20px; }
.share-input { flex: 1; font-size: 11px; font-family: monospace; }
.btn-copy { white-space: nowrap; flex-shrink: 0; }

.qr-section { text-align: center; margin-bottom: 22px; }
.qr-label { font-size: 12px; color: var(--brown-lt, #a07850); margin-bottom: 10px; }
.qr-code { border-radius: 10px; border: 3px solid var(--parchment, #ede0cc); }
.qr-loading { font-size: 12px; color: var(--parchment-dark, #d9c9ae); padding: 20px; }

.continue-btn { width: 100%; padding: 13px; font-size: 15px; margin-bottom: 10px; }
.skip-link {
  display: block;
  text-align: center;
  font-size: 12px;
  color: var(--brown-lt, #a07850);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}

@keyframes slideUp {
  from { transform: translateY(16px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}

/* ── Setup accordion ── */
.setup-accordion {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 4px;
}
.setup-panel {
  border: 1.5px solid var(--parchment, #ede0cc);
  border-radius: 10px;
  overflow: hidden;
  background: var(--cream, #faf6ef);
}
.setup-panel-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  cursor: pointer;
  list-style: none;
  user-select: none;
  transition: background 0.15s;
}
.setup-panel-head::-webkit-details-marker { display: none; }
.setup-panel-head:hover { background: var(--parchment, #ede0cc); }
.setup-panel[open] > .setup-panel-head {
  background: var(--parchment, #ede0cc);
  border-bottom: 1px solid var(--parchment-dark, #d9c9ae);
}
.setup-panel-num {
  width: 20px; height: 20px;
  background: var(--terracotta, #c1440e);
  color: #fff;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  flex-shrink: 0;
}
.setup-panel-title {
  flex: 1;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--charcoal, #2c2416);
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body, 'DM Sans', sans-serif);
}
.required-badge {
  font-size: 10px;
  font-weight: 700;
  background: #fff3e0;
  color: #b84e00;
  border: 1px solid #ffcc80;
  border-radius: 20px;
  padding: 2px 8px;
  letter-spacing: 0.02em;
}
.setup-chevron {
  font-size: 16px;
  color: var(--brown-lt, #a07850);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.setup-panel[open] .setup-chevron { transform: rotate(90deg); }
.panel-body { padding: 14px 16px 16px; }
.panel-desc {
  font-size: 13px;
  color: var(--brown-lt, #a07850);
  line-height: 1.65;
  margin: 0 0 12px;
}
.step-list {
  margin: 0;
  padding: 0 0 0 20px;
  list-style: decimal;
  font-size: 13px;
  color: var(--charcoal, #2c2416);
  font-family: var(--font-body, sans-serif);
}
.step-list li {
  padding: 6px 0 6px 6px;
  line-height: 1.5;
  border-bottom: 1px solid rgba(237,224,204,0.5);
}
.step-list li:last-child { border-bottom: none; }
.step-list a { color: var(--terracotta, #c1440e); text-decoration: none; }
.step-list a:hover { text-decoration: underline; }
</style>
