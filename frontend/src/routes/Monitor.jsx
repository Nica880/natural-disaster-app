import { useEffect, useState } from 'react'
import { Bell, BellRing, Radio } from 'lucide-react'

import { api } from '../services/api'
import { playAlert, requestNotificationPermission, showNotification } from '../lib/alert'
import IncidentCard from '../components/monitor/IncidentCard'
import IncidentDetail from '../components/monitor/IncidentDetail'
import IncidentHistory from '../components/monitor/IncidentHistory'

/** Live operator dashboard. Active incidents stream in via SSE (with a chime
 *  + notification on each new one); closed incidents live in the history
 *  dropdown. Clicking any incident opens the shared detail modal. */
export default function Monitor() {
  const [incidents, setIncidents] = useState([])
  const [connected, setConnected] = useState(false)
  const [historyRefresh, setHistoryRefresh] = useState(0)
  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  )

  // Modal source: `openId` is the incident being viewed. Active incidents are
  // read live from `incidents` (so the modal updates as frames arrive); a
  // history incident is fetched on demand into `fetched`.
  const [openId, setOpenId] = useState(null)
  const [fetched, setFetched] = useState(null)
  const detail = incidents.find(i => i.id === openId)
    || (fetched && fetched.id === openId ? fetched : null)

  useEffect(() => {
    requestNotificationPermission()
    const t = setInterval(() => {
      if (typeof Notification !== 'undefined') setNotifPermission(Notification.permission)
    }, 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const es = api.streamIncidents()
    es.onopen  = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (e) => {
      const { type, incident } = JSON.parse(e.data)
      if (type === 'dismiss') setHistoryRefresh(n => n + 1)  // it just entered history
      setIncidents(prev => {
        if (type === 'dismiss') return prev.filter(i => i.id !== incident.id)
        const without = prev.filter(i => i.id !== incident.id)
        // Alert only on live `create` events (not snapshot replay or updates).
        if (type === 'create') {
          playAlert()
          showNotification(
            `${incident.disaster_type} detected`,
            `${incident.camera_id} · ${incident.location || 'unknown location'}`,
          )
        }
        return [incident, ...without]
      })
    }
    return () => es.close()
  }, [])

  const openIncident = (id) => { setFetched(null); setOpenId(id) }

  const openHistoryIncident = (id) => {
    api.getIncident(id)
      .then(full => { setFetched(full); setOpenId(id) })
      .catch(() => {})
  }

  const closeModal = () => { setOpenId(null); setFetched(null) }

  const onDismiss = (id) => {
    api.dismissIncident(id)
    if (openId === id) closeModal()
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 uppercase tracking-wider font-medium mb-2">
            <Radio className="size-3.5" />
            Operations
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Live monitor</h1>
          <p className="text-slate-600 mt-1">
            Incidents raised by connected cameras. Click any card for evidence frames, recommended units, and the location.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <NotifBadge permission={notifPermission} />
          <ConnectionBadge connected={connected} />
        </div>
      </header>

      {incidents.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid lg:grid-cols-2 gap-4">
          {incidents.map(inc => (
            <IncidentCard key={inc.id} incident={inc}
                          onOpen={() => openIncident(inc.id)}
                          onDismiss={() => onDismiss(inc.id)} />
          ))}
        </div>
      )}

      <IncidentHistory refreshSignal={historyRefresh} onOpen={openHistoryIncident} />

      {detail && (
        <IncidentDetail
          key={detail.id}
          incident={detail}
          onClose={closeModal}
          onDismiss={() => onDismiss(detail.id)}
        />
      )}
    </div>
  )
}

function ConnectionBadge({ connected }) {
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
      connected ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'
    }`}>
      <span className={`size-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
      {connected ? 'Connected' : 'Disconnected'}
    </div>
  )
}

function NotifBadge({ permission }) {
  if (permission === 'granted') {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-indigo-50 text-indigo-700">
        <BellRing className="size-3.5" />
        Notifications on
      </div>
    )
  }
  if (permission === 'denied' || permission === 'unsupported') return null
  return (
    <button onClick={requestNotificationPermission}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors">
      <Bell className="size-3.5" />
      Enable notifications
    </button>
  )
}

function EmptyState() {
  return (
    <div className="border border-dashed border-slate-300 rounded-2xl p-10 text-center bg-white/60">
      <Bell className="size-8 text-slate-400 mx-auto mb-3" />
      <p className="text-slate-600 font-medium">No active incidents</p>
      <p className="text-sm text-slate-500 mt-1">
        Cameras are quiet. Incidents appear here in real time, with an audible alert and a desktop notification.
      </p>
    </div>
  )
}
