import { useCallback, useState } from 'react'
import { api } from '../services/api'

const INITIAL = {
  classify: null,
  detect:   null,
  flood:    null,
  fire:     null,
  carcrash: null,
}

/** Manages the multi-call analysis flow for a single uploaded image.
 *
 * Returns one `run(key)` function and a results map. Errors are stored
 * per-action so the UI can surface them next to the offending button.
 */
export function useAnalysis(file) {
  const [results, setResults] = useState(INITIAL)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(null)

  const reset = useCallback(() => {
    setResults(INITIAL)
    setErrors({})
    setLoading(null)
  }, [])

  const run = useCallback((key) => async () => {
    if (!file) return
    const fn = {
      classify: api.classify,
      detect:   api.detect,
      flood:    api.detectFlood,
      fire:     api.detectFire,
      carcrash: api.detectCarCrash,
    }[key]
    if (!fn) return
    setLoading(key)
    setErrors(prev => ({ ...prev, [key]: null }))
    try {
      const data = await fn(file)
      setResults(prev => ({ ...prev, [key]: data }))
    } catch (err) {
      setErrors(prev => ({ ...prev, [key]: err.message }))
    } finally {
      setLoading(null)
    }
  }, [file])

  const runAll = useCallback(async () => {
    if (!file) return
    await run('classify')()
    await Promise.all([run('detect')(), run('flood')(), run('fire')(), run('carcrash')()])
  }, [file, run])

  return { results, errors, loading, run, runAll, reset }
}
