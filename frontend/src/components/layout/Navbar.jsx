import { NavLink, Link } from 'react-router-dom'
import clsx from 'clsx'
import { Shield, ScanLine, Info as InfoIcon } from 'lucide-react'

function Item({ to, children, icon: Icon }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) => clsx(
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
        isActive
          ? 'bg-indigo-50 text-indigo-700'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
      )}
    >
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
          <span className="font-semibold text-slate-900 tracking-tight">Aegis</span>
          <span className="text-xs text-slate-400 hidden sm:inline">— Disaster Image Intelligence</span>
        </Link>
        <nav className="flex items-center gap-1">
          <Item to="/" icon={Shield}>Overview</Item>
          <Item to="/analyze" icon={ScanLine}>Analyze</Item>
          <Item to="/about" icon={InfoIcon}>About</Item>
        </nav>
      </div>
    </header>
  )
}
