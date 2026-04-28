import { useEffect, useState } from "react"
import { getSystemOverview, controlActuator, setSystemMode, getRoomHistory } from "./services/api"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const ROOM_CONFIG = {
  living_room: {
    sensors: ["temperature"],
    controls: [
      { key: "light", label: "Light", onColor: "bg-amber-500 hover:bg-amber-400" },
      { key: "ac", label: "AC", onColor: "bg-sky-600 hover:bg-sky-500" },
      { key: "fan", label: "Fan", onColor: "bg-cyan-600 hover:bg-cyan-500" },
    ],
  },
  bedroom: {
    sensors: ["temperature"],
    controls: [
      { key: "light", label: "Light", onColor: "bg-amber-500 hover:bg-amber-400" },
      { key: "ac", label: "AC", onColor: "bg-sky-600 hover:bg-sky-500" },
      { key: "fan", label: "Fan", onColor: "bg-cyan-600 hover:bg-cyan-500" },
    ],
  },
  kitchen: {
    sensors: ["temperature", "motion", "smoke"],
    controls: [
      { key: "light", label: "Light", onColor: "bg-amber-500 hover:bg-amber-400" },
      { key: "exhaust_fan", label: "Exhaust Fan", onColor: "bg-cyan-600 hover:bg-cyan-500" },
    ],
  },
  bathroom: {
    sensors: ["temperature", "humidity", "motion"],
    controls: [
      { key: "light", label: "Light", onColor: "bg-amber-500 hover:bg-amber-400" },
      { key: "ventilation_fan", label: "Ventilation Fan", onColor: "bg-cyan-600 hover:bg-cyan-500" },
    ],
  },
  hallway: {
    sensors: ["motion"],
    controls: [
      { key: "light", label: "Light", onColor: "bg-amber-500 hover:bg-amber-400" },
    ],
  },
}

const SENSOR_LABELS = {
  temperature: "Temperature",
  humidity: "Humidity",
  motion: "Motion",
  smoke: "Smoke",
}

function formatSensorValue(sensorKey, value) {
  if (sensorKey === "temperature") return `${value} °C`
  if (sensorKey === "humidity") return `${value} %`
  return value
}

