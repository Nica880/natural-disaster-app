import Card, { CardHeader } from '../../ui/Card'
import Metric from '../../ui/Metric'
import SeverityMeter from '../../ui/SeverityMeter'
import AnnotatedImage from '../AnnotatedImage'
import { Flame, Truck, Stethoscope, Shield, ShieldAlert, Plane } from 'lucide-react'
import { int, m2, pct } from '../../../lib/format'

const RESOURCES = [
  { key: 'fire_trucks',   label: 'Fire trucks',  icon: Truck },
  { key: 'ambulances',    label: 'Ambulances',   icon: Stethoscope },
  { key: 'police_units',  label: 'Police',       icon: Shield },
  { key: 'smurd',         label: 'SMURD',        icon: ShieldAlert },
  { key: 'aerial_units',  label: 'Aerial',       icon: Plane },
]

export default function FireCard({ data, originalSrc, showOverlay = true }) {
  if (!data) return null

  return (
    <Card padding="md" tone="fire" className="animate-fade-up">
      <CardHeader
        title="Fire & smoke detection"
        subtitle="YOLOv8 · D-Fire dataset"
        icon={Flame}
        accent="bg-orange-100 text-orange-700"
      />

      <AnnotatedImage
        src={data.annotated_image}
        originalSrc={originalSrc}
        showOverlay={showOverlay}
        alt="Fire and smoke detections"
      />

      {/* Severity strip */}
      <div className="mb-4">
        <SeverityMeter severity={data.severity} />
      </div>

      {/* Area metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-xl bg-white border border-orange-200 p-4">
          <div className="flex items-baseline justify-between">
            <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">Fire area</span>
            <span className="text-xs text-slate-500 font-mono-num">{int(data.fire_count)} box</span>
          </div>
          <p className="font-mono-num text-2xl font-semibold text-orange-700 mt-1">{pct(data.fire_area_pct, 1)}</p>
          <div className="h-1.5 mt-2 bg-orange-100 rounded-full overflow-hidden">
            <div className="h-full bg-orange-500 rounded-full transition-[width] duration-500" style={{ width: `${Math.min(100, data.fire_area_pct)}%` }} />
          </div>
        </div>
        <div className="rounded-xl bg-white border border-slate-200 p-4">
          <div className="flex items-baseline justify-between">
            <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">Smoke area</span>
            <span className="text-xs text-slate-500 font-mono-num">{int(data.smoke_count)} box</span>
          </div>
          <p className="font-mono-num text-2xl font-semibold text-slate-700 mt-1">{pct(data.smoke_area_pct, 1)}</p>
          <div className="h-1.5 mt-2 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-slate-500 rounded-full transition-[width] duration-500" style={{ width: `${Math.min(100, data.smoke_area_pct)}%` }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <Metric label="Estimated ground area" value={m2(data.estimated_area_m2)} hint="@ 80m altitude · 60° FOV" />
        <Metric label="Detections" value={int(data.fire_count + data.smoke_count)} hint={`${data.fire_count} fire · ${data.smoke_count} smoke`} />
      </div>

      {/* Recommended response */}
      <div className="border-t border-orange-200 pt-4">
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
