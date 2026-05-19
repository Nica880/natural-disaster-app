import clsx from 'clsx'
import { Info, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'

const TONES = {
  info:    { c: 'bg-blue-50 border-blue-200 text-blue-900',         icon: Info,           iconC: 'text-blue-600' },
  warning: { c: 'bg-yellow-50 border-yellow-200 text-yellow-900',   icon: AlertTriangle,  iconC: 'text-yellow-600' },
  success: { c: 'bg-emerald-50 border-emerald-200 text-emerald-900',icon: CheckCircle2,   iconC: 'text-emerald-600' },
  error:   { c: 'bg-red-50 border-red-200 text-red-900',            icon: XCircle,        iconC: 'text-red-600' },
}

export default function Alert({ tone = 'info', title, children, className }) {
  const t = TONES[tone]
  const Icon = t.icon
  return (
    <div className={clsx('rounded-xl border px-4 py-3 flex gap-3 items-start', t.c, className)}>
      <Icon className={clsx('size-5 shrink-0 mt-0.5', t.iconC)} />
      <div className="flex-1">
        {title && <p className="font-medium text-sm leading-tight mb-0.5">{title}</p>}
        <div className="text-sm leading-snug opacity-90">{children}</div>
      </div>
    </div>
  )
}
