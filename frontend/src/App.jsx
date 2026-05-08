import { useEffect, useMemo, useState } from 'react'

import { I } from './components/Icons'
import LeftRail from './components/LeftRail'
import RightRail from './components/RightRail'
import FloorPlanV2 from './components/FloorPlanV2'
import Scrubber from './components/Scrubber'
import { useNeuroNest } from './hooks/useNeuroNest'
import IntegrationDock from './components/IntegrationDock'
import EnergySavings from './components/EnergySavings'
import AiTimeline from './components/AiTimeline'
import AiExplanation from './components/AiExplanation'
import DemoConsole from './components/DemoConsole'
import { getSystemDiagnostics } from './services/api'

function useClock() {
  const [clock, setClock] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return clock
}

function pad(n) { return String(n).padStart(2, '0') }

export default function App() {
  const { uiData, loading, toggleDevice, setMode, runScenario } = useNeuroNest()

  const [selectedRoom, setSelectedRoom] = useState('living')
  const [activeDecisionId, setActiveDecisionId] = useState(null)
  const [activeScenario, setActiveScenario] = useState('live')
  const [scenarioLoading, setScenarioLoading] = useState(null)
  const [toast, setToast] = useState(null)
  const [theme, setTheme] = useState('graphite')
  const [centerView, setCenterView] = useState('floorplan')
  const [diagnostics, setDiagnostics] = useState(null)

  const clock = useClock()

  // Apply theme to root
  useEffect(() => {
    document.documentElement.dataset.theme = theme === 'graphite' ? '' : theme
  }, [theme])

  // Diagnostics polling
  useEffect(() => {
    async function load() {
      try { setDiagnostics(await getSystemDiagnostics()) } catch {
        // Diagnostics are non-critical; keep the last known values.
      }
    }
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const active = diagnostics?.demo?.active
    if (active) setActiveScenario(active)
  }, [diagnostics])

  const showToast = (text, kind = 'info') => {
    setToast({ text, kind })
    setTimeout(() => setToast(null), 2400)
  }

  const sensors = useMemo(() => uiData?.sensors ?? {}, [uiData])
  const devices = useMemo(() => uiData?.devices ?? {}, [uiData])
  const mode = uiData?.mode ?? 'Auto'
  const alerts = useMemo(() => {
    const nextAlerts = {}
    for (const [roomId, s] of Object.entries(sensors)) {
      if (s.smoke) nextAlerts[roomId] = { type: 'smoke', message: 'Smoke detected' }
    }
    return nextAlerts
  }, [sensors])

  // Synthetic decisions based on live actuator state
  const decisions = useMemo(() => {
    if (!uiData) return []
    const result = []
    for (const [roomId, devList] of Object.entries(devices)) {
      for (const d of devList) {
        if (d.on) {
          result.push({
            id: `${d.id}-on`,
            room: roomId,
            kind: 'on',
            title: `${d.name} → On`,
            reason: `Device active in ${roomId}.`,
            tag: 'active',
            at: 'live',
            t: 0,
            trace: [
              { label: 'Device', text: `${d.name} is currently ON` },
              { label: 'Room', text: roomId },
            ],
          })
        }
      }
    }
    for (const [roomId, alert] of Object.entries(alerts)) {
      result.unshift({
        id: `alert-${roomId}`,
        room: roomId,
        kind: 'alert',
        title: `${roomId} alert`,
        reason: alert.message,
        tag: 'safety',
        at: 'now',
        t: 0,
        trace: [
          { label: 'Sensor', text: 'Smoke detected' },
          { label: 'Action', text: 'Alert raised' },
        ],
      })
    }
    return result.slice(0, 10)
  }, [uiData, devices, alerts])

  const climateSpark = useMemo(() => Array.from({ length: 60 }, (_, i) =>
    21.2 + Math.sin(i / 9) * 0.8 + Math.cos(i / 5) * 0.4
  ), [])

  const sparkData = useMemo(() => {
    const data = {}
    for (const [k, s] of Object.entries(sensors)) {
      const t = s.temp ?? 21
      const h = s.humidity ?? 45
      data[k] = {
        temp:     Array.from({ length: 24 }, (_, i) => t + Math.sin(i / 3) * 0.6 + Math.cos(i / 7) * 0.3),
        humidity: Array.from({ length: 24 }, (_, i) => h + Math.sin(i / 4) * 2 + Math.cos(i / 6) * 1.5),
      }
    }
    return data
  }, [sensors])

  const climate = {
    temp:     sensors.living?.temp ?? 21.4,
    humidity: sensors.living?.humidity ?? 42,
    outside:  14,
  }
  const totalDevicesOn = Object.values(devices).flat().filter(d => d.on).length
  const energy = { kwh: 8.4 + totalDevicesOn * 0.3, savings: 3.2 }
  const serviceList = diagnostics?.services ?? []
  const healthyServices = serviceList.filter(service => service.ok).length
  const serviceSummary = serviceList.length
    ? `${healthyServices}/${serviceList.length} services`
    : 'Checking services'

  const handleToggleDevice = (deviceId, roomId, deviceKey) => {
    toggleDevice(roomId, deviceKey)
    showToast(`${deviceKey} toggled`)
  }

  const handleSelectDecision = (id) => {
    const d = decisions.find(x => x.id === id)
    if (!d) return
    setActiveDecisionId(id === activeDecisionId ? null : id)
    setSelectedRoom(d.room)
  }

  const handleScenario = async (id) => {
    setActiveScenario(id)
    setScenarioLoading(id)
    try {
      const result = await runScenario(id)
      setDiagnostics(await getSystemDiagnostics())
      setActiveScenario(result?.active ?? id)
      showToast(
        id === 'live' ? 'Live data resumed' : `Scenario: ${id.replace(/_/g, ' ')}`,
        id === 'kitchen_smoke' ? 'alert' : 'info'
      )
    } catch {
      showToast('Scenario failed', 'alert')
    } finally {
      setScenarioLoading(null)
    }
  }

  const handleModeChange = (m) => {
    setMode(m)
    showToast(`Mode → ${m}`)
  }

  const clockStr = `${pad(clock.getHours())}:${pad(clock.getMinutes())}:${pad(clock.getSeconds())}`
  const activeDecision = decisions.find(d => d.id === activeDecisionId)
  const roomDevices = devices[selectedRoom] ?? []
  const roomAlert = alerts[selectedRoom]

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--bg)' }}>
        <div style={{ textAlign: 'center', color: 'var(--muted)' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--accent)', margin: '0 auto 16px', display: 'grid', placeItems: 'center', color: '#0e1110' }}>
            <I.Logo/>
          </div>
          Connecting…
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      {/* TOPBAR */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><I.Logo/></div>
          <div>
            <div className="brand-name">NeuroNest</div>
          </div>
          <span className="brand-sub mono">v2 · adaptive home</span>
        </div>

        <div className="topbar-center">
          {['Auto', 'Manual', 'Away'].map(m => (
            <button key={m}
              className={`mode-btn ${mode === m ? 'is-active' : ''}`}
              onClick={() => handleModeChange(m)}>
              {m === 'Auto' && <I.Sparkles/>}
              {m === 'Manual' && <I.Settings/>}
              {m === 'Away' && <I.Shield/>}
              {m}
            </button>
          ))}
        </div>

        <div className="topbar-right">
          <div className="health-pill">
            <span
              className="pulse-dot"
              style={Object.keys(alerts).length > 0 || (serviceList.length && healthyServices < serviceList.length) ? { background: 'var(--alert)' } : {}}
            />
            <span>{Object.keys(alerts).length > 0 ? `${Object.keys(alerts).length} alert(s)` : serviceSummary}</span>
          </div>
          <div className="clock">{clockStr}</div>
          {['graphite', 'midnight', 'paper'].map(t => (
            <button key={t} className="icon-btn" title={t} onClick={() => setTheme(t)}
              style={theme === t ? { borderColor: 'var(--accent)', color: 'var(--accent)' } : {}}>
              {t === 'graphite' && <I.Moon/>}
              {t === 'midnight' && <I.Shield/>}
              {t === 'paper' && <I.Sun/>}
            </button>
          ))}
          <button className="icon-btn" aria-label="Notifications"><I.Bell/></button>
        </div>
      </header>

      {/* LEFT */}
      <LeftRail
        climate={climate}
        energy={energy}
        decisions={decisions}
        activeDecisionId={activeDecisionId}
        onSelectDecision={handleSelectDecision}
        climateSpark={climateSpark}/>

      {/* CENTER */}
      <main className="center">
        <div className="stage-head">
          <div className="stage-title">
            <h1>Today</h1>
            <span className="stage-sub mono">
              {clock.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()}
            </span>
          </div>
          <div className="stage-actions">
            <div className="seg">
              <button className={centerView === 'floorplan' ? 'is-active' : ''} onClick={() => setCenterView('floorplan')}>Floor plan</button>
              <button className={centerView === 'energy' ? 'is-active' : ''} onClick={() => setCenterView('energy')}>Energy</button>
              <button className={centerView === 'integrations' ? 'is-active' : ''} onClick={() => setCenterView('integrations')}>Integrations</button>
            </div>
          </div>
        </div>

        <div className="plan-wrap" style={centerView !== 'floorplan' ? { overflow: 'auto' } : {}}>
          {centerView === 'floorplan' && (
            <FloorPlanV2
              sensors={sensors}
              selectedRoom={selectedRoom}
              onSelectRoom={setSelectedRoom}
              alerts={alerts}
              showFurniture={true}/>
          )}
          {centerView === 'energy' && (
            <div style={{ padding: 24, height: '100%', overflow: 'auto' }}>
              <EnergySavings overview={uiData?._raw} diagnostics={diagnostics}/>
            </div>
          )}
          {centerView === 'integrations' && (
            <div className="integration-view">
              <DemoConsole diagnostics={diagnostics} loading={scenarioLoading} onScenario={handleScenario}/>
              <AiExplanation overview={uiData?._raw} diagnostics={diagnostics} alerts={[]}/>
              <AiTimeline overview={uiData?._raw} diagnostics={diagnostics} alerts={[]}/>
              <IntegrationDock diagnostics={diagnostics} mode={mode}/>
            </div>
          )}
        </div>
      </main>

      {/* RIGHT */}
      <RightRail
        roomId={selectedRoom}
        sensors={sensors}
        alert={roomAlert}
        devices={roomDevices}
        onToggleDevice={handleToggleDevice}
        activeDecision={activeDecision}
        sparkData={sparkData[selectedRoom] || { temp: [], humidity: [] }}/>

      {/* FOOTER */}
      <Scrubber
        activeScenario={activeScenario}
        loadingScenario={scenarioLoading}
        onScenario={handleScenario}/>

      {/* Toast */}
      {toast && (
        <div className="nn-toast show">
          <span className="pulse-dot" style={toast.kind === 'alert' ? { background: 'var(--alert)' } : {}}/>
          {toast.text}
        </div>
      )}
    </div>
  )
}
