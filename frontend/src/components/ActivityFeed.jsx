import { motion } from 'framer-motion'
import { CircleAlert, Clock3, History, Radio } from 'lucide-react'
import { formatDeviceName, formatRoomName } from '../App'

function fallbackEvents(alerts, rooms) {
  const generated = []
  const now = new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  for (const alert of alerts) {
    generated.push({
      id: alert.id,
      title: 'Safety Alert',
      text: alert.text,
      time: now,
      level: 'critical',
      passive: false,
    })
  }

  for (const room of rooms) {
    if (Number(room.motion) > 0) {
      generated.push({
        id: `${room.room_id}-motion-live`,
        title: 'Live Occupancy',
        text: `${formatRoomName(room.room_id)} motion detected`,
        time: now,
        level: 'motion',
        passive: true,
      })
    }
  }

  return generated
}

function backendActionEvents(diagnostics) {
  return (diagnostics?.ai?.recent_actions ?? []).slice(0, 5).map((action) => ({
    id: `backend-${action.time}-${action.room}-${action.device}-${action.command}`,
    title: formatRoomName(action.room),
    text: `${formatDeviceName(action.device)} -> ${action.command}`,
    time: new Date(action.time).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    level: 'ai',
    passive: false,
  }))
}

export default function ActivityFeed({ events, alerts, rooms, diagnostics }) {
  const manualEvents = events.filter((event) => !event.passive)
  const backendEvents = backendActionEvents(diagnostics)
  const passiveEvents = [...events.filter((event) => event.passive), ...fallbackEvents(alerts, rooms)]
  const visibleEvents = [...manualEvents, ...backendEvents, ...passiveEvents].slice(0, 8)

  return (
    <section className="activity-rail" aria-label="Recent actions and activity">
      <div className="activity-header">
        <div>
          <span className="panel-label">Recent Actions</span>
          <h2>Action History</h2>
        </div>
        <History size={20} />
      </div>

      {visibleEvents.length === 0 ? (
        <div className="empty-feed">
          <Radio size={20} />
          <span>No recent activity yet</span>
        </div>
      ) : (
        <div className="event-list">
          {visibleEvents.map((event, index) => (
            <motion.div
              className={`event-item event-item--${event.level}`}
              key={event.id}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.04 }}
            >
              <div className="event-icon">
                {event.level === 'critical' ? <CircleAlert size={16} /> : <Clock3 size={16} />}
              </div>
              <div>
                <strong>{event.title}</strong>
                <p>{event.text}</p>
              </div>
              <time>{event.time}</time>
            </motion.div>
          ))}
        </div>
      )}
    </section>
  )
}
