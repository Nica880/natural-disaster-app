import { AlertTriangle, Flame, Droplets, Car, Wind, Activity, ShieldQuestion, Info } from 'lucide-react'
import AnnotatedImage from './AnnotatedImage'
import { conf, m2, pct } from '../../lib/format'

const TYPE_STYLE = {
  Wildfire:   { tone: 'fire',    icon: Flame,    bg: 'from-orange-600 to-red-600' },
  Flood:      { tone: 'flood',   icon: Droplets, bg: 'from-blue-600 to-indigo-700' },
  'Car Crash':{ tone: 'crash',   icon: Car,      bg: 'from-zinc-700 to-zinc-900' },
  Cyclone:    { tone: 'cyclone', icon: Wind,     bg: 'from-violet-600 to-purple-700' },
  Earthquake: { tone: 'quake',   icon: Activity, bg: 'from-amber-600 to-orange-700' },
  Uncertain:  { tone: 'slate',   icon: ShieldQuestion, bg: 'from-slate-600 to-slate-800' },
}

export default function VerdictCard({ verdict, originalSrc, showOverlay = true }) {
  if (!verdict) return null
  const style = TYPE_STYLE[verdict.disaster_type] ?? TYPE_STYLE.Uncertain
  const Icon = style.icon
  const hasImage = (showOverlay && verdict.annotated_image) || originalSrc

  return (
    <div className="rounded-2xl overflow-hidden border border-slate-200 shadow-sm bg-white animate-fade-up">
      {/* Headline strip */}
      <div className={`bg-gradient-to-br ${style.bg} text-white px-6 py-5`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="size-12 rounded-xl bg-white/15 flex items-center justify-center backdrop-blur-sm">
              <Icon className="size-6" strokeWidth={2.2} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider opacity-80">Verdict</p>
              <h2 className="text-2xl font-bold leading-tight">{verdict.disaster_type}</h2>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase tracking-wider opacity-70">Classifier</p>
            <p className="font-mono-num text-lg font-semibold">{conf(verdict.confidence)}</p>
          </div>
        </div>
        <p className="mt-4 text-sm text-white/90 leading-relaxed">{verdict.summary}</p>
      </div>

      {/* Image — annotated when overlays are on, original otherwise */}
      {hasImage && (
        <div className="bg-slate-100">
          <AnnotatedImage
            src={verdict.annotated_image}
            originalSrc={originalSrc}
            showOverlay={showOverlay}
            alt={verdict.disaster_type}
          />
        </div>
      )}

      {/* Key metrics */}
      {(verdict.affected_area_pct != null || verdict.affected_area_m2 != null) && (
        <div className="grid grid-cols-2 gap-px bg-slate-200 border-t border-slate-200">
          <div className="bg-white p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Frame coverage</p>
            <p className="font-mono-num text-2xl font-semibold text-slate-900 mt-1">
              {verdict.affected_area_pct != null ? pct(verdict.affected_area_pct, 1) : '—'}
            </p>
          </div>
          <div className="bg-white p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Estimated ground area</p>
            <p className="font-mono-num text-2xl font-semibold text-slate-900 mt-1">
              {verdict.affected_area_m2 != null ? m2(verdict.affected_area_m2) : '—'}
            </p>
          </div>
        </div>
      )}

      {/* Severity + resources */}
      {(verdict.severity || verdict.resources) && (
        <div className="px-6 py-4 border-t border-slate-200 flex flex-wrap items-center gap-x-6 gap-y-2">
          {verdict.severity && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Severity</span>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold capitalize">
                {verdict.severity}
              </span>
            </div>
          )}
          {verdict.resources && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">Dispatch</span>
              {Object.entries(verdict.resources)
                .filter(([, v]) => v > 0)
                .map(([k, v]) => (
                  <span key={k} className="font-mono-num">
                    <strong className="text-slate-900">{v}</strong> {k.replaceAll('_', ' ')}
                  </span>
                ))}
              {Object.values(verdict.resources).every(v => !v) && (
                <span className="italic text-slate-400">none needed</span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Notes */}
      {verdict.notes?.length > 0 && (
        <div className="px-6 py-3 border-t border-slate-200 bg-amber-50 flex items-start gap-2">
          <Info className="size-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-900 space-y-1">
            {verdict.notes.map((n, i) => <p key={i}>{n}</p>)}
          </div>
        </div>
      )}
    </div>
  )
}
