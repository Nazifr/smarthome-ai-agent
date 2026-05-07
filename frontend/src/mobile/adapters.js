// Mobile adapters — convert API responses to screen props.
// Only uses fields that actually exist in the backend schema.
//
// Backend Room: { room_id, temperature, humidity, motion (int), smoke (int), actuators: {key: "ON"|"OFF"} }
// Backend SystemOverview: { mode, total_rooms, active_alerts, rooms[] }

const ROOM_NAMES = {
  living_room: 'Living Room',
  bedroom:     'Bedroom',
  kitchen:     'Kitchen',
  bathroom:    'Bathroom',
  hallway:     'Hallway',
}

const DEVICE_ICONS = {
  light:           'lightbulb',
  lamp:            'lightbulb',
  ac:              'thermo',
  fan:             'fan',
  exhaust_fan:     'fan',
  ventilation_fan: 'fan',
  speaker:         'speaker',
  display:         'speaker',
  lock:            'lock',
}

function deviceIcon(key) {
  const k = key.toLowerCase()
  for (const [pattern, icon] of Object.entries(DEVICE_ICONS)) {
    if (k.includes(pattern)) return icon
  }
  return 'lightbulb'
}

function deviceLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function roomStatus(room, devicesOn) {
  if (Number(room.smoke) > 0) return { text: 'Smoke detected', alert: true }
  if (devicesOn > 0) return { text: `${devicesOn} device${devicesOn > 1 ? 's' : ''} on`, active: true }
  if (Number(room.motion) > 0) return { text: 'Occupied', active: false }
  return { text: 'All off', active: false }
}

export function adaptHome(overview) {
  if (!overview) return null
  const rooms = (overview.rooms ?? []).map(r => {
    const devicesOn = Object.values(r.actuators ?? {}).filter(s => s === 'ON').length
    const totalDevices = Object.keys(r.actuators ?? {}).length
    const status = roomStatus(r, devicesOn)
    return {
      id:           r.room_id,
      name:         ROOM_NAMES[r.room_id] ?? r.room_id,
      temp:         r.temperature,
      humidity:     r.humidity,
      motion:       Number(r.motion) > 0,
      smoke:        Number(r.smoke) > 0,
      devicesOn,
      totalDevices,
      status,
    }
  })

  const totalDevicesOn = rooms.reduce((s, r) => s + r.devicesOn, 0)
  const totalDevices   = rooms.reduce((s, r) => s + r.totalDevices, 0)
  const primaryRoom    = rooms.find(r => r.id === 'living_room') ?? rooms[0]

  return {
    temp:          primaryRoom?.temp ?? null,
    humidity:      primaryRoom?.humidity ?? null,
    totalDevicesOn,
    totalDevices,
    mode:          overview.mode,
    activeAlerts:  overview.active_alerts ?? 0,
    rooms,
  }
}

export function adaptRoom(overview, roomId) {
  if (!overview) return null
  const r = (overview.rooms ?? []).find(x => x.room_id === roomId)
  if (!r) return null

  const devices = Object.entries(r.actuators ?? {}).map(([key, state]) => ({
    id:     `${roomId}_${key}`,
    key,
    name:   deviceLabel(key),
    icon:   deviceIcon(key),
    on:     state === 'ON',
  }))

  const devicesOn = devices.filter(d => d.on).length

  return {
    id:       r.room_id,
    name:     ROOM_NAMES[r.room_id] ?? r.room_id,
    temp:     r.temperature,
    humidity: r.humidity,
    motion:   Number(r.motion) > 0,
    smoke:    Number(r.smoke) > 0,
    devices,
    devicesOn,
  }
}

export function adaptEnergy(overview) {
  if (!overview) return null
  const totalDevicesOn = (overview.rooms ?? []).reduce((s, r) =>
    s + Object.values(r.actuators ?? {}).filter(v => v === 'ON').length, 0)

  // Estimated from device count — no real energy API exists yet
  const estimatedKwh = +(8.4 + totalDevicesOn * 0.3).toFixed(1)
  const estimatedSavings = +(3.2 - totalDevicesOn * 0.05).toFixed(1)

  // Synthetic 7-day bars (no history API)
  const todayFraction = Math.max(0.15, Math.min(0.95, estimatedKwh / 12))
  const syntheticBars = [0.72, 0.85, 0.61, 0.91, 0.76, 0.53, todayFraction]
  const dayLabels = (() => {
    const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
    const today = new Date().getDay()
    return Array.from({length: 7}, (_, i) => days[(today - 6 + i + 7) % 7])
  })()

  return {
    estimatedKwh,
    estimatedSavings: Math.max(0, estimatedSavings),
    syntheticBars,
    dayLabels,
    totalDevicesOn,
  }
}

export { ROOM_NAMES, deviceIcon, deviceLabel }
