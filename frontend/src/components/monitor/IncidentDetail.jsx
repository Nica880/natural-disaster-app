import { useEffect, useState } from 'react'
import {
  AlertTriangle, Camera, Clock, MapPin, X, Map,
  Truck, Ambulance, Siren, Plane, Cross, Ship, Bus,
  ThumbsUp, ThumbsDown, Check,
  Wind, Droplets, Thermometer, CloudRain, ShieldAlert, ShieldCheck, Loader2,
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

// "What is it actually?" options — keep in sync with the classifier's classes;
// the backend derives the fine_tune_images/<folder> from these names.
const ACTUAL_TYPES = ['Wildfire', 'Flood', 'Car Crash', 'Cyclone', 'Earthquake', 'Normal']

export default function IncidentDetail({ incident, onClose, onDismiss }) {
  // Active main image — defaults to the best-evidence snapshot, but can be
  // swapped by clicking a thumbnail in the frame strip.
  const [activeFrame, setActiveFrame] = useState(null)
  // Operator ground-truth: null (unanswered) | true (correct) | false (false alarm)
  const [feedback, setFeedback] = useState(null)
  // False-alarm flow: picker visibility + the corrected class the operator chose
  const [pickingType, setPickingType] = useState(false)
  const [correctedType, setCorrectedType] = useState(null)
  // Live weather, tagged with the incident id it belongs to. Tagging lets us
  // show a fresh load when switching incidents without a synchronous state
  // reset inside the effect (which React flags as a cascading render).
  const [weather, setWeather] = useState(null)       // { forId, data }
  const [weatherErr, setWeatherErr] = useState(null)  // { forId, msg }

  const sendFeedback = (correct) => {
    setFeedback(correct)
    api.submitFeedback(incident.id, { verdict_correct: correct }).catch(() => setFeedback(null))
  }

  // Wrong verdict + the true class → backend stores it and harvests the frame
  // into fine_tune_images/<class>/ for the next training run.
  const sendCorrection = (actualType) => {
    setFeedback(false)
    setCorrectedType(actualType)
    api.submitFeedback(incident.id, { verdict_correct: false, actual_type: actualType })
      .catch(() => { setFeedback(null); setCorrectedType(null); setPickingType(false) })
  }

  const hasCoords = incident?.lat != null && incident?.lon != null

  // Fetch weather whenever a different located incident is opened.
  useEffect(() => {
    if (!hasCoords) return
    let cancelled = false
    const forId = incident.id
    api.weather(incident.lat, incident.lon, incident.disaster_type)
      .then((w) => { if (!cancelled) setWeather({ forId, data: w }) })
      .catch((e) => { if (!cancelled) setWeatherErr({ forId, msg: e.message || 'Weather unavailable' }) })
    return () => { cancelled = true }
  }, [incident?.id, incident?.lat, incident?.lon, incident?.disaster_type, hasCoords])

  // Only surface weather/error that belongs to the currently open incident.
  const curWeather = weather?.forId === incident?.id ? weather.data : null
  const curWeatherErr = weatherErr?.forId === incident?.id ? weatherErr.msg : null

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
          <div className="lg:col-span-2 p-6 bg-slate-50/40 divide-y divide-slate-200/70">
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

            {hasCoords && (
              <Section title="Weather on scene">
                <WeatherSection weather={curWeather} error={curWeatherErr} />
              </Section>
            )}

            <Section title="Recommended units">
              <ResourcesBlock resources={incident.resources} disasterType={incident.disaster_type} accent={tone.accent} />
            </Section>

            <Section title="Was the detection correct?">
              {feedback !== null ? (
                <p className="inline-flex items-center gap-1.5 text-xs text-emerald-700">
                  <Check className="size-3.5" />
                  {feedback
                    ? 'Recorded as correct — thanks.'
                    : `Recorded — saved for retraining as ${correctedType}.`}
                </p>
              ) : pickingType ? (
                <select autoFocus defaultValue=""
                        onChange={(e) => e.target.value && sendCorrection(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-amber-200 bg-white text-sm text-slate-700 focus:outline-none focus:border-amber-400">
                  <option value="" disabled>What is actually in the image?</option>
                  {ACTUAL_TYPES.map((t) => (
                    <option key={t} value={t}>{t === 'Normal' ? 'Normal — no incident' : t}</option>
                  ))}
                </select>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => sendFeedback(true)}
                          className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm hover:bg-emerald-100 transition-colors">
                    <ThumbsUp className="size-4" /> Correct
                  </button>
                  <button onClick={() => setPickingType(true)}
                          className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 text-sm hover:bg-amber-100 transition-colors">
                    <ThumbsDown className="size-4" /> False alarm
                  </button>
                </div>
              )}
            </Section>

            <div className="pt-4">
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
    <div className="py-4 first:pt-0">
      <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-2.5">{title}</p>
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

const RISK_TONE = {
  elevated: { box: 'bg-amber-50 border-amber-200 text-amber-800',   icon: ShieldAlert },
  reduced:  { box: 'bg-emerald-50 border-emerald-200 text-emerald-800', icon: ShieldCheck },
  normal:   { box: 'bg-slate-50 border-slate-200 text-slate-600',   icon: ShieldCheck },
}

function WeatherSection({ weather, error }) {
  if (error) {
    return <p className="text-xs text-slate-500 italic">{error}</p>
  }
  if (!weather) {
    return (
      <p className="inline-flex items-center gap-2 text-xs text-slate-400">
        <Loader2 className="size-4 animate-spin" /> Loading current conditions…
      </p>
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        {weather.icon && (
          <img src={`https://openweathermap.org/img/wn/${weather.icon}@2x.png`}
               alt="" className="size-12 -my-1" />
        )}
        <div className="min-w-0">
          <p className="text-2xl font-semibold text-slate-900 leading-none">{Math.round(weather.temp_c)}°C</p>
          <p className="text-xs text-slate-500 truncate">
            {weather.description}{weather.place ? ` · ${weather.place}` : ''}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <WeatherChip icon={Thermometer} label="Feels like" value={`${Math.round(weather.feels_like_c)}°C`} />
        <WeatherChip icon={Wind}        label="Wind"       value={`${weather.wind_speed_kmh} km/h`} />
        <WeatherChip icon={Droplets}    label="Humidity"   value={`${weather.humidity_pct}%`} />
        <WeatherChip icon={CloudRain}   label="Rain (1h)"  value={weather.rain_1h_mm != null ? `${weather.rain_1h_mm} mm` : 'none'} />
      </div>

      {weather.risk_note && <RiskBanner level={weather.risk_level} note={weather.risk_note} />}
    </div>
  )
}

function WeatherChip({ icon, label, value }) {
  const Icon = icon
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
      <Icon className="size-4 text-slate-400 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-slate-500 truncate">{label}</p>
        <p className="text-sm font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  )
}

function RiskBanner({ level, note }) {
  const tone = RISK_TONE[level] || RISK_TONE.normal
  const Icon = tone.icon
  return (
    <div className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs leading-relaxed ${tone.box}`}>
      <Icon className="size-4 shrink-0 mt-0.5" />
      <span>{note}</span>
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
