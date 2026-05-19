/**
 * Disaster-type metadata. One source of truth for colors, icons, labels
 * used by all result components.
 *
 * Keys match the backend ResNet18 class labels exactly.
 */
import { Flame, Droplets, Wind, Activity, Car, AlertTriangle } from 'lucide-react'

export const DISASTER_META = {
  Wildfire: {
    label: 'Wildfire',
    icon: Flame,
    token: 'fire',
    blurb: 'Open-flame / smoke detected.',
  },
  Flood: {
    label: 'Flood',
    icon: Droplets,
    token: 'flood',
    blurb: 'Standing water / inundation.',
  },
  Cyclone: {
    label: 'Cyclone',
    icon: Wind,
    token: 'cyclone',
    blurb: 'Storm rotation / wind damage.',
  },
  Earthquake: {
    label: 'Earthquake',
    icon: Activity,
    token: 'quake',
    blurb: 'Structural collapse / rubble.',
  },
  'Car Crash': {
    label: 'Car Crash',
    icon: Car,
    token: 'crash',
    blurb: 'Vehicle accident scene.',
  },
}

export function metaFor(name) {
  return DISASTER_META[name] || {
    label: name,
    icon: AlertTriangle,
    token: 'crash',
    blurb: '',
  }
}

/** Severity → palette token (light/dark text/bg/border).
 *  Tailwind-safe: full classnames so the compiler picks them up. */
export const SEVERITY_STYLE = {
  none:    { label: 'No fire',  bg: 'bg-emerald-50',  border: 'border-emerald-200', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  small:   { label: 'Small',    bg: 'bg-yellow-50',   border: 'border-yellow-200',  text: 'text-yellow-800',  dot: 'bg-yellow-500' },
  medium:  { label: 'Medium',   bg: 'bg-orange-50',   border: 'border-orange-200',  text: 'text-orange-700',  dot: 'bg-orange-500' },
  large:   { label: 'Large',    bg: 'bg-red-50',      border: 'border-red-200',     text: 'text-red-700',     dot: 'bg-red-500' },
  extreme: { label: 'Extreme',  bg: 'bg-rose-100',    border: 'border-rose-300',    text: 'text-rose-800',    dot: 'bg-rose-600' },
}
