import clsx from 'clsx'
import { Loader2 } from 'lucide-react'

const VARIANTS = {
  primary:   'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300 shadow-sm',
  secondary: 'bg-white text-slate-700 border border-slate-200 hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50',
  ghost:     'bg-transparent text-slate-700 hover:bg-slate-100',
  fire:      'bg-orange-600 text-white hover:bg-orange-700 disabled:bg-orange-300 shadow-sm',
  flood:     'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300 shadow-sm',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2.5 text-sm gap-2',
  lg: 'px-5 py-3 text-base gap-2',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading,
  icon: Icon,
  className,
  disabled,
  ...rest
}) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-lg transition-all',
        'disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : Icon && <Icon className="size-4" />}
      {children}
    </button>
  )
}
