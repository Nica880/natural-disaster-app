import Card, { CardHeader } from '../../ui/Card'
import Metric from '../../ui/Metric'
import Badge from '../../ui/Badge'
import AnnotatedImage from '../AnnotatedImage'
import { ScanSearch, Users, Car, Building2 } from 'lucide-react'
import { int, m2, pct } from '../../../lib/format'

export default function DetectCard({ data, originalSrc, showOverlay = true }) {
  if (!data) return null
  const topClasses = Object.entries(data.class_counts || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)

  return (
    <Card padding="md" className="animate-fade-up">
      <CardHeader
        title="Object inventory"
        subtitle="YOLOv8 · Open Images V7"
        icon={ScanSearch}
        accent="bg-slate-100 text-slate-700"
      />

      <AnnotatedImage
        src={data.annotated_image}
        originalSrc={originalSrc}
        showOverlay={showOverlay}
        alt="Detected objects"
      />

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
          <Users className="size-5 text-slate-600 shrink-0" />
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">People</p>
            <p className="font-mono-num font-semibold text-slate-900">{int(data.people)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
          <Car className="size-5 text-slate-600 shrink-0" />
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Vehicles</p>
            <p className="font-mono-num font-semibold text-slate-900">{int(data.vehicles)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
          <Building2 className="size-5 text-slate-600 shrink-0" />
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Buildings</p>
            <p className="font-mono-num font-semibold text-slate-900">{int(data.buildings)}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-slate-100">
        <Metric label="Total objects" value={int(data.objects_detected)} />
        <Metric label="Image coverage" value={pct(data.area_percent, 1)} hint="bounding-box area / image" />
        <Metric label="Estimated footprint" value={m2(data.estimated_area_m2)} hint="per-class real-world priors" />
      </div>

      {topClasses.length > 0 && (
        <div>
          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-medium mb-2">Detected classes</p>
          <div className="flex flex-wrap gap-1.5">
            {topClasses.map(([cls, count]) => (
              <Badge key={cls} tone="slate">
                {cls} <span className="font-mono-num text-slate-500">· {count}</span>
              </Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
