import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import Header from './components/Header'
import StatsBar from './components/StatsBar'
import RoomGrid from './components/RoomGrid'
import ActivityFeed from './components/ActivityFeed'
import AiExplanation from './components/AiExplanation'
import AiTimeline from './components/AiTimeline'
import DemoConsole from './components/DemoConsole'
import EnergySavings from './components/EnergySavings'
import IntegrationDock from './components/IntegrationDock'
import RoomPanel from './components/RoomPanel'
import {
  controlActuator,
  getRoomHistory,
  getSystemOverview,
  getSystemDiagnostics,
  setSystemMode,
  triggerDemoScenario,
} from './services/api'

export const ROOM_CONFIG = {
  living_room: {
    zone: 'West Wing',
    sensors: ['temperature'],
    controls: [
      { key: 'light', label: 'Light' },
      { key: 'ac', label: 'AC' },
      { key: 'fan', label: 'Fan' },
    ],
  },
  bedroom: {
    zone: 'Private Zone',
    sensors: ['temperature'],
    controls: [
      { key: 'light', label: 'Light' },
      { key: 'ac', label: 'AC' },
      { key: 'fan', label: 'Fan' },
    ],
  },
  kitchen: {
    zone: 'Safety Critical',
    sensors: ['temperature', 'motion', 'smoke'],
    controls: [
      { key: 'light', label: 'Light' },
      { key: 'exhaust_fan', label: 'Exhaust Fan' },
    ],
  },
  bathroom: {
    zone: 'Humidity Watch',
    sensors: ['temperature', 'humidity', 'motion'],
    controls: [
      { key: 'light', label: 'Light' },
      { key: 'ventilation_fan', label: 'Ventilation Fan' },
    ],
  },
  hallway: {
    zone: 'Transit',
    sensors: ['motion'],
    controls: [{ key: 'light', label: 'Light' }],
  },
}

export const SENSOR_LABELS = {
  temperature: 'Temperature',
  humidity: 'Humidity',
  motion: 'Motion',
  smoke: 'Smoke',
}

