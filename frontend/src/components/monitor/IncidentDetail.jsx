import { useEffect, useState } from 'react'
import {
  AlertTriangle, Camera, Clock, MapPin, X, Map,
  Truck, Ambulance, Siren, Plane, Cross, Ship, Bus,
  ThumbsUp, ThumbsDown, Check,
} from 'lucide-react'

import { api } from '../../services/api'

const DISASTER_TONES = {
  Wildfire:    { badge: 'bg-orange-50 text-orange-700 border-orange-200', accent: 'text-orange-600' },
  Flood:       { badge: 'bg-blue-50 text-blue-700 border-blue-200',       accent: 'text-blue-600'   },
  'Car Crash': { badge: 'bg-zinc-50 text-zinc-700 border-zinc-200',       accent: 'text-zinc-700'   },
  Cyclone:     { badge: 'bg-violet-50 text-violet-700 border-violet-200', accent: 'text-violet-600' },
  Earthquake:  { badge: 'bg-amber-50 text-amber-700 border-amber-200',    accent: 'text-amber-600'  },
}

const RESOURCE_META = {
  fire_trucks:      { label: 'Fire trucks',         icon: Truck },
  ambulances:       { label: 'Ambulances',          icon: Ambulance },
  police_units:     { label: 'Police units',        icon: Siren },
  aerial_units:     { label: 'Aerial units',        icon: Plane },
  smurd:            { label: 'SMURD teams',         icon: Cross },
  tow_trucks:       { label: 'Tow trucks',          icon: Truck },
  boats:            { label: 'Rescue boats',        icon: Ship },
  evacuation_buses: { label: 'Evacuation buses',    icon: Bus },
}

