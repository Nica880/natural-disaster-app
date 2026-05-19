import { useEffect, useState } from 'react'
import { ScanLine, Eye, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'

import ImageDropzone from '../components/analyze/ImageDropzone'
import VerdictCard from '../components/analyze/VerdictCard'
import ClassifyCard from '../components/analyze/results/ClassifyCard'
import DetectCard from '../components/analyze/results/DetectCard'
import FloodCard from '../components/analyze/results/FloodCard'
import FireCard from '../components/analyze/results/FireCard'
import CarCrashCard from '../components/analyze/results/CarCrashCard'
import Alert from '../components/ui/Alert'
import Toggle from '../components/ui/Toggle'
import { useAnalysis } from '../hooks/useAnalysis'

export default function Analyze() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [showOverlays, setShowOverlays] = useState(true)
  const [showDetails, setShowDetails] = useState(false)
  const { data, error, loading, rerun } = useAnalysis(file)

  useEffect(() => {
    if (!file) { setPreview(null); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const onSelect = (f) => setFile(f)
  const onClear  = () => setFile(null)

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 uppercase tracking-wider font-medium mb-2">
            <ScanLine className="size-3.5" />
            Analyser
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Disaster analysis</h1>
          <p className="text-slate-600 mt-1">Drop an image. Every model runs automatically; the verdict appears below.</p>
        </div>
      </header>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-4 lg:sticky lg:top-20 self-start">
          <ImageDropzone file={file} preview={preview} onSelect={onSelect} onClear={onClear} />

          {file && (
            <>
              <Toggle
                checked={showOverlays}
                onChange={setShowOverlays}
                icon={Eye}
                label="Show overlays"
                hint="Draw model boxes / masks on result images"
              />
              <button
                type="button"
                onClick={rerun}
                disabled={loading}
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Analysing…' : 'Re-run analysis'}
              </button>
            </>
          )}

          {error && (
            <Alert tone="error" title="Analysis failed">{error}</Alert>
          )}
        </div>

        {/* Right column */}
        <div className="lg:col-span-3 space-y-4">
          {!file && (
            <EmptyState />
          )}

          {file && loading && (
            <LoadingState />
          )}

          {file && !loading && data && (
            <>
              <VerdictCard verdict={data.verdict} showOverlay={showOverlays} />

              <button
                type="button"
                onClick={() => setShowDetails(s => !s)}
                className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-sm font-medium text-slate-700"
              >
                <span>{showDetails ? 'Hide' : 'Show'} per-model details</span>
                {showDetails ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
              </button>

              {showDetails && (
                <div className="space-y-4 animate-fade-up">
                  <ClassifyCard data={data.classification} />
                  <FireCard     data={data.fire}     showOverlay={showOverlays} />
                  <FloodCard    data={data.flood}    showOverlay={showOverlays} />
                  <CarCrashCard data={data.carcrash} showOverlay={showOverlays} />
                  <DetectCard   data={data.objects}  showOverlay={showOverlays} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="border border-dashed border-slate-300 rounded-2xl p-10 text-center bg-white/60">
      <ScanLine className="size-8 text-slate-400 mx-auto mb-3" />
      <p className="text-slate-600 font-medium">No image yet</p>
      <p className="text-sm text-slate-500 mt-1">Drop a drone photo on the left to start the automatic analysis.</p>
    </div>
  )
}

function LoadingState() {
  const lines = [
    'Classifying scene with ResNet-18…',
    'Running fire & smoke detector…',
    'Running flood segmenter…',
    'Running car-crash detector…',
    'Counting people, vehicles, buildings…',
    'Building verdict…',
  ]
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 animate-fade-up">
      <div className="flex items-center gap-3 mb-4">
        <RefreshCw className="size-5 text-indigo-600 animate-spin" />
        <span className="font-medium text-slate-900">Analysing the image…</span>
      </div>
      <ul className="space-y-1.5 text-sm text-slate-500">
        {lines.map((l, i) => (
          <li key={l} className="flex items-center gap-2 animate-pulse" style={{ animationDelay: `${i * 80}ms` }}>
            <span className="size-1.5 rounded-full bg-slate-300" />
            {l}
          </li>
        ))}
      </ul>
    </div>
  )
}
