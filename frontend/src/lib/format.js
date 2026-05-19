/** Display helpers — keep numbers consistently formatted across the app. */

export const pct = (v, digits = 1) => `${Number(v ?? 0).toFixed(digits)}%`

export const m2 = (v) => {
  const n = Number(v ?? 0)
  if (n >= 10_000) return `${(n / 10_000).toFixed(2)} ha`
  if (n >= 1000)   return `${n.toFixed(0)} m²`
  return `${n.toFixed(1)} m²`
}

export const int = (v) => Number(v ?? 0).toLocaleString('en-US')

export const conf = (v) => `${(Number(v ?? 0) * 100).toFixed(1)}%`
