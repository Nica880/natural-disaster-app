import { Brain, ScanSearch, Droplets, Flame, Play } from 'lucide-react'
import Button from '../ui/Button'

const ACTIONS = [
  { key: 'classify', label: 'Classify',       icon: Brain,      variant: 'primary',   hint: 'ResNet-18 scene class' },
  { key: 'detect',   label: 'Objects',        icon: ScanSearch, variant: 'secondary', hint: 'YOLO · Open Images V7' },
  { key: 'flood',    label: 'Flood mask',     icon: Droplets,   variant: 'flood',     hint: 'YOLOv8-seg' },
  { key: 'fire',     label: 'Fire & smoke',   icon: Flame,      variant: 'fire',      hint: 'YOLOv8 · D-Fire' },
]

export default function ActionGroup({ disabled, loading, onRun, onRunAll }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Run analyses</p>
        <Button
          size="sm"
          variant="ghost"
          icon={Play}
          loading={loading === '__all__'}
          disabled={disabled}
          onClick={onRunAll}
        >
          Run all
        </Button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {ACTIONS.map(a => (
          <button
            key={a.key}
            type="button"
            disabled={disabled || loading != null}
            onClick={onRun(a.key)}
            className="group text-left flex flex-col gap-1 p-3.5 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <div className="flex items-center gap-2">
              <a.icon className={`size-4 ${
                a.key === 'fire'  ? 'text-orange-600' :
                a.key === 'flood' ? 'text-blue-600' :
                a.key === 'classify' ? 'text-indigo-600' :
                'text-slate-700'
              }`} />
              <span className="font-medium text-sm text-slate-900">{a.label}</span>
              {loading === a.key && <span className="ml-auto text-[10px] text-indigo-600 animate-pulse">running…</span>}
            </div>
            <span className="text-[11px] text-slate-500">{a.hint}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
