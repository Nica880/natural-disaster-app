import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

/** Auto-fires the unified /api/v1/analyze endpoint whenever the file changes.
 *  Exposes the full response, a separate error, a loading flag, and a manual
 *  `rerun()` so the UI can offer "Re-run analysis" without re-uploading. */
export function useAnalysis(file) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const run = useCallback(async (f) => {
    if (!f) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const json = await api.analyze(f)
      setData(json)
    } catch (err) {
      setError(err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!file) {
      setData(null); setError(null); setLoading(false)
      return
    }
    run(file)
  }, [file, run])

  const rerun = useCallback(() => run(file), [file, run])

  return { data, error, loading, rerun }
}
