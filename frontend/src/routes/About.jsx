import { Brain, ScanSearch, Droplets, Flame, Server, Cpu, Database, Layers, ExternalLink } from 'lucide-react'
import Card, { CardHeader } from '../components/ui/Card'
import Badge from '../components/ui/Badge'

const ACCENT = {
  indigo: 'bg-indigo-100 text-indigo-700',
  slate:  'bg-slate-100 text-slate-700',
  fire:   'bg-orange-100 text-orange-700',
  flood:  'bg-blue-100 text-blue-700',
}

const MODELS = [
  {
    icon: Brain,    accent: ACCENT.indigo, label: 'Scene classifier',
    model: 'ResNet-18',
    dataset: 'Roboflow “Natural Disasters” · 5 classes · ~9.6 k images',
    output: '5-way probability distribution',
    href: 'https://universe.roboflow.com/yolo-classification/natural-disasters',
  },
  {
    icon: ScanSearch, accent: ACCENT.slate, label: 'Generic detector',
    model: 'YOLOv8n',
    dataset: 'Open Images V7 · 601 classes',
    output: 'Counts of people / vehicles / buildings + footprint priors',
    href: 'https://storage.googleapis.com/openimages/web/index.html',
  },
  {
    icon: Flame,    accent: ACCENT.fire,   label: 'Fire & smoke detector',
    model: 'YOLOv8s',
    dataset: 'D-Fire · ~21 k images · fire + smoke bbox',
    output: 'Bounding boxes, severity tier, resource recommendation',
    href: 'https://github.com/gaiasd/DFireDataset',
  },
  {
    icon: Droplets, accent: ACCENT.flood,  label: 'Flood segmenter',
    model: 'YOLOv8n-seg',
    dataset: '“Flood Amateur Video” semantic segmentation set',
    output: 'Pixel-level flooded-area mask + scene class counts',
    href: 'https://data.mendeley.com/datasets/3kzr8mt8s2/5',
  },
]

const STACK = [
  { icon: Cpu,      label: 'Frontend',  detail: 'React 19 · Tailwind v4 · lucide icons' },
  { icon: Server,   label: 'Backend',   detail: 'FastAPI · Pydantic v2 · Ultralytics YOLOv8' },
  { icon: Database, label: 'Storage',   detail: 'PostgreSQL (planned · drone metadata + analyses)' },
  { icon: Layers,   label: 'Pipelines', detail: 'Modular services per model · DI in FastAPI' },
]

export default function About() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12 space-y-10">
      <section>
        <Badge tone="indigo">About</Badge>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
          A modular pipeline for drone-image disaster triage
        </h1>
        <p className="mt-3 text-slate-600 max-w-3xl leading-relaxed">
          Aegis is the dissertation prototype of <strong>Mihăilă Nicanor</strong>
          (UPB · Faculty of Automatic Control and Computers · E-Government track,
          coord. Prof. Dr. Ing. Nirvana Popescu). The system combines a scene
          classifier with three specialised detectors so that aerial photos of an
          incident can be turned into a structured response brief in seconds —
          disaster type, affected area, people and structures at risk, and an
          initial draft of the resources to dispatch.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Models</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {MODELS.map(m => (
            <Card key={m.label} padding="md">
              <CardHeader
                title={m.label}
                subtitle={m.model}
                icon={m.icon}
                accent={m.accent}
              />
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-[11px] uppercase tracking-wider text-slate-500">Dataset</dt>
                  <dd className="text-slate-800">{m.dataset}</dd>
                </div>
                <div>
                  <dt className="text-[11px] uppercase tracking-wider text-slate-500">Output</dt>
                  <dd className="text-slate-800">{m.output}</dd>
                </div>
                {m.href && (
                  <a href={m.href} target="_blank" rel="noopener noreferrer"
                     className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium mt-1">
                    Source <ExternalLink className="size-3" />
                  </a>
                )}
              </dl>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Stack</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {STACK.map(s => (
            <div key={s.label} className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 bg-white">
              <div className="size-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700">
                <s.icon className="size-4" />
              </div>
              <div>
                <p className="font-medium text-slate-900">{s.label}</p>
                <p className="text-sm text-slate-500">{s.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <p>
          <strong>Important — this is a didactic prototype.</strong> Resource
          recommendations are a coarse heuristic derived from area coverage and
          severity tier. Real dispatching depends on wind, water access, traffic
          and many other factors not modelled here. Don&apos;t use this for
          life-safety decisions.
        </p>
      </section>
    </div>
  )
}
