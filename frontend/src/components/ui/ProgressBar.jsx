import clsx from 'clsx'

/**
 * Compact bar for showing a 0-100% value with label + numeric.
 * Used in probability lists and area coverage indicators.
 */
export default function ProgressBar({ label, value, max = 1, color = 'bg-indigo-500', secondary }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-sm text-slate-700 w-28 truncate">{label}</span>
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-[width] duration-500 ease-out', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-mono-num text-xs text-slate-600 w-14 text-right tabular-nums">
        {secondary ?? `${pct.toFixed(1)}%`}
      </span>
    </div>
  )
}
