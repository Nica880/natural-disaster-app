import { useEffect, useState } from 'react'
import { Target, ChevronDown, ChevronUp } from 'lucide-react'

import { api } from '../../services/api'

const pct = (p) => `${Math.round((p || 0) * 100)}%`

/** Collapsible, discreet panel of detection-accuracy stats computed from
 *  operator feedback. Mirrors IncidentHistory: collapsed by default, fetches
 *  on open. Text-first and muted — no flashy charts. */
export default function FeedbackStats() {
  const [open, setOpen] = useState(false)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api.feedbackStats()
      .then(data => setStats(data && typeof data === 'object' ? data : null))
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [open])

  const reviewed = stats?.total_reviewed ?? 0

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
      >
        <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
          <Target className="size-4 text-slate-400" />
          Detection accuracy
          {stats && reviewed > 0 && <span className="text-xs text-slate-400">({pct(stats.precision)})</span>}
        </span>
        {open ? <ChevronUp className="size-4 text-slate-400" /> : <ChevronDown className="size-4 text-slate-400" />}
      </button>

      {open && (
        <div className="border-t border-slate-100">
          {loading ? (
            <p className="px-4 py-6 text-sm text-slate-400 text-center">Loading…</p>
          ) : !stats || reviewed === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-400 text-center">
              No operator feedback yet — mark incidents Correct / False alarm to build accuracy stats.
            </p>
          ) : (
            <div className="px-4 py-3">
              <p className="text-xs text-slate-500">
                {reviewed} reviewed · {pct(stats.precision)} confirmed correct
                {stats.total_false > 0 && ` · ${stats.total_false} false alarm${stats.total_false > 1 ? 's' : ''}`}
              </p>
              <ul className="mt-3 space-y-2.5">
                {stats.by_type.map(t => (
                  <li key={t.disaster_type}>
                    <div className="flex items-center justify-between gap-2 text-xs text-slate-600">
                      <span className="truncate">{t.disaster_type}</span>
                      <span className="shrink-0 text-slate-400">
                        {t.correct}/{t.reviewed} · {pct(t.precision)}
                      </span>
                    </div>
                    <div className="mt-1 h-1 rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-400" style={{ width: pct(t.precision) }} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
