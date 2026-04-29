import { motion } from 'framer-motion'
import {
  Droplets,
  Fan,
  Flame,
  Lightbulb,
  MoveRight,
  Radio,
  Thermometer,
  Waves,
} from 'lucide-react'
import { formatRoomName, formatSensorValue, ROOM_CONFIG } from '../App'

const SENSOR_ICONS = {
  temperature: Thermometer,
  humidity: Droplets,
  motion: Radio,
  smoke: Flame,
}

const DEVICE_ICONS = {
  light: Lightbulb,
  ac: Waves,
  fan: Fan,
  exhaust_fan: Fan,
  ventilation_fan: Fan,
}

export default function RoomCard({ room, index, selected, localStates, onClick }) {
  const config = ROOM_CONFIG[room.room_id] ?? {
    zone: 'Adaptive Zone',
    sensors: ['temperature', 'humidity', 'motion', 'smoke'],
    controls: Object.keys(room.actuators ?? {}).map((key) => ({ key, label: key })),
  }
  const hasAlert = Number(room.smoke) > 0
  const activeDevices = Object.entries(room.actuators ?? {}).filter(([device, state]) => {
    const localState = localStates?.[`${room.room_id}-${device}`]
    return (localState ?? state) === 'ON'
  })

  return (
    <motion.button
      type="button"
      className={`room-node room-node--${room.room_id} ${selected ? 'is-selected' : ''} ${
        hasAlert ? 'has-alert' : ''
      }`}
      onClick={onClick}
      variants={{
        hidden: { opacity: 0, y: 24, scale: 0.97 },
        visible: { opacity: 1, y: 0, scale: 1 },
      }}
      transition={{ duration: 0.42, delay: index * 0.02, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -6 }}
      whileTap={{ scale: 0.985 }}
    >
      <span className="node-signal" aria-hidden="true" />
      <span className="node-topline">
        <span>{config.zone}</span>
        <span className={hasAlert ? 'room-state room-state--alert' : 'room-state'}>
          {hasAlert ? 'Alert' : 'Nominal'}
        </span>
      </span>

      <span className="node-title">
        {formatRoomName(room.room_id)}
        <MoveRight size={18} />
      </span>

      <span className="sensor-grid">
        {config.sensors.map((sensor) => {
          const Icon = SENSOR_ICONS[sensor]
          return (
            <span className="sensor-pill" key={sensor}>
              {Icon && <Icon size={15} />}
              <span>{formatSensorValue(sensor, room[sensor])}</span>
            </span>
          )
        })}
      </span>

      <span className="device-row">
        {Object.entries(room.actuators ?? {}).map(([device, state]) => {
          const Icon = DEVICE_ICONS[device] ?? Lightbulb
          const localState = localStates?.[`${room.room_id}-${device}`]
          const active = (localState ?? state) === 'ON'

          return (
            <span className={active ? 'device-dot is-on' : 'device-dot'} key={device}>
              <Icon size={14} />
            </span>
          )
        })}
        <span className="device-summary">
          {activeDevices.length}/{Object.keys(room.actuators ?? {}).length} active
        </span>
      </span>
    </motion.button>
  )
}
