/**
 * Supabase client singleton.
 * The anon key is safe to use client-side — it is designed for browser use.
 * Real security comes from Supabase Row Level Security (RLS) policies,
 * not from keeping the anon key secret.
 */
import { createClient } from '@supabase/supabase-js'

let _client = null

/** Return the active Supabase client, or null if not connected. */
export function getClient() {
  return _client
}

/** Initialise the client with validated credentials. */
export function initClient(url, anonKey) {
  _client = createClient(url, anonKey, {
    auth: { persistSession: false },   // we manage our own session storage
    global: { headers: { 'x-app': 'mealplanner' } },
  })
  return _client
}

/** Remove the client (used on disconnect). */
export function clearClient() {
  _client = null
}

export function isConnected() {
  return _client !== null
}

// ── Storage keys ─────────────────────────────────────────────────────────────
export const CRED_URL_KEY = 'mp_sb_url'
export const CRED_KEY_KEY = 'mp_sb_key'

export function loadStoredCredentials() {
  return {
    url: localStorage.getItem(CRED_URL_KEY) || '',
    key: localStorage.getItem(CRED_KEY_KEY) || '',
  }
}

export function saveCredentials(url, key) {
  localStorage.setItem(CRED_URL_KEY, url)
  localStorage.setItem(CRED_KEY_KEY, key)
}

export function clearCredentials() {
  localStorage.removeItem(CRED_URL_KEY)
  localStorage.removeItem(CRED_KEY_KEY)
}

/**
 * Test a connection without persisting anything.
 * Returns { ok, needsSetup, error }
 *   ok=true, needsSetup=false → DB ready
 *   ok=true, needsSetup=true  → connected but tables missing
 *   ok=false                  → bad credentials / network error
 */
export async function testConnection(url, key) {
  if (!url || !key) return { ok: false, error: 'URL and anon key are required.' }

  // Basic URL validation
  try { new URL(url) } catch {
    return { ok: false, error: 'Invalid URL format.' }
  }

  try {
    const client = createClient(url, key, { auth: { persistSession: false } })
    const { error } = await client.from('recipes').select('count').limit(1)

    if (!error) return { ok: true, needsSetup: false }

    // Postgres error code 42P01 = "undefined_table"
    if (error.code === '42P01' || error.message?.includes('does not exist')) {
      return { ok: true, needsSetup: true }
    }

    // Auth/network error
    return { ok: false, error: error.message || 'Connection failed.' }
  } catch (err) {
    return { ok: false, error: err.message || 'Network error — check the URL.' }
  }
}

// ── Share link helpers (uses URL hash — NEVER sent to server) ─────────────────
export function buildShareLink(url, key) {
  const payload = btoa(JSON.stringify({ url, key }))
  const base = `${window.location.origin}${window.location.pathname}`
  return `${base}#setup/${payload}`
}

export function parseShareLink(hash) {
  try {
    if (!hash.startsWith('#setup/')) return null
    const payload = hash.slice('#setup/'.length)
    const { url, key } = JSON.parse(atob(payload))
    if (!url || !key) return null
    return { url, key }
  } catch {
    return null
  }
}
