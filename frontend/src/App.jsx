import { useState } from 'react'
import './App.css'

function App() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [floodResult, setFloodResult] = useState(null)
  const [fireResult, setFireResult] = useState(null)
  const [fireError, setFireError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
      setAnalysisResult(null)
      setFloodResult(null)
      setFireResult(null)
      setFireError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedImage) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', selectedImage)

    try {
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedImage) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', selectedImage)

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setAnalysisResult(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFloodAnalysis = async () => {
    if (!selectedImage) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', selectedImage)

    try {
      const response = await fetch('http://127.0.0.1:8000/flood_analysis', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setFloodResult(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFireAnalysis = async () => {
    if (!selectedImage) return

    setLoading(true)
    setFireError(null)
    const formData = new FormData()
    formData.append('file', selectedImage)

    try {
      const response = await fetch('http://127.0.0.1:8000/fire_analysis', {
        method: 'POST',
        body: formData
      })
      if (response.status === 503) {
        const err = await response.json()
        setFireError(err.detail || 'Fire model not loaded yet.')
      } else {
        const data = await response.json()
        setFireResult(data)
      }
    } catch (error) {
      console.error('Error:', error)
      setFireError('Network error contacting backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white p-8 rounded-3xl shadow-lg border border-gray-200">
          
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Disaster Detection AI</h2>
          <p className="text-gray-500 mb-8">Upload an image to detect natural disasters</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center hover:border-gray-500 transition cursor-pointer">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
                id="imageInput"
              />
              <label htmlFor="imageInput" className="cursor-pointer">
                <div className="text-gray-600">
                  <p className="text-lg">Click to upload image</p>
                </div>
              </label>
            </div>

            {preview && (
              <div className="mt-4">
                <img src={preview} alt="Preview" className="mx-auto rounded-lg shadow-md" style={{maxHeight: '300px', maxWidth: '350px', objectFit: 'contain'}} />
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={!selectedImage || loading}
                className="flex-1 bg-slate-700 text-white py-3 px-6 rounded-full font-semibold hover:bg-slate-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                {loading ? 'Analyzing...' : 'Detect Disaster'}
              </button>
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={!selectedImage || loading}
                className="flex-1 bg-slate-600 text-white py-3 px-6 rounded-full font-semibold hover:bg-slate-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                Analyze Details
              </button>
              <button
                type="button"
                onClick={handleFloodAnalysis}
                disabled={!selectedImage || loading}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-full font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                Flood Analysis
              </button>
              <button
                type="button"
                onClick={handleFireAnalysis}
                disabled={!selectedImage || loading}
                className="flex-1 bg-orange-600 text-white py-3 px-6 rounded-full font-semibold hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                Fire Analysis
              </button>
            </div>
          </form>

          {result && (
            <div className="mt-8 space-y-4">
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">
                  {result.class}
                </h2>
                <p className="text-lg text-slate-700">
                  Confidence: {(result.confidence * 100).toFixed(2)}%
                </p>
              </div>

              {analysisResult && (
                <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">Detailed Analysis</h3>
                  <div className="space-y-2 text-gray-700">
                    <p><strong>Vehicles detected:</strong> {analysisResult.vehicles}</p>
                    <p><strong>People detected:</strong> {analysisResult.people}</p>
                    <p><strong>Buildings detected:</strong> {analysisResult.buildings}</p>
                    <p><strong>Estimated footprint:</strong> ~{analysisResult.estimated_area_m2} m²</p>
                    <p><strong>Image coverage:</strong> {analysisResult.area_percent}%</p>
                    <p><strong>Total objects:</strong> {analysisResult.objects_detected}</p>
                  </div>
                </div>
              )}

              {fireError && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-yellow-700 mb-2">Fire Analysis unavailable</h3>
                  <p className="text-sm text-yellow-700">{fireError}</p>
                </div>
              )}

              {fireResult && (
                <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-orange-700 mb-4">Fire Analysis</h3>
                  <div className="grid grid-cols-2 gap-3 text-gray-700">
                    <p><strong>Severity:</strong> <span className="capitalize">{fireResult.severity}</span></p>
                    <p><strong>Fire boxes:</strong> {fireResult.fire_count}</p>
                    <p><strong>Smoke boxes:</strong> {fireResult.smoke_count}</p>
                    <p><strong>Fire area:</strong> {fireResult.fire_area_pct}%</p>
                    <p><strong>Smoke area:</strong> {fireResult.smoke_area_pct}%</p>
                    <p><strong>Estimated:</strong> ~{fireResult.estimated_area_m2} m²</p>
                  </div>
                  <div className="mt-4 pt-4 border-t border-orange-200">
                    <h4 className="font-semibold text-orange-700 mb-2">Recommended response</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <p>Fire trucks: <strong>{fireResult.resources.fire_trucks}</strong></p>
                      <p>Ambulances: <strong>{fireResult.resources.ambulances}</strong></p>
                      <p>Police units: <strong>{fireResult.resources.police_units}</strong></p>
                      <p>SMURD: <strong>{fireResult.resources.smurd}</strong></p>
                      <p>Aerial units: <strong>{fireResult.resources.aerial_units}</strong></p>
                    </div>
                  </div>
                </div>
              )}

              {floodResult && (
                <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-blue-700 mb-4">Flood Segmentation Analysis</h3>
                  <div className="space-y-2 text-gray-700">
                    <p><strong>Flooded area:</strong> {floodResult.flood_area_percent}%</p>
                    <p><strong>Estimated flood area:</strong> ~{floodResult.flood_area_m2} m²</p>
                    <p><strong>Buildings:</strong> {floodResult.buildings}</p>
                    <p><strong>Vehicles:</strong> {floodResult.vehicles}</p>
                    <p><strong>People:</strong> {floodResult.people}</p>
                    <p><strong>Plants:</strong> {floodResult.plants}</p>
                    <p><strong>Total objects:</strong> {floodResult.total_objects}</p>
                  </div>
                </div>
              )}

              <div className="bg-gray-50 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-4">All Probabilities</h3>
                <div className="space-y-3">
                  {Object.entries(result.probabilities).map(([cls, prob]) => (
                    <div key={cls} className="flex justify-between items-center">
                      <span className="text-gray-700 text-sm font-medium">{cls}</span>
                      <div className="flex items-center gap-3 flex-1 ml-4">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-slate-600 h-2 rounded-full transition-all"
                            style={{ width: `${prob * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 w-16 text-right">
                          {(prob * 100).toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
