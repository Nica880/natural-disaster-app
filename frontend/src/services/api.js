const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function postImage(path, file, extra = {}) {
  const formData = new FormData()
  formData.append('file', file)
  for (const [k, v] of Object.entries(extra)) {
    if (v != null) formData.append(k, v)
  }
  const response = await fetch(`${API_BASE}${path}`, { method: 'POST', body: formData })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = body.detail || `${response.status} ${response.statusText}`
    const err = new Error(message)
    err.status = response.status
    throw err
  }
  return body
}

export const api = {
  analyze:         (file) => postImage('/api/v1/analyze',          file),
  classify:        (file) => postImage('/api/v1/classify',         file),
  detect:          (file) => postImage('/api/v1/detect',           file),
  detectFire:      (file) => postImage('/api/v1/detect/fire',      file),
  detectFlood:     (file) => postImage('/api/v1/detect/flood',     file),
  detectCarCrash:  (file) => postImage('/api/v1/detect/carcrash',  file),
  health:          () => fetch(`${API_BASE}/health`).then(r => r.json()),

  // Live monitor
  incidents:       () => fetch(`${API_BASE}/api/v1/incidents`).then(r => r.json()),
  dismissIncident: (id) => fetch(`${API_BASE}/api/v1/incidents/${id}/dismiss`, { method: 'POST' }).then(r => r.json()),
  streamIncidents: () => new EventSource(`${API_BASE}/api/v1/incidents/stream`),
  submitFeedback:  (id, payload) => fetch(`${API_BASE}/api/v1/incidents/${id}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json()),

  // History
  incidentHistory: (limit = 50) => fetch(`${API_BASE}/api/v1/incidents/history?limit=${limit}`).then(r => r.json()),
  getIncident:     (id) => fetch(`${API_BASE}/api/v1/incidents/${id}`).then(r => r.json()),
  imageUrl:        (ref) => (ref ? `${API_BASE}/api/v1/images/${ref}` : null),

  // Detection-accuracy stats (operator feedback)
  feedbackStats:   () => fetch(`${API_BASE}/api/v1/feedback/stats`).then(r => r.json()),
}
