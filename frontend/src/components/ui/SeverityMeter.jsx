import clsx from 'clsx'
import { SEVERITY_STYLE } from '../../lib/disasters'

const ORDER = ['none', 'small', 'medium', 'large', 'extreme']

export default function SeverityMeter({ severity = 'none' }) {
  const idx = ORDER.indexOf(severity)
  const style = SEVERITY_STYLE[severity] ?? SEVERITY_STYLE.none

  return (
    <div className={clsx('rounded-xl border p-4', style.bg, style.border)}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] uppercase tracking-wider font-medium text-slate-600">Severity</span>
        <span className={clsx('text-sm font-semibold capitalize', style.text)}>
          {style.label}
        </span>
      </div>
      <div className="flex gap-1.5">
        {ORDER.map((level, i) => (
          <div
            key={level}
            className={clsx(
              'flex-1 h-1.5 rounded-full transition-colors',
              i <= idx ? SEVERITY_STYLE[level].dot : 'bg-white/70',
            )}
          />
        ))}
      </div>
      <div className="flex justify-between mt-2 text-[10px] text-slate-500 font-medium">
        {ORDER.map(level => (
          <span key={level} className="capitalize">{level}</span>
        ))}
      </div>
    </div>
  )
}
