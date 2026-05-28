import { useEffect, useState } from 'react'
import { History, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'

import { api } from '../../services/api'

const TONES = {
  Wildfire:    'bg-orange-50 text-orange-700 border-orange-200',
  Flood:       'bg-blue-50 text-blue-700 border-blue-200',
  'Car Crash': 'bg-zinc-50 text-zinc-700 border-zinc-200',
  Cyclone:     'bg-violet-50 text-violet-700 border-violet-200',
  Earthquake:  'bg-amber-50 text-amber-700 border-amber-200',
}

const fmt = (iso) =>
  new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

/** Collapsible list of closed (dismissed) incidents, fetched from the durable
 *  store. Refetches when opened and whenever `refreshSignal` changes (e.g.
 *  after a dismiss). Clicking a row opens it in the shared detail modal. */
export default function IncidentHistory({ refreshSignal, onOpen }) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api.incidentHistory()
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [open, refreshSignal])

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
      >
        <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
          <History className="size-4 text-slate-400" />
          Incident history
          {items.length > 0 && <span className="text-xs text-slate-400">({items.length})</span>}
        </span>
        {open ? <ChevronUp className="size-4 text-slate-400" /> : <ChevronDown className="size-4 text-slate-400" />}
      </button>

      {open && (
        <div className="border-t border-slate-100">
          {loading ? (
            <p className="px-4 py-6 text-sm text-slate-400 text-center">Loading…</p>
          ) : items.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-400 text-center">No past incidents yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
              {items.map(it => (
                <li key={it.id}>
                  <button
                    type="button"
                    onClick={() => onOpen(it.id)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 transition-colors"
                  >
                    {api.imageUrl(it.snapshot_ref) ? (
                      <img src={api.imageUrl(it.snapshot_ref)} alt="" className="size-10 rounded object-cover bg-slate-900 shrink-0" />
                    ) : (
                      <span className="size-10 rounded bg-slate-100 shrink-0" />
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium border ${TONES[it.disaster_type] || 'bg-slate-50 text-slate-700 border-slate-200'}`}>
                          <AlertTriangle className="size-3" />{it.disaster_type}
                        </span>
                        {it.severity && <span className="text-[11px] text-slate-400">{it.severity}</span>}
                      </span>
                      <span className="block text-xs text-slate-500 truncate mt-0.5">
                        {it.location || it.camera_id} · {fmt(it.last_seen)} · {it.frame_count} frame{it.frame_count > 1 ? 's' : ''}
                      </span>
                    </span>
                    <span className="text-[11px] text-slate-400 shrink-0">{(it.confidence * 100).toFixed(0)}%</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