export function formatRoomName(roomId = '') {
  return roomId
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

export function formatDeviceName(device = '') {
  return device
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

export function formatSensorValue(sensor, value) {
  if (value === undefined || value === null || value === '') return 'N/A'
  if (sensor === 'temperature') return `${Number(value).toFixed(1)} C`
  if (sensor === 'humidity') return `${Number(value).toFixed(0)}%`
  if (sensor === 'motion') return Number(value) > 0 ? 'Detected' : 'Clear'
  if (sensor === 'smoke') return Number(value) > 0 ? 'Alert' : 'Clear'
  return String(value)
}

function calculateAlerts(overview) {
  return (overview?.rooms ?? [])
    .filter((room) => Number(room.smoke) > 0)
    .map((room) => ({
      id: `${room.room_id}-smoke`,
      room: room.room_id,
      text: `${formatRoomName(room.room_id)} smoke detected`,
      level: 'critical',
    }))
}

function calculateHealth(overview, alerts) {
  const rooms = overview?.rooms ?? []
  if (!rooms.length) return 0

  const activeRooms = rooms.filter((room) => {
    const sensors = ROOM_CONFIG[room.room_id]?.sensors ?? []
    return sensors.some((sensor) => room[sensor] !== undefined && room[sensor] !== null)
  }).length

  return Math.max(0, Math.round((activeRooms / rooms.length) * 100) - alerts.length * 18)
}

function buildEvents(previousOverview, nextOverview) {
  if (!previousOverview || !nextOverview) return []

  const now = new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const events = []

  if (previousOverview.mode !== nextOverview.mode) {
    events.push({
      id: `mode-${Date.now()}-${nextOverview.mode}`,
      title: 'Mode Updated',
      text: `System mode switched to ${nextOverview.mode}`,
      time: now,
      level: nextOverview.mode === 'AI' ? 'ai' : 'info',
    })
  }

  for (const nextRoom of nextOverview.rooms ?? []) {
    const previousRoom = previousOverview.rooms?.find(
      (room) => room.room_id === nextRoom.room_id
    )
    if (!previousRoom) continue

    for (const [device, nextState] of Object.entries(nextRoom.actuators ?? {})) {
      const previousState = previousRoom.actuators?.[device]
      if (previousState && previousState !== nextState) {
        events.push({
          id: `actuator-${nextRoom.room_id}-${device}-${Date.now()}`,
          title: formatRoomName(nextRoom.room_id),
          text: `${formatDeviceName(device)} changed to ${nextState}`,
          time: now,
          level: 'info',
        })
      }
    }

    for (const sensor of ['smoke', 'motion']) {
      const previousValue = Number(previousRoom[sensor])
      const nextValue = Number(nextRoom[sensor])

      if (sensor === 'smoke' && nextValue > 0 && previousValue !== nextValue) {
        events.push({
          id: `smoke-${nextRoom.room_id}-${Date.now()}`,
          title: 'Safety Alert',
          text: `${formatRoomName(nextRoom.room_id)} smoke sensor triggered`,
          time: now,
          level: 'critical',
        })
      }

      if (sensor === 'motion' && nextValue > 0 && previousValue !== nextValue) {
        events.push({
          id: `motion-${nextRoom.room_id}-${Date.now()}`,
          title: 'Occupancy',
          text: `${formatRoomName(nextRoom.room_id)} motion detected`,
          time: now,
          level: 'motion',
        })
      }
    }
  }

  return events
}

function formatHistory(data) {
  return (data ?? [])
    .map((item) => {
      const rawTime = item.time || item.ts || item.timestamp
      const date = rawTime ? new Date(rawTime) : new Date()
      return {
        time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        value: Number(item.value),
      }
    })
    .filter((item) => Number.isFinite(item.value))
}

export default function App() {
  const [overview, setOverview] = useState(null)
  const previousOverviewRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [events, setEvents] = useState([])
  const [selectedRoomId, setSelectedRoomId] = useState(null)
  const [actionLoading, setActionLoading] = useState('')
  const [localStates, setLocalStates] = useState({})
  const [roomHistory, setRoomHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyMinutes, setHistoryMinutes] = useState(60)
  const [diagnostics, setDiagnostics] = useState(null)
  const [demoLoading, setDemoLoading] = useState('')

  const rooms = overview?.rooms ?? []
  const alerts = useMemo(() => calculateAlerts(overview), [overview])
  const health = useMemo(() => calculateHealth(overview, alerts), [overview, alerts])
  const selectedRoom = rooms.find((room) => room.room_id === selectedRoomId) ?? null

  async function loadOverview() {
    try {
      const data = await getSystemOverview()

      setEvents((currentEvents) => {
        const generatedEvents = buildEvents(previousOverviewRef.current, data)
        return [...generatedEvents, ...currentEvents].slice(0, 24)
      })
      previousOverviewRef.current = data
      setOverview(data)
      setError('')
    } catch (err) {
      setError(err.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOverview()
    const interval = window.setInterval(loadOverview, 700)
    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    async function loadDiagnostics() {
      try {
        const data = await getSystemDiagnostics()
        setDiagnostics(data)
      } catch (err) {
        console.error('Failed to load diagnostics', err)
      }
    }

    loadDiagnostics()
    const interval = window.setInterval(loadDiagnostics, 5000)
    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!selectedRoomId) {
      setRoomHistory([])
      return
    }

    async function loadHistory() {
      try {
        setHistoryLoading(true)
        const data = await getRoomHistory(selectedRoomId, 'temperature', historyMinutes)
        setRoomHistory(formatHistory(data))
      } catch (err) {
        console.error('Failed to load room history', err)
        setRoomHistory([])
      } finally {
        setHistoryLoading(false)
      }
    }

    loadHistory()
  }, [selectedRoomId, historyMinutes])

  async function handleModeChange(mode) {
    try {
      await setSystemMode(mode)
      setEvents((current) => [
        {
          id: `mode-manual-${Date.now()}`,
          title: 'Manual Command',
          text: `System mode requested: ${mode}`,
          time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          level: mode === 'AI' ? 'ai' : 'info',
        },
        ...current,
      ].slice(0, 24))
      await loadOverview()
    } catch (err) {
      setError(err.message || 'Failed to change system mode')
    }
  }

  async function handleActuator(roomId, device, state) {
    const key = `${roomId}-${device}-${state}`
    setActionLoading(key)
    setLocalStates((current) => ({
      ...current,
      [`${roomId}-${device}`]: state,
    }))
    setEvents((current) => [
      {
        id: `manual-${roomId}-${device}-${state}-${Date.now()}`,
        title: formatRoomName(roomId),
        text: `${formatDeviceName(device)} turned ${state}`,
        time: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
        level: 'manual',
      },
      ...current,
    ].slice(0, 24))

    try {
      await controlActuator(roomId, device, state)
      await loadOverview()
    } catch (err) {
      setError(err.message || 'Failed to control device')
    } finally {
      setActionLoading('')
    }
  }

  async function handleDemoScenario(scenario) {
    setDemoLoading(scenario)
    try {
      const demo = await triggerDemoScenario(scenario)
      setDiagnostics((current) => ({
        ...current,
        demo,
      }))
      setEvents((current) => [
        {
          id: `demo-${scenario}-${Date.now()}`,
          title: 'Demo Scenario',
          text: `${scenario.replaceAll('_', ' ')} activated`,
          time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          level: scenario === 'kitchen_smoke' ? 'critical' : 'manual',
        },
        ...current,
      ].slice(0, 24))
      await loadOverview()
    } catch (err) {
      setError(err.message || 'Failed to trigger demo scenario')
    } finally {
      setDemoLoading('')
    }
  }

  if (loading) {
    return (
      <main className="boot-screen">
        <div className="boot-mark" />
        <p>Synchronizing smart home telemetry...</p>
      </main>
    )
  }

  if (error && !overview) {
    return (
      <main className="boot-screen boot-screen--error">
        <p>{error}</p>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <div className="ambient-grid" aria-hidden="true" />
      <Header overview={overview} alerts={alerts} health={health} />

      <section className="dashboard-layout">
        <div className="dashboard-main">
          {error && (
            <div className="inline-alert" role="alert">
              {error}
            </div>
          )}

          <StatsBar
            overview={overview}
            alerts={alerts}
            health={health}
            onModeChange={handleModeChange}
          />

          <DemoConsole
            diagnostics={diagnostics}
            loading={demoLoading}
            onScenario={handleDemoScenario}
          />

          <EnergySavings overview={overview} diagnostics={diagnostics} />

          <RoomGrid
            rooms={rooms}
            selectedRoomId={selectedRoomId}
            localStates={localStates}
            onRoomClick={setSelectedRoomId}
          />
        </div>

        <aside className="side-stack">
          <AiExplanation
            overview={overview}
            diagnostics={diagnostics}
            alerts={alerts}
          />
          <AiTimeline overview={overview} diagnostics={diagnostics} alerts={alerts} />
          <ActivityFeed
            events={events}
            alerts={alerts}
            rooms={rooms}
            diagnostics={diagnostics}
          />
          <IntegrationDock diagnostics={diagnostics} mode={overview?.mode ?? 'Manual'} />
        </aside>
      </section>

      <AnimatePresence>
        {selectedRoom && (
          <RoomPanel
            key={selectedRoom.room_id}
            room={selectedRoom}
            history={roomHistory}
            historyLoading={historyLoading}
            historyMinutes={historyMinutes}
            actionLoading={actionLoading}
            localStates={localStates}
            onHistoryMinutesChange={setHistoryMinutes}
            onClose={() => setSelectedRoomId(null)}
            onActuator={handleActuator}
          />
        )}
      </AnimatePresence>
    </main>
  )
}
