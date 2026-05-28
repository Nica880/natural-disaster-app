import { AlertTriangle, Camera, Clock, MapPin, X } from 'lucide-react'

const TONES = {
  Wildfire:    'bg-orange-50 text-orange-700 border-orange-200',
  Flood:       'bg-blue-50 text-blue-700 border-blue-200',
  'Car Crash': 'bg-zinc-50 text-zinc-700 border-zinc-200',
  Cyclone:     'bg-violet-50 text-violet-700 border-violet-200',
  Earthquake:  'bg-amber-50 text-amber-700 border-amber-200',
}

const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export default function IncidentCard({ incident, onOpen, onDismiss }) {
  const tone = TONES[incident.disaster_type] || 'bg-slate-50 text-slate-700 border-slate-200'
  return (
    <button
      type="button"
      onClick={onOpen}
      className="text-left w-full rounded-2xl border border-slate-200 bg-white overflow-hidden animate-fade-up hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer"
    >
      {incident.snapshot && (
        <img src={incident.snapshot} alt={incident.disaster_type} className="w-full h-48 object-cover" />
      )}
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border ${tone}`}>
              <AlertTriangle className="size-3" />
              {incident.disaster_type}
              {incident.severity && <span className="opacity-70">· {incident.severity}</span>}
            </div>
            <p className="text-sm text-slate-900 font-medium mt-2 leading-snug">{incident.summary}</p>
          </div>
          <span
            role="button"
            tabIndex={0}
            onClick={(e) => { e.stopPropagation(); onDismiss() }}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); onDismiss() } }}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors shrink-0"
            title="Dismiss"
          >
            <X className="size-4" />
          </span>
        </div>
        <div className="grid grid-cols-2 gap-y-1.5 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1.5 truncate">
            <Camera className="size-3.5 shrink-0" />{incident.camera_id}
          </span>
          <span className="inline-flex items-center gap-1.5 truncate">
            <MapPin className="size-3.5 shrink-0" />{incident.location || 'no location'}
          </span>
          <span className="inline-flex items-center gap-1.5 col-span-2">
            <Clock className="size-3.5 shrink-0" />
            {formatTime(incident.first_seen)} → {formatTime(incident.last_seen)}
            <span className="text-slate-400">·</span>
            {incident.frame_count} frame{incident.frame_count > 1 ? 's' : ''}
            <span className="text-slate-400">·</span>
            conf {(incident.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </button>
  )
}
