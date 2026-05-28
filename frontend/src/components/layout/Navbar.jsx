import { NavLink, Link } from 'react-router-dom'
import clsx from 'clsx'
import { Shield, ScanLine, Radio, LayoutGrid, Info as InfoIcon } from 'lucide-react'

/** Nav item with optional "live" pulse — used to mark the operator-critical
 *  Monitor route so it visually stands apart from the supporting pages. */
function Item({ to, children, icon: Icon, primary = false, end = true }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => clsx(
        'inline-flex items-center gap-1.5 rounded-lg text-sm font-medium transition-colors',
        primary ? 'px-3 py-1.5' : 'px-3 py-1.5',
        isActive
          ? (primary ? 'bg-rose-50 text-rose-700' : 'bg-indigo-50 text-indigo-700')
          : (primary ? 'text-rose-700 hover:bg-rose-50' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'),
      )}
    >
      {primary && <span className="relative flex size-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
        <span className="relative inline-flex size-2 rounded-full bg-rose-500" />
      </span>}
      {Icon && <Icon className="size-4" />}
      {children}
    </NavLink>
  )
}

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="size-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-sm">
            <Shield className="size-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="font-semibold text-slate-900 tracking-tight">RAID</span>
          <span className="text-xs text-slate-400 hidden sm:inline">— Real-time Aerial Incident Detection</span>
        </Link>
        <nav className="flex items-center gap-1">
          <Item to="/" icon={Radio} primary>Monitor</Item>
          <span className="w-px h-5 bg-slate-200 mx-1" aria-hidden />
          <Item to="/analyze" icon={ScanLine}>Analyze</Item>
          <Item to="/overview" icon={LayoutGrid}>Overview</Item>
          <Item to="/about" icon={InfoIcon}>About</Item>
        </nav>
      </div>
    </header>
  )
}