function formatRoomName(roomId) {
  return roomId
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function calculateAlerts(overview) {
  if (!overview) return []

  const alerts = []

  for (const room of overview.rooms ?? []) {
    if (Number(room.smoke) > 0) {
      alerts.push({
        id: `${room.room_id}-smoke`,
        text: `${formatRoomName(room.room_id)} smoke detected`,
      })
    }
  }

  return alerts
}

function buildEventsFromOverviewChange(previousOverview, nextOverview) {
  if (!previousOverview || !nextOverview) return []

  const newEvents = []

  if (previousOverview.mode !== nextOverview.mode) {
    newEvents.push({
      id: `mode-${Date.now()}-${nextOverview.mode}`,
      text: `System mode changed to ${nextOverview.mode}`,
      time: new Date().toLocaleTimeString(),
      level: "info",
    })
  }

  for (const nextRoom of nextOverview.rooms ?? []) {
    const prevRoom = previousOverview.rooms?.find(
      (room) => room.room_id === nextRoom.room_id
    )

    if (!prevRoom) continue

    for (const [device, nextState] of Object.entries(nextRoom.actuators ?? {})) {
      const prevState = prevRoom.actuators?.[device]

      if (prevState && prevState !== nextState) {
        newEvents.push({
          id: `actuator-${nextRoom.room_id}-${device}-${Date.now()}`,
          text: `${formatRoomName(nextRoom.room_id)} ${device.replaceAll("_", " ")} turned ${nextState}`,
          time: new Date().toLocaleTimeString(),
          level: "info",
        })
      }
    }

    for (const [sensor, value] of Object.entries(nextRoom.sensors ?? {})) {
      const prevValue = prevRoom.sensors?.[sensor]

      if (sensor === "smoke" && value > 0 && prevValue !== value) {
        newEvents.push({
          id: `smoke-${nextRoom.room_id}-${Date.now()}`,
          text: `${formatRoomName(nextRoom.room_id)} smoke detected`,
          time: new Date().toLocaleTimeString(),
          level: "alert",
        })
      }

      if (sensor === "motion" && value > 0 && prevValue !== value) {
        newEvents.push({
          id: `motion-${nextRoom.room_id}-${Date.now()}`,
          text: `${formatRoomName(nextRoom.room_id)} motion detected`,
          time: new Date().toLocaleTimeString(),
          level: "info",
        })
      }
    }
  }

  return newEvents
}

export default function App() {
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [actionLoading, setActionLoading] = useState("")
  const [localStates, setLocalStates] = useState({})
  const [events, setEvents] = useState([])
  const [previousOverview, setPreviousOverview] = useState(null)
  const [eventLimit, setEventLimit] = useState(10)
  const alerts = calculateAlerts(overview)
  const [selectedRoomId, setSelectedRoomId] = useState(null)
  const [isClosingModal, setIsClosingModal] = useState(false)
  const selectedRoom = overview?.rooms?.find((room) => room.room_id === selectedRoomId) ?? null
  const [roomHistory, setRoomHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyMinutes, setHistoryMinutes] = useState(60)


  async function loadOverview() {
    try {
      const data = await getSystemOverview()

      setEvents((prevEvents) => {
        const generatedEvents = buildEventsFromOverviewChange(previousOverview, data)
        return [...generatedEvents, ...prevEvents].slice(0, 20)
      })

      setPreviousOverview(data)
      setOverview(data)
      setError("")
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOverview()

    const interval = setInterval(() => {
      loadOverview()
    }, 500)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!selectedRoomId) {
      setRoomHistory([])
      return
    }

    loadRoomHistory(selectedRoomId)
  }, [selectedRoomId, historyMinutes])



  async function handleActuator(roomId, device, state) {
    const actionKey = `${roomId}-${device}-${state}`
    setActionLoading(actionKey)

    setLocalStates((prev) => ({
      ...prev,
      [`${roomId}-${device}`]: state,
    }))

    try {
      await controlActuator(roomId, device, state)

      // stop loading quickly
      setActionLoading("")

      // refresh once, but dont block the button on it
      loadOverview()
    } catch (err) {
      setError(err.message)
      setActionLoading("")
    }
  }

  async function handleModeChange(mode) {
    try {
      await setSystemMode(mode)
      await loadOverview()
    } catch (err) {
      setError(err.message)
    }
  }

  function closeRoomModal() {
    setIsClosingModal(true)

    setTimeout(() => {
      setSelectedRoomId(null)
      setIsClosingModal(false)
    }, 200)
  }

  async function loadRoomHistory(roomId) {
    try {
      setHistoryLoading(true)

      const data = await getRoomHistory(roomId, "temperature", historyMinutes)

      const formatted = (data ?? []).map((item) => ({
        time: new Date(item.time || item.ts || item.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        value: Number(item.value),
      }))
      setRoomHistory(formatted)
    } catch (err) {
      console.error("Failed to load room history", err)
      setRoomHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  function getOnButtonClass(currentState, loadingKey, expectedKey, colorClass) {
    const active = currentState === "ON"
    const loading = loadingKey === expectedKey

    return `flex-1 rounded-xl px-4 py-2 font-medium ${active ? colorClass : "bg-slate-700 hover:bg-slate-600"
      } ${loading ? "opacity-80" : ""}`
  }

  function getOffButtonClass(currentState, loadingKey, expectedKey) {
    const active = currentState === "OFF"
    const loading = loadingKey === expectedKey

    return `flex-1 rounded-xl px-4 py-2 font-medium ${active ? "bg-rose-600 hover:bg-rose-500" : "bg-slate-700 hover:bg-slate-600"
      } ${loading ? "opacity-80" : ""}`
  }



  if (loading) {
    return (
      <div className="w-full min-h-screen bg-slate-950 text-white px-6 py-8">
        <p className="text-xl">Loading dashboard...</p>
      </div>
    )
  }

  if (error && !overview) {
    return (
      <div className="min-h-screen bg-slate-950 text-red-400 flex items-center justify-center">
        <p className="text-xl">{error}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white px-6 py-8 flex justify-center">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2 text-yellow-400 !text-yellow-400">
            Smart Home Dashboard
          </h1>
          <p className="text-slate-400">Adaptive AI-Based IoT Smart Home System</p>
        </header>

        {error && (
          <div className="mb-6 bg-red-900/40 border border-red-700 text-red-300 rounded-2xl p-4">
            {error}
          </div>
        )}

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-900 rounded-2xl p-5 shadow-lg">
            <p className="text-slate-400 text-sm mb-2">System Mode</p>

            <div className="flex gap-2">
              {["Manual", "Static", "AI"].map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleModeChange(mode)}
                  className={`flex-1 rounded-xl px-3 py-2 text-sm font-medium ${overview.mode === mode
                    ? "bg-yellow-500 text-black"
                    : "bg-slate-700 hover:bg-slate-600"
                    }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 rounded-2xl p-5 shadow-lg">
            <p className="text-slate-400 text-sm mb-2">Total Rooms</p>
            <p className="text-2xl font-semibold">{overview.total_rooms}</p>
          </div>

          <div className="bg-slate-900 rounded-2xl p-5 shadow-lg">
            <p className="text-slate-400 text-sm mb-2">Active Alerts</p>
            <p className="text-2xl font-semibold">{alerts.length}</p>
            {alerts.length > 0 && (
              <p className="text-xs text-red-300 mt-2">
                {alerts[0].text}
              </p>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 gap-6">Rooms</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

            {overview.rooms.map((room) => {
              const config = ROOM_CONFIG[room.room_id]
              const hasAlert = Number(room.smoke) > 0
              return (
                <div

                  key={room.room_id}
                  onClick={() => {
                    setIsClosingModal(false)
                    setSelectedRoomId(room.room_id)
                  }}
                  className={`cursor-pointer rounded-2xl p-5 shadow-lg border transition hover:scale-[1.01] ${hasAlert
                    ? "bg-red-950/40 border-red-800 shadow-red-900/40"
                    : "bg-slate-900 border-slate-800"
                    } ${selectedRoomId === room.room_id ? "ring-2 ring-yellow-400" : ""
                    }`}
                >
                  <div className="mb-4 flex items-center justify-center gap-2">
                    <h3 className="text-xl font-semibold capitalize tracking-wide">
                      {formatRoomName(room.room_id)}
                    </h3>

                    {hasAlert && (
                      <span className="text-xs text-red-300 bg-red-900/50 px-2 py-1 rounded-md">
                        ALERT
                      </span>
                    )}
                  </div>

                  <div className="space-y-2 text-slate-300 mb-6 text-center text-sm">
                    {config.sensors.map((sensorKey) => (
                      <p key={sensorKey}>
                        {SENSOR_LABELS[sensorKey]}:{" "}
                        {formatSensorValue(sensorKey, room[sensorKey])}
                      </p>
                    ))}

                    {config.controls.map((control, index) => (
                      <p key={`${control.label}-${index}`}>
                        {control.label}: {room.actuators[control.key]}
                      </p>
                    ))}
                  </div>

                  <div className="space-y-4">
                    {config.controls.map((control, index) => {
                      const localKey = `${room.room_id}-${control.key}`
                      const currentState = localStates[localKey] ?? room.actuators[control.key]

                      return (
                        <div key={`${control.label}-${index}`}>
                          <p className="text-sm text-slate-400 mb-2 text-center">
                            {control.label} Control
                          </p>

                          <div className="flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleActuator(room.room_id, control.key, "ON")
                              }}
                              disabled={actionLoading !== ""}
                              className={getOnButtonClass(
                                currentState,
                                actionLoading,
                                `${room.room_id}-${control.key}-ON`,
                                control.onColor
                              )}
                            >
                              {actionLoading === `${room.room_id}-${control.key}-ON`
                                ? "Sending..."
                                : `${control.label} ON`}
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleActuator(room.room_id, control.key, "OFF")
                              }}
                              disabled={actionLoading !== ""}
                              className={getOffButtonClass(
                                currentState,
                                actionLoading,
                                `${room.room_id}-${control.key}-OFF`
                              )}
                            >
                              {actionLoading === `${room.room_id}-${control.key}-OFF`
                                ? "Sending..."
                                : `${control.label} OFF`}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </section>



        <section className="mt-8">
          <div className="bg-slate-900 rounded-2xl p-5 shadow-lg border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold gap-5">Recent Activity</h2>

              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-400">{Math.min(events.length, eventLimit)} / {events.length} items</span>

                <select
                  value={eventLimit}
                  onChange={(e) => setEventLimit(Number(e.target.value))}
                  className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-sm"
                >
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                  <option value={20}>20</option>
                </select>
              </div>
            </div>

            {events.length === 0 ? (
              <p className="text-slate-400">No recent activity yet.</p>
            ) : (
              <div className="space-y-3">
                {events.slice(0, eventLimit).map((event) => (
                  <div
                    key={event.id}
                    className={`rounded-xl px-4 py-3 border ${event.level === "alert"
                      ? "bg-red-950/40 border-red-800 text-red-200"
                      : "bg-slate-800 border-slate-700 text-slate-200"
                      }`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <p className="font-medium">{event.text}</p>
                      <span className="text-xs text-slate-400 whitespace-nowrap">
                        {event.time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {selectedRoom && (
          <div
            className={`fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4 ${isClosingModal ? "animate-fadeOut" : "animate-fadeIn"
              }`}
            onClick={closeRoomModal}
          >
            <div
              className={`w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl border border-slate-700 bg-slate-900 shadow-2xl ${isClosingModal ? "animate-scaleOut" : "animate-scaleIn"
                }`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-slate-800 px-6 py-5">
                <div>
                  <h2 className="text-2xl font-semibold">
                    {formatRoomName(selectedRoom.room_id)} Details
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    Live room status and controls
                  </p>
                </div>

                <button
                  onClick={closeRoomModal}
                  className="rounded-xl bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
                >
                  Close
                </button>
              </div>

              <div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
                  <h3 className="mb-4 text-lg font-semibold">Sensors</h3>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Temperature</span>
                      <span>{formatSensorValue("temperature", selectedRoom.temperature)}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Humidity</span>
                      <span>{formatSensorValue("humidity", selectedRoom.humidity)}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Motion</span>
                      <span>{formatSensorValue("motion", selectedRoom.motion)}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Smoke</span>
                      <span>{formatSensorValue("smoke", selectedRoom.smoke)}</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
                  <h3 className="mb-4 text-lg font-semibold">Actuators</h3>

                  <div className="space-y-4">
                    {(ROOM_CONFIG[selectedRoom.room_id]?.controls ?? []).map((control) => {
                      const localKey = `${selectedRoom.room_id}-${control.key}`
                      const currentState =
                        localStates[localKey] ?? selectedRoom.actuators?.[control.key]

                      return (
                        <div key={control.key}>
                          <p className="mb-2 font-medium">{control.label}</p>

                          <div className="flex gap-3">
                            <button
                              onClick={() =>
                                handleActuator(selectedRoom.room_id, control.key, "ON")
                              }
                              className={getOnButtonClass(
                                currentState,
                                actionLoading,
                                `${selectedRoom.room_id}-${control.key}-ON`,
                                control.onColor
                              )}
                            >
                              {actionLoading === `${selectedRoom.room_id}-${control.key}-ON`
                                ? "Sending..."
                                : "ON"}
                            </button>

                            <button
                              onClick={() =>
                                handleActuator(selectedRoom.room_id, control.key, "OFF")
                              }
                              className={getOffButtonClass(
                                currentState,
                                actionLoading,
                                `${selectedRoom.room_id}-${control.key}-OFF`
                              )}
                            >
                              {actionLoading === `${selectedRoom.room_id}-${control.key}-OFF`
                                ? "Sending..."
                                : "OFF"}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>


                <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5 md:col-span-2">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Temperature History</h3>

                      <select
                        value={historyMinutes}
                        onChange={(e) => setHistoryMinutes(Number(e.target.value))}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-sm"
                      >
                        <option value={15}>15 min</option>
                        <option value={60}>60 min</option>
                        <option value={180}>180 min</option>
                      </select>
                    </div>
                  </div>

                  {historyLoading ? (
                    <p className="text-slate-400">Loading chart...</p>
                  ) : roomHistory.length === 0 ? (
                    <p className="text-slate-400">No history data available.</p>
                  ) : (
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={roomHistory}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="time" />
                          <YAxis
                            tick={{ fill: "#94a3b8" }}
                            domain={["auto", "auto"]}
                          />

                          <Tooltip
                            contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155" }}
                            labelStyle={{ color: "#e2e8f0" }}
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#38bdf8"
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}