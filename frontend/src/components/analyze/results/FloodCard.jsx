import Card, { CardHeader } from '../../ui/Card'
import Metric from '../../ui/Metric'
import AnnotatedImage from '../AnnotatedImage'
import { Droplets, Users, Car, Building2, Sprout } from 'lucide-react'
import { int, m2, pct } from '../../../lib/format'

export default function FloodCard({ data, showOverlay = true }) {
  if (!data) return null
  return (
    <Card padding="md" tone="flood" className="animate-fade-up">
      <CardHeader
        title="Flood segmentation"
        subtitle="YOLOv8n-seg · pixel-level mask"
        icon={Droplets}
        accent="bg-blue-100 text-blue-700"
      />

      {showOverlay && <AnnotatedImage src={data.annotated_image} alt="Flood segmentation mask" />}

      <div className="rounded-xl bg-white border border-blue-200 p-5 mb-4">
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-sm text-slate-600">Inundated area</span>
          <span className="font-mono-num text-3xl font-semibold text-blue-700 tabular-nums">
            {pct(data.flood_area_pct, 1)}
          </span>
        </div>
        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-[width] duration-500"
            style={{ width: `${Math.min(100, data.flood_area_pct ?? 0)}%` }}
          />
        </div>
        <p className="text-xs text-slate-500 mt-2">≈ {m2(data.flood_area_m2)} (assuming standard frame scale)</p>
      </div>

      <div className="grid grid-cols-4 gap-2">
        {[
          { icon: Building2, label: 'Buildings', value: data.buildings },
          { icon: Car,       label: 'Vehicles',  value: data.vehicles  },
          { icon: Users,     label: 'People',    value: data.people    },
          { icon: Sprout,    label: 'Plants',    value: data.plants    },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="p-3 rounded-xl bg-white/70 border border-blue-100 text-center">
            <Icon className="size-4 text-blue-600 mx-auto mb-1" />
            <p className="font-mono-num font-semibold text-slate-900">{int(value)}</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}
