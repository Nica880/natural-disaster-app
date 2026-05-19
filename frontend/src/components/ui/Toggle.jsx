import clsx from 'clsx'

/** Compact pill toggle. Used for the "show overlays" switch on the
 *  analyser page. Accessible: behaves like a button + aria-pressed. */
export default function Toggle({ checked, onChange, icon: Icon, label, hint, className }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={clsx(
        'flex items-center gap-3 px-3 py-2 rounded-xl border w-full text-left transition-all',
        checked
          ? 'bg-indigo-50 border-indigo-200 text-indigo-900 hover:bg-indigo-100'
          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50',
        className,
      )}
    >
      {Icon && (
        <div className={clsx(
          'size-7 rounded-lg flex items-center justify-center shrink-0',
          checked ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600',
        )}>
          <Icon className="size-4" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium leading-tight">{label}</p>
        {hint && <p className="text-[11px] text-slate-500 mt-0.5">{hint}</p>}
      </div>
      <div className={clsx(
        'relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors',
        checked ? 'bg-indigo-600' : 'bg-slate-300',
      )}>
        <span className={clsx(
          'inline-block size-4 rounded-full bg-white shadow translate-y-0.5 transition-transform',
          checked ? 'translate-x-[18px]' : 'translate-x-0.5',
        )} />
      </div>
    </button>
  )
}
