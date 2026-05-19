import { useState } from 'react'
import { api } from './services/api'
import './App.css'

const initialResults = {
  classify: null,
  detect: null,
  flood: null,
  fire: null,
}
const initialErrors = {}

function App() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [results, setResults] = useState(initialResults)
  const [errors, setErrors] = useState(initialErrors)
  const [loadingAction, setLoadingAction] = useState(null)

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setSelectedImage(file)
    setPreview(URL.createObjectURL(file))
    setResults(initialResults)
    setErrors(initialErrors)
  }

  const run = (key, fn) => async () => {
    if (!selectedImage) return
    setLoadingAction(key)
    setErrors(prev => ({ ...prev, [key]: null }))
    try {
      const data = await fn(selectedImage)
      setResults(prev => ({ ...prev, [key]: data }))
    } catch (err) {
      setErrors(prev => ({ ...prev, [key]: err.message }))
    } finally {
      setLoadingAction(null)
    }
  }

  const isLoading = loadingAction !== null
  const { classify, detect, flood, fire } = results

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white p-8 rounded-3xl shadow-lg border border-gray-200">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Disaster Detection AI</h2>
          <p className="text-gray-500 mb-8">Upload a drone-captured image to detect, classify and quantify natural disasters.</p>

          <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center hover:border-gray-500 transition cursor-pointer">
            <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" id="imageInput" />
            <label htmlFor="imageInput" className="cursor-pointer">
              <div className="text-gray-600">
                <p className="text-lg">Click to upload image</p>
              </div>
            </label>
          </div>

          {preview && (
            <div className="mt-4">
              <img src={preview} alt="Preview" className="mx-auto rounded-lg shadow-md" style={{ maxHeight: 300, maxWidth: 350, objectFit: 'contain' }} />
            </div>
          )}

          <div className="flex gap-3 mt-6 flex-wrap">
            <ActionButton className="bg-slate-700 hover:bg-slate-800" loading={loadingAction === 'classify'} disabled={!selectedImage || isLoading} onClick={run('classify', api.classify)}>
              Detect Disaster
            </ActionButton>
            <ActionButton className="bg-slate-600 hover:bg-slate-700" loading={loadingAction === 'detect'} disabled={!selectedImage || isLoading} onClick={run('detect', api.detect)}>
              Analyze Details
            </ActionButton>
            <ActionButton className="bg-blue-600 hover:bg-blue-700" loading={loadingAction === 'flood'} disabled={!selectedImage || isLoading} onClick={run('flood', api.detectFlood)}>
              Flood Analysis
            </ActionButton>
            <ActionButton className="bg-orange-600 hover:bg-orange-700" loading={loadingAction === 'fire'} disabled={!selectedImage || isLoading} onClick={run('fire', api.detectFire)}>
              Fire Analysis
            </ActionButton>
          </div>

          <div className="mt-8 space-y-4">
            {classify && <ClassifyPanel data={classify} />}
            {detect && <DetectPanel data={detect} />}
            {flood && <FloodPanel data={flood} />}
            {fire && <FirePanel data={fire} />}
            {Object.entries(errors).filter(([, v]) => v).map(([k, msg]) => (
              <ErrorPanel key={k} action={k} message={msg} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionButton({ className = '', loading, disabled, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex-1 min-w-[150px] text-white py-3 px-6 rounded-full font-semibold disabled:bg-gray-300 disabled:cursor-not-allowed transition ${className}`}
    >
      {loading ? 'Working…' : children}
    </button>
  )
}

function ClassifyPanel({ data }) {
  return (
    <>
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6">
        <h3 className="text-2xl font-bold text-slate-800 mb-2">{data.predicted_class}</h3>
        <p className="text-lg text-slate-700">Confidence: {(data.confidence * 100).toFixed(2)}%</p>
      </div>
      <div className="bg-gray-50 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">All Probabilities</h3>
        <div className="space-y-3">
          {Object.entries(data.probabilities).map(([cls, prob]) => (
            <div key={cls} className="flex items-center">
              <span className="text-gray-700 text-sm font-medium w-32">{cls}</span>
              <div className="flex items-center gap-3 flex-1 ml-4">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div className="bg-slate-600 h-2 rounded-full transition-all" style={{ width: `${prob * 100}%` }} />
                </div>
                <span className="text-sm text-gray-600 w-16 text-right">{(prob * 100).toFixed(2)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function DetectPanel({ data }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">Detailed Analysis</h3>
      <div className="grid grid-cols-2 gap-2 text-gray-700">
        <p><strong>Vehicles:</strong> {data.vehicles}</p>
        <p><strong>People:</strong> {data.people}</p>
        <p><strong>Buildings:</strong> {data.buildings}</p>
        <p><strong>Estimated footprint:</strong> ~{data.estimated_area_m2} m²</p>
        <p><strong>Image coverage:</strong> {data.area_percent}%</p>
        <p><strong>Total objects:</strong> {data.objects_detected}</p>
      </div>
    </div>
  )
}

function FloodPanel({ data }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
      <h3 className="text-lg font-semibold text-blue-700 mb-4">Flood Segmentation</h3>
      <div className="grid grid-cols-2 gap-2 text-gray-700">
        <p><strong>Flooded area:</strong> {data.flood_area_pct}%</p>
        <p><strong>Estimated:</strong> ~{data.flood_area_m2} m²</p>
        <p><strong>Buildings:</strong> {data.buildings}</p>
        <p><strong>Vehicles:</strong> {data.vehicles}</p>
        <p><strong>People:</strong> {data.people}</p>
        <p><strong>Plants:</strong> {data.plants}</p>
      </div>
    </div>
  )
}

function FirePanel({ data }) {
  return (
    <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6">
      <h3 className="text-lg font-semibold text-orange-700 mb-4">Fire & Smoke Analysis</h3>
      <div className="grid grid-cols-2 gap-2 text-gray-700">
        <p><strong>Severity:</strong> <span className="capitalize">{data.severity}</span></p>
        <p><strong>Fire boxes:</strong> {data.fire_count}</p>
        <p><strong>Smoke boxes:</strong> {data.smoke_count}</p>
        <p><strong>Fire area:</strong> {data.fire_area_pct}%</p>
        <p><strong>Smoke area:</strong> {data.smoke_area_pct}%</p>
        <p><strong>Estimated:</strong> ~{data.estimated_area_m2} m²</p>
      </div>
      <div className="mt-4 pt-4 border-t border-orange-200">
        <h4 className="font-semibold text-orange-700 mb-2">Recommended response</h4>
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
          <p>Fire trucks: <strong>{data.resources.fire_trucks}</strong></p>
          <p>Ambulances: <strong>{data.resources.ambulances}</strong></p>
          <p>Police units: <strong>{data.resources.police_units}</strong></p>
          <p>SMURD: <strong>{data.resources.smurd}</strong></p>
          <p>Aerial units: <strong>{data.resources.aerial_units}</strong></p>
        </div>
      </div>
    </div>
  )
}

function ErrorPanel({ action, message }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-4">
      <p className="text-sm text-yellow-800"><strong>{action}</strong> failed: {message}</p>
    </div>
  )
}

export default App
