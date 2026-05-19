import clsx from 'clsx'

export default function Metric({ label, value, hint, accent = 'text-slate-900', className }) {
  return (
    <div className={clsx('flex flex-col gap-1', className)}>
      <span className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">{label}</span>
      <span className={clsx('font-mono-num text-xl font-semibold tabular-nums', accent)}>{value}</span>
      {hint && <span className="text-xs text-slate-500">{hint}</span>}
    </div>
  )
}
