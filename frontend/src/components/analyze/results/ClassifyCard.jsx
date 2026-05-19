import Card, { CardHeader } from '../../ui/Card'
import Badge from '../../ui/Badge'
import ProgressBar from '../../ui/ProgressBar'
import { metaFor } from '../../../lib/disasters'
import { conf } from '../../../lib/format'

const BAR_COLOR = {
  fire:    'bg-orange-500',
  flood:   'bg-blue-500',
  cyclone: 'bg-violet-500',
  quake:   'bg-amber-500',
  crash:   'bg-zinc-500',
}

export default function ClassifyCard({ data }) {
  if (!data) return null
  const meta = metaFor(data.predicted_class)
  const Icon = meta.icon

  // sort probabilities descending so the winner is at top
  const probs = Object.entries(data.probabilities).sort(([, a], [, b]) => b - a)

  return (
    <Card padding="md" className="animate-fade-up">
      <CardHeader
        title="Scene classification"
        subtitle="ResNet-18 · 5 disaster classes"
        icon={Icon}
        accent="bg-indigo-100 text-indigo-700"
        action={<Badge tone="indigo" dot="bg-indigo-500">Top-1</Badge>}
      />

      <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white p-5 mb-4">
        <p className="text-xs uppercase tracking-wider text-indigo-200">Predicted</p>
        <p className="text-2xl font-semibold mt-1">{meta.label}</p>
        <p className="text-sm text-indigo-100 mt-1">{meta.blurb}</p>
        <div className="mt-3 inline-flex items-center gap-2 bg-white/15 px-2.5 py-1 rounded-lg text-sm">
          <span className="size-1.5 rounded-full bg-emerald-300" />
          <span className="font-mono-num">{conf(data.confidence)}</span>
          <span className="text-indigo-200">confidence</span>
        </div>
      </div>

      <div className="space-y-0.5">
        {probs.map(([cls, p]) => {
          const m = metaFor(cls)
          return (
            <ProgressBar
              key={cls}
              label={m.label}
              value={p}
              color={BAR_COLOR[m.token] || 'bg-slate-400'}
              secondary={`${(p * 100).toFixed(2)}%`}
            />
          )
        })}
      </div>
    </Card>
  )
}
