// Maps GET /api/system/overview → the shape NeuroNest UI components expect.
//
// Backend Room schema:
//   { room_id, temperature, humidity, motion (int), smoke (int), actuators: {device: "ON"|"OFF"} }
//
// Backend mode values: "AI" | "Manual" | "Static"
// UI mode values:      "Auto" | "Manual" | "Away"

const ROOM_ID_MAP = {
  living_room: 'living',
  bedroom:     'bedroom',
  kitchen:     'kitchen',
  bathroom:    'bathroom',
  hallway:     'hallway',
  office:      'office',
}

const MODE_MAP = {
  AI:     'Auto',
  Manual: 'Manual',
  Static: 'Away',
}

function deviceIcon(deviceKey) {
  const k = deviceKey.toLowerCase()
  if (k.includes('light') || k.includes('lamp') || k.includes('pendant')) return 'Lightbulb'
  if (k.includes('fan') || k.includes('hood') || k.includes('vent') || k.includes('exhaust')) return 'Fan'
  if (k.includes('ac') || k.includes('climate') || k.includes('thermo')) return 'Thermo'
  if (k.includes('speaker') || k.includes('display') || k.includes('screen')) return 'Speaker'
  if (k.includes('lock') || k.includes('door')) return 'Lock'
  if (k.includes('blind') || k.includes('curtain')) return 'Sun'
  if (k.includes('coffee') || k.includes('appliance')) return 'Sparkles'
  return 'Lightbulb'
}

function deviceLabel(deviceKey) {
  return deviceKey
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export function mapOverviewToUiShape(overview) {
  if (!overview) return null

  const sensors = {}
  const devices = {}

  for (const room of overview.rooms ?? []) {
    const uiId = ROOM_ID_MAP[room.room_id] ?? room.room_id

    sensors[uiId] = {
      temp:     typeof room.temperature === 'number' ? room.temperature : null,
      humidity: typeof room.humidity === 'number' ? room.humidity : null,
      motion:   Number(room.motion) > 0,
      smoke:    room.room_id === 'kitchen' ? Number(room.smoke) > 0 : undefined,
      co2:      null,
      lux:      typeof room.light === 'number' ? room.light : null,
    }

    devices[uiId] = Object.entries(room.actuators ?? {}).map(([key, state]) => ({
      id:        `${uiId}_${key}`,
      roomId:    uiId,
      deviceKey: key,
      name:      deviceLabel(key),
      icon:      deviceIcon(key),
      on:        state === 'ON',
      meta:      state === 'ON' ? 'On' : 'Off',
    }))
  }

  return {
    _raw: overview,
    sensors,
    devices,
    mode: MODE_MAP[overview.mode] ?? overview.mode,
    activeAlerts: overview.active_alerts ?? 0,
  }
}

export function uiModeToApiMode(uiMode) {
  return { Auto: 'AI', Manual: 'Manual', Away: 'Static' }[uiMode] ?? uiMode
}