const fmt = (iso) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export default function IncidentDetail({ incident, onClose, onDismiss }) {
  // Active main image — defaults to the best-evidence snapshot, but can be
  // swapped by clicking a thumbnail in the frame strip.
  const [activeFrame, setActiveFrame] = useState(null)
  // Operator ground-truth: null (unanswered) | true (correct) | false (false alarm)
  const [feedback, setFeedback] = useState(null)

  const sendFeedback = (correct) => {
    setFeedback(correct)
    api.submitFeedback(incident.id, { verdict_correct: correct }).catch(() => setFeedback(null))
  }

  // Close on Escape — small operator-quality touch.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!incident) return null
  const tone = DISASTER_TONES[incident.disaster_type] || { badge: 'bg-slate-50 text-slate-700 border-slate-200', accent: 'text-slate-600' }
  const mainSnapshot = activeFrame?.snapshot || incident.snapshot
  const mapUrl = (incident.lat != null && incident.lon != null)
    ? `https://www.google.com/maps?q=${incident.lat},${incident.lon}`
    : null

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-up"
         onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[92vh] overflow-hidden shadow-2xl flex flex-col"
           onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-semibold border ${tone.badge}`}>
              <AlertTriangle className="size-4" />
              {incident.disaster_type}
              {incident.severity && <span className="opacity-70 font-normal">· {incident.severity}</span>}
            </div>
            <p className="text-sm text-slate-600 truncate">{incident.summary}</p>
          </div>
          <button onClick={onClose}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                  title="Close (Esc)">
            <X className="size-5" />
          </button>
        </div>

        {/* Body */}
        <div className="grid lg:grid-cols-5 gap-0 overflow-y-auto">
          {/* Left — evidence */}
          <div className="lg:col-span-3 p-6 space-y-4 border-r border-slate-200">
            {mainSnapshot
              ? <img src={mainSnapshot} alt={incident.disaster_type}
                     className="w-full rounded-xl border border-slate-200 bg-slate-900 object-contain max-h-[60vh]" />
              : <div className="aspect-video rounded-xl border border-dashed border-slate-300 flex items-center justify-center text-slate-400">No snapshot</div>}

            {incident.frames.length > 1 && (
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-2">
                  Evidence frames ({incident.frames.length})
                </p>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {incident.frames.map((f, idx) => {
                    const isActive = (activeFrame ?? incident.frames[incident.frames.length - 1]) === f
                    return (
                      <button key={idx} onClick={() => setActiveFrame(f)}
                              className={`shrink-0 rounded-lg overflow-hidden border-2 transition-all ${
                                isActive ? 'border-indigo-500' : 'border-transparent hover:border-slate-300'
                              }`}
                              title={`${fmt(f.timestamp)} · conf ${(f.confidence * 100).toFixed(0)}%`}>
                        <img src={f.snapshot} alt={`frame ${idx + 1}`}
                             className="h-16 w-24 object-cover bg-slate-900" />
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right — metrics, location, resources, actions */}
          <div className="lg:col-span-2 p-6 space-y-5 bg-slate-50/40">
            <Section title="Metrics">
              <Stat label="Confidence"   value={`${(incident.confidence * 100).toFixed(0)}%`} />
              {incident.severity      && <Stat label="Severity"   value={incident.severity} />}
              {incident.affected_area_pct != null && (
                <Stat label="Affected area" value={`${incident.affected_area_pct.toFixed(1)}% of frame`} />
              )}
              {incident.affected_area_m2 != null && incident.affected_area_m2 > 0 && (
                <Stat label="Approx. ground" value={`${incident.affected_area_m2.toFixed(0)} m²`} />
              )}
              <Stat label="Frames" value={`${incident.frame_count} captured`} />
              <Stat label="Active since" value={`${fmt(incident.first_seen)} → ${fmt(incident.last_seen)}`} />
            </Section>

            <Section title="Source">
              <Row icon={Camera}>{incident.camera_id}</Row>
              <Row icon={MapPin}>{incident.location || 'no location'}</Row>
              {mapUrl && (
                <a href={mapUrl} target="_blank" rel="noreferrer"
                   className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-700 hover:border-indigo-300 hover:text-indigo-700 transition-colors">
                  <Map className="size-4" />
                  Open in Google Maps
                </a>
              )}
            </Section>

            <Section title="Recommended units">
              <ResourcesBlock resources={incident.resources} disasterType={incident.disaster_type} accent={tone.accent} />
            </Section>

            <Section title="Was the detection correct?">
              {feedback !== null ? (
                <p className="inline-flex items-center gap-1.5 text-xs text-emerald-700">
                  <Check className="size-3.5" />
                  Recorded as {feedback ? 'correct' : 'a false alarm'} — thanks.
                </p>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => sendFeedback(true)}
                          className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm hover:bg-emerald-100 transition-colors">
                    <ThumbsUp className="size-4" /> Correct
                  </button>
                  <button onClick={() => sendFeedback(false)}
                          className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 text-sm hover:bg-amber-100 transition-colors">
                    <ThumbsDown className="size-4" /> False alarm
                  </button>
                </div>
              )}
            </Section>

            <div className="pt-2 border-t border-slate-200">
              <button onClick={onDismiss}
                      className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 transition-colors">
                <X className="size-4" />
                Dismiss incident
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-2">{title}</p>
      <div className="space-y-1.5">{children}</div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-sm font-medium text-slate-900 text-right">{value}</span>
    </div>
  )
}

function Row({ icon: Icon, children }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-700">
      <Icon className="size-4 text-slate-400 shrink-0" />
      <span className="truncate">{children}</span>
    </div>
  )
}

function ResourcesBlock({ resources, disasterType, accent }) {
  if (!resources || Object.keys(resources).length === 0) {
    return (
      <p className="text-xs text-slate-500 italic">
        No specialist model available for <span className="font-medium">{disasterType}</span> —
        train the corresponding detector to surface resource recommendations.
      </p>
    )
  }
  const entries = Object.entries(resources).filter(([, n]) => n > 0)
  if (entries.length === 0) {
    return <p className="text-xs text-slate-500 italic">No additional units recommended.</p>
  }
  return (
    <div className="grid grid-cols-2 gap-2">
      {entries.map(([key, count]) => {
        const meta = RESOURCE_META[key] || { label: key, icon: AlertTriangle }
        const Icon = meta.icon
        return (
          <div key={key} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
            <Icon className={`size-4 ${accent} shrink-0`} />
            <div className="min-w-0">
              <p className="text-xs text-slate-500 truncate">{meta.label}</p>
              <p className="text-sm font-semibold text-slate-900">×{count}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
