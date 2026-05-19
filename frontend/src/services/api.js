const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function postImage(path, file) {
  const formData = new FormData()
  formData.append('file', file)
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
}
