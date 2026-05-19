import { GitBranch } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white/70 mt-20">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-slate-500">
        <p>
          Aegis · Master&apos;s thesis, UPB Faculty of Automatic Control and Computers ·
          coord. <span className="text-slate-700">Prof. Dr. Ing. Nirvana Popescu</span>
        </p>
        <a
          href="https://github.com/Nica880/natural-disaster-app"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 hover:text-slate-900 transition-colors"
        >
          <GitBranch className="size-4" />
          Source
        </a>
      </div>
    </footer>
  )
}
