import clsx from 'clsx'

export default function Card({ children, className, padding = 'md', tone = 'default' }) {
  const tones = {
    default: 'bg-white border-slate-200',
    fire:    'bg-orange-50/40 border-orange-200',
    flood:   'bg-blue-50/40 border-blue-200',
    cyclone: 'bg-violet-50/40 border-violet-200',
    quake:   'bg-amber-50/40 border-amber-200',
    crash:   'bg-zinc-50/60 border-zinc-200',
    accent:  'bg-indigo-50/40 border-indigo-200',
    muted:   'bg-slate-50 border-slate-200',
  }
  const paddings = {
    none: '',
    sm:   'p-4',
    md:   'p-6',
    lg:   'p-8',
  }
  return (
    <div className={clsx('rounded-2xl border shadow-sm', tones[tone], paddings[padding], className)}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, icon: Icon, accent, action }) {
  return (
    <div className="flex items-start justify-between gap-3 mb-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={clsx('flex items-center justify-center rounded-xl size-10 shrink-0', accent || 'bg-slate-100 text-slate-700')}>
            <Icon className="size-5" />
          </div>
        )}
        <div>
          <h3 className="text-base font-semibold text-slate-900 leading-tight">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}
