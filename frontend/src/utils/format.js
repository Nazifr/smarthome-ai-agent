export const ROOM_CONFIG = {
  living_room: { zone: 'West Wing',       sensors: ['temperature'], controls: [{ key: 'light', label: 'Light' }, { key: 'ac', label: 'AC' }, { key: 'fan', label: 'Fan' }] },
  bedroom:     { zone: 'Private Zone',    sensors: ['temperature'], controls: [{ key: 'light', label: 'Light' }, { key: 'ac', label: 'AC' }, { key: 'fan', label: 'Fan' }] },
  kitchen:     { zone: 'Safety Critical', sensors: ['temperature', 'motion', 'smoke'], controls: [{ key: 'light', label: 'Light' }, { key: 'exhaust_fan', label: 'Exhaust Fan' }] },
  bathroom:    { zone: 'Humidity Watch',  sensors: ['temperature', 'humidity', 'motion'], controls: [{ key: 'light', label: 'Light' }, { key: 'ventilation_fan', label: 'Ventilation Fan' }] },
  hallway:     { zone: 'Transit',         sensors: ['motion'], controls: [{ key: 'light', label: 'Light' }] },
  office:      { zone: 'Work Zone',       sensors: ['temperature', 'humidity', 'motion'], controls: [{ key: 'light', label: 'Light' }, { key: 'ac', label: 'AC' }, { key: 'fan', label: 'Fan' }] },
}

export const SENSOR_LABELS = {
  temperature: 'Temperature',
  humidity: 'Humidity',
  motion: 'Motion',
  smoke: 'Smoke',
  light: 'Light',
}

export function formatRoomName(roomId = '') {
  return roomId.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatDeviceName(device = '') {
  return device.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatSensorValue(sensor, value) {
  if (value === undefined || value === null || value === '') return 'N/A'
  if (sensor === 'temperature') return `${Number(value).toFixed(1)} C`
  if (sensor === 'humidity') return `${Number(value).toFixed(0)}%`
  if (sensor === 'motion') return Number(value) > 0 ? 'Detected' : 'Clear'
  if (sensor === 'smoke') return Number(value) > 0 ? 'Alert' : 'Clear'
  if (sensor === 'light') return `${Number(value).toFixed(0)} lux`
  return String(value)
}
