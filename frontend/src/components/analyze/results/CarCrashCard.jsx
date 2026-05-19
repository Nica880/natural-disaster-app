import Card, { CardHeader } from '../../ui/Card'
import Metric from '../../ui/Metric'
import { Car, Stethoscope, Shield, ShieldAlert, Truck, Flame } from 'lucide-react'
import { int, m2, pct } from '../../../lib/format'

const SEVERITY_STYLE = {
  none:     { label: 'No accident',  bg: 'bg-emerald-50',  border: 'border-emerald-200', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  minor:    { label: 'Minor',        bg: 'bg-yellow-50',   border: 'border-yellow-200',  text: 'text-yellow-800',  dot: 'bg-yellow-500' },
  moderate: { label: 'Moderate',     bg: 'bg-orange-50',   border: 'border-orange-200',  text: 'text-orange-700',  dot: 'bg-orange-500' },
  major:    { label: 'Major',        bg: 'bg-red-50',      border: 'border-red-200',     text: 'text-red-700',     dot: 'bg-red-500' },
}
const ORDER = ['none', 'minor', 'moderate', 'major']

const RESOURCES = [
  { key: 'ambulances',   label: 'Ambulances', icon: Stethoscope },
  { key: 'police_units', label: 'Police',     icon: Shield },
  { key: 'fire_trucks',  label: 'Fire',       icon: Flame },
  { key: 'smurd',        label: 'SMURD',      icon: ShieldAlert },
  { key: 'tow_trucks',   label: 'Tow trucks', icon: Truck },
]

export default function CarCrashCard({ data }) {
  if (!data) return null
  const idx = ORDER.indexOf(data.severity)
  const style = SEVERITY_STYLE[data.severity] ?? SEVERITY_STYLE.none

  return (
    <Card padding="md" tone="crash" className="animate-fade-up">
      <CardHeader
        title="Car-crash detection"
        subtitle="YOLOv8 · Accident-Detection"
        icon={Car}
        accent="bg-zinc-100 text-zinc-700"
      />

      {/* Severity strip */}
      <div className={`rounded-xl border p-4 mb-4 ${style.bg} ${style.border}`}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-[11px] uppercase tracking-wider font-medium text-slate-600">Severity</span>
          <span className={`text-sm font-semibold ${style.text}`}>{style.label}</span>
        </div>
        <div className="flex gap-1.5">
          {ORDER.map((level, i) => (
            <div key={level} className={`flex-1 h-1.5 rounded-full transition-colors ${i <= idx ? SEVERITY_STYLE[level].dot : 'bg-white/70'}`} />
          ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-slate-500 font-medium">
          {ORDER.map(level => <span key={level} className="capitalize">{level}</span>)}
        </div>
      </div>

      {/* Area + count metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-xl bg-white border border-zinc-200 p-4">
          <span className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Accident area</span>
          <p className="font-mono-num text-2xl font-semibold text-zinc-800 mt-1">{pct(data.accident_area_pct, 1)}</p>
          <div className="h-1.5 mt-2 bg-zinc-100 rounded-full overflow-hidden">
            <div className="h-full bg-zinc-500 rounded-full transition-[width] duration-500" style={{ width: `${Math.min(100, data.accident_area_pct)}%` }} />
          </div>
        </div>
        <div className="rounded-xl bg-white border border-zinc-200 p-4">
          <span className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Detections</span>
          <p className="font-mono-num text-2xl font-semibold text-zinc-800 mt-1">{int(data.accident_count)}</p>
          <p className="text-xs text-slate-500 mt-2">accident region{data.accident_count === 1 ? '' : 's'} found</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <Metric label="Estimated ground area" value={m2(data.estimated_area_m2)} hint="@ 80m altitude · 60° FOV" />
        <Metric label="Top confidence" value={data.detections?.length ? `${(Math.max(...data.detections.map(d => d.confidence)) * 100).toFixed(1)}%` : '—'} />
      </div>

      {/* Recommended response */}
      <div className="border-t border-zinc-200 pt-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-wider text-slate-600 font-medium">Recommended response</p>
          <span className="text-[10px] text-slate-400">heuristic · not dispatch-grade</span>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {RESOURCES.map(({ key, label, icon: Icon }) => (
            <div key={key} className="flex flex-col items-center text-center p-2.5 rounded-lg bg-white border border-slate-200">
              <Icon className="size-4 text-slate-600 mb-1" />
              <p className="font-mono-num text-base font-semibold text-slate-900">{int(data.resources?.[key])}</p>
              <p className="text-[10px] text-slate-500 leading-tight">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
