/**
 * TrendPulse API Client
 * Uses relative paths so Vite dev server proxy routes to FastAPI backend.
 */

const API_BASE = '/api/v1'

async function request(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: { 'Accept': 'application/json', ...options.headers },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()
    return { ok: true, data }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

// Health
export async function checkBackendHealth() {
  return request('/health')
}

// Ingestion
export async function loadSampleData() {
  return request('/ingest/sample', { method: 'POST' })
}

export async function analyzeFiles(files) {
  const formData = new FormData()
  const fileList = Array.isArray(files) ? files : [files]
  fileList.forEach((file) => {
    formData.append('files', file)
  })

  try {
    const response = await fetch(`${API_BASE}/ingest/analyze`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Analysis failed (HTTP ${response.status})`)
    }

    const data = await response.json()
    return { ok: true, data }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function updateStaging(payload) {
  return request('/ingest/stage-update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function confirmImport(payload) {
  return request('/ingest/confirm-import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getStagedSession(sessionId) {
  return request(`/ingest/stage/${encodeURIComponent(sessionId)}`)
}

export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE}/ingest/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Upload failed (HTTP ${response.status})`)
    }

    const data = await response.json()
    return { ok: true, data }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function getIngestionHistory() {
  return request('/ingest/history')
}

export async function getIngestionStats() {
  return request('/ingest/stats')
}

export async function resetData() {
  return request('/ingest/reset', { method: 'DELETE' })
}

// Objective Seller Insights
export async function getInsights(params = {}) {
  const queryParts = []
  if (params.period) queryParts.push(`period=${encodeURIComponent(params.period)}`)
  if (params.category && params.category !== 'All') queryParts.push(`category=${encodeURIComponent(params.category)}`)
  const queryString = queryParts.length > 0 ? `?${queryParts.join('&')}` : ''
  return request(`/insights${queryString}`)
}

export async function getPredictions() {
  return request('/insights/predictions')
}

// Business Profile (Dynamic Store Identity)
export async function getBusinessProfile() {
  return request('/profile')
}

export async function updateBusinessProfile(profileData) {
  return request('/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profileData)
  })
}

