import { Link } from 'react-router-dom'
import { ArrowRight, Flame, Droplets, Wind, Activity, Car, Cpu, ScanLine, ShieldAlert } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'

const CATEGORIES = [
  { name: 'Wildfire',   icon: Flame,    tone: 'fire'    },
  { name: 'Flood',      icon: Droplets, tone: 'flood'   },
  { name: 'Cyclone',    icon: Wind,     tone: 'cyclone' },
  { name: 'Earthquake', icon: Activity, tone: 'quake'   },
  { name: 'Car crash',  icon: Car,      tone: 'crash'   },
]

const STAGES = [
  {
    icon: ScanLine,
    title: 'Capture',
    body: 'A drone (or operator) uploads an aerial image of an incident scene.',
  },
  {
    icon: Cpu,
    title: 'Analyse',
    body: 'Four specialised models run in parallel: scene classifier, generic object detector, fire & smoke detector, flood segmenter.',
  },
  {
    icon: ShieldAlert,
    title: 'Decide',
    body: 'The dashboard surfaces type, severity, affected area, and a draft resource-allocation recommendation.',
  },
]

export default function Home() {
  return (
    <div className="bg-grid">
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-12">
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7">
            <Badge tone="indigo" className="mb-5">
              <span className="size-1.5 rounded-full bg-indigo-500" />
              Master&apos;s thesis · UPB · 2026
            </Badge>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 leading-[1.05]">
              Faster eyes on the ground,<br />
              <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                better decisions in the air.
              </span>
            </h1>
            <p className="mt-5 text-lg text-slate-600 max-w-2xl leading-relaxed">
              Aegis turns drone-captured photos of disasters into a structured report
              in under a second — disaster type, affected area, people and structures
              at risk, and a draft response plan.
            </p>
            <div className="mt-7 flex items-center gap-3">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 bg-indigo-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-indigo-700 shadow-sm transition-all"
              >
                Open the analyser <ArrowRight className="size-4" />
              </Link>
              <Link
                to="/about"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-700 hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200 transition-all"
              >
                How it works
              </Link>
            </div>

            <div className="mt-10 flex flex-wrap gap-2">
              {CATEGORIES.map(c => (
                <Badge key={c.name} tone={c.tone} icon={c.icon}>{c.name}</Badge>
              ))}
            </div>
          </div>

          {/* Right-hand visual: a fake "report card" preview */}
          <div className="lg:col-span-5">
            <Card padding="md" className="rotate-1 shadow-md">
              <div className="flex items-center justify-between mb-3">
                <Badge tone="fire" icon={Flame}>Wildfire</Badge>
                <span className="text-xs text-slate-500 font-mono-num">conf 92.4%</span>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="rounded-lg p-2.5 bg-orange-50 border border-orange-100">
                  <p className="text-[10px] uppercase tracking-wider text-orange-700">Fire area</p>
                  <p className="font-mono-num text-lg font-semibold text-orange-700">18.3%</p>
                </div>
                <div className="rounded-lg p-2.5 bg-slate-50 border border-slate-100">
                  <p className="text-[10px] uppercase tracking-wider text-slate-600">Smoke</p>
                  <p className="font-mono-num text-lg font-semibold text-slate-800">42.1%</p>
                </div>
                <div className="rounded-lg p-2.5 bg-emerald-50 border border-emerald-100">
                  <p className="text-[10px] uppercase tracking-wider text-emerald-700">~Area</p>
                  <p className="font-mono-num text-lg font-semibold text-emerald-700">1.8 ha</p>
                </div>
              </div>
              <div className="rounded-lg bg-red-50 border border-red-100 p-3 flex items-center gap-3">
                <div className="size-8 rounded-md bg-red-100 flex items-center justify-center text-red-600">
                  <ShieldAlert className="size-4" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-red-700 font-medium">Severity</p>
                  <p className="text-sm font-semibold text-red-800">Large — dispatch 4 trucks · 2 ambulances · 1 aerial</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid md:grid-cols-3 gap-4">
          {STAGES.map((s, i) => (
            <Card key={s.title} padding="md">
              <div className="flex items-center gap-2 mb-2">
                <span className="size-7 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-semibold">{i + 1}</span>
                <s.icon className="size-4 text-indigo-600" />
                <span className="font-semibold text-slate-900">{s.title}</span>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">{s.body}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
