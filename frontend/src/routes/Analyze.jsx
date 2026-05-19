import { useEffect, useMemo, useState } from 'react'
import ImageDropzone from '../components/analyze/ImageDropzone'
import ActionGroup from '../components/analyze/ActionGroup'
import ClassifyCard from '../components/analyze/results/ClassifyCard'
import DetectCard from '../components/analyze/results/DetectCard'
import FloodCard from '../components/analyze/results/FloodCard'
import FireCard from '../components/analyze/results/FireCard'
import CarCrashCard from '../components/analyze/results/CarCrashCard'
import Alert from '../components/ui/Alert'
import { useAnalysis } from '../hooks/useAnalysis'
import { ScanLine } from 'lucide-react'

export default function Analyze() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const { results, errors, loading, run, runAll, reset } = useAnalysis(file)

  useEffect(() => {
    if (!file) { setPreview(null); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const onSelect = (f) => { setFile(f); reset() }
  const onClear  = () => { setFile(null); reset() }

  const anyResult = Object.values(results).some(Boolean)
  const errorList = useMemo(() => Object.entries(errors).filter(([, v]) => v), [errors])

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 uppercase tracking-wider font-medium mb-2">
            <ScanLine className="size-3.5" />
            Analyser
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Run a disaster analysis</h1>
          <p className="text-slate-600 mt-1">Upload one image, then trigger any combination of models.</p>
        </div>
      </header>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Left column: upload + actions */}
        <div className="lg:col-span-2 space-y-4 lg:sticky lg:top-20 self-start">
          <ImageDropzone file={file} preview={preview} onSelect={onSelect} onClear={onClear} />
          <ActionGroup
            disabled={!file}
            loading={loading}
            onRun={run}
            onRunAll={runAll}
          />
          {errorList.length > 0 && (
            <div className="space-y-2">
              {errorList.map(([k, msg]) => (
                <Alert key={k} tone={msg.includes('not loaded') ? 'warning' : 'error'} title={`${capitalize(k)} failed`}>
                  {msg}
                </Alert>
              ))}
            </div>
          )}
        </div>

        {/* Right column: results */}
        <div className="lg:col-span-3 space-y-4">
          {!anyResult && errorList.length === 0 && (
            <div className="border border-dashed border-slate-300 rounded-2xl p-10 text-center bg-white/60">
              <ScanLine className="size-8 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-600 font-medium">No analysis yet</p>
              <p className="text-sm text-slate-500 mt-1">
                {file ? 'Pick an action on the left to run a model.' : 'Upload a drone image to start.'}
              </p>
            </div>
          )}
          <ClassifyCard data={results.classify} />
          <FireCard data={results.fire} />
          <FloodCard data={results.flood} />
          <CarCrashCard data={results.carcrash} />
          <DetectCard data={results.detect} />
        </div>
      </div>
    </div>
  )
}

function capitalize(s) { return s ? s[0].toUpperCase() + s.slice(1) : s }
