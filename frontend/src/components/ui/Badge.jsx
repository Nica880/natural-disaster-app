import clsx from 'clsx'

export default function Badge({ children, tone = 'slate', icon: Icon, className, dot }) {
  const tones = {
    slate:   'bg-slate-100 text-slate-700 border-slate-200',
    indigo:  'bg-indigo-50 text-indigo-700 border-indigo-200',
    fire:    'bg-orange-50 text-orange-700 border-orange-200',
    flood:   'bg-blue-50 text-blue-700 border-blue-200',
    cyclone: 'bg-violet-50 text-violet-700 border-violet-200',
    quake:   'bg-amber-50 text-amber-700 border-amber-200',
    crash:   'bg-zinc-100 text-zinc-700 border-zinc-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    danger:  'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
      tones[tone],
      className,
    )}>
      {dot && <span className={clsx('size-1.5 rounded-full', dot)} />}
      {Icon && <Icon className="size-3" />}
      {children}
    </span>
  )
}
