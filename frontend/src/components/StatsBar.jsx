import { motion } from 'framer-motion'
import { Activity, Flame, Home, Sparkles, Zap } from 'lucide-react'

const MODES = ['Manual', 'Static', 'AI']

function countActiveDevices(rooms = []) {
  return rooms.reduce((total, room) => {
    const active = Object.values(room.actuators ?? {}).filter((state) => state === 'ON')
    return total + active.length
  }, 0)
}

export default function StatsBar({ overview, alerts, health, onModeChange }) {
  const rooms = overview?.rooms ?? []
  const mode = overview?.mode ?? 'Manual'
  const activeDevices = countActiveDevices(rooms)

  const stats = [
    { label: 'Rooms Online', value: rooms.length, icon: Home, tone: 'cyan' },
    { label: 'Active Devices', value: activeDevices, icon: Zap, tone: 'amber' },
    { label: 'System Health', value: `${health}%`, icon: Activity, tone: 'green' },
    { label: 'Alerts', value: alerts.length, icon: Flame, tone: alerts.length ? 'red' : 'green' },
  ]

  return (
    <section className="status-strip" aria-label="System statistics">
      <div className="mode-console">
        <div>
          <span className="panel-label">Operating Mode</span>
          <strong>{mode}</strong>
        </div>
        <div className="segmented-control" aria-label="Change operating mode">
          {MODES.map((item) => (
            <button
              key={item}
              className={item === mode ? 'is-active' : ''}
              onClick={() => onModeChange(item)}
              type="button"
            >
              {item === 'AI' && <Sparkles size={14} />}
              {item}
            </button>
          ))}
        </div>
      </div>

      {stats.map((stat, index) => {
        const Icon = stat.icon
        return (
          <motion.div
            className={`metric-tile metric-tile--${stat.tone}`}
            key={stat.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, duration: 0.35 }}
          >
            <Icon size={20} />
            <div>
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
            </div>
          </motion.div>
        )
      })}
    </section>
  )
}
