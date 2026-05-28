/** Operator alert helpers — browser notifications + an audible chime.
 *
 *  The chime is synthesised at runtime via the Web Audio API, so there's
 *  no audio asset to ship. Notifications need user permission; if the
 *  user denies them, the chime still plays.
 */

let _ctx = null

function getAudioContext() {
  if (_ctx) return _ctx
  const Ctor = window.AudioContext || window.webkitAudioContext
  if (!Ctor) return null
  _ctx = new Ctor()
  return _ctx
}

/** Two-tone alert chime: 880 Hz → 660 Hz, ~250 ms total. */
export function playAlert() {
  const ctx = getAudioContext()
  if (!ctx) return
  try {
    // AudioContext starts in 'suspended' state on some browsers until the
    // first user gesture. A nav-link click counts as a gesture, so by the
    // time we hit this on an SSE event the context should be running.
    if (ctx.state === 'suspended') ctx.resume()

    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain).connect(ctx.destination)

    const t = ctx.currentTime
    osc.frequency.setValueAtTime(880, t)
    osc.frequency.exponentialRampToValueAtTime(660, t + 0.18)
    gain.gain.setValueAtTime(0.001, t)
    gain.gain.exponentialRampToValueAtTime(0.2, t + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.25)

    osc.start(t)
    osc.stop(t + 0.3)
  } catch {
    // Don't let a broken audio context break the UI.
  }
}

export function requestNotificationPermission() {
  if (typeof Notification === 'undefined') return
  if (Notification.permission === 'default') Notification.requestPermission()
}

export function showNotification(title, body) {
  if (typeof Notification === 'undefined') return
  if (Notification.permission !== 'granted') return
  // `silent: true` because we play our own chime — avoids double-beeps.
  new Notification(title, { body, silent: true, tag: 'raid-incident' })
}
