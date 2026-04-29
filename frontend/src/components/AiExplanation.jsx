import { BrainCircuit, CheckCircle2, CircleAlert, Route } from 'lucide-react'
import { formatDeviceName, formatRoomName, formatSensorValue } from '../App'

function getLatestAction(diagnostics) {
  return diagnostics?.ai?.recent_actions?.[0] ?? null
}

function getRoom(overview, action) {
  if (!action) return null
  return overview?.rooms?.find((room) => room.room_id === action.room) ?? null
}

function buildSignals(room, alerts) {
  if (!room) return ['Waiting for recent AI action data']

  const signals = [
    `Temperature ${formatSensorValue('temperature', room.temperature)}`,
    `Motion ${formatSensorValue('motion', room.motion)}`,
  ]

  if (room.humidity) signals.push(`Humidity ${formatSensorValue('humidity', room.humidity)}`)
  if (alerts.some((alert) => alert.room === room.room_id)) signals.push('Safety alert active')

  return signals
}

export default function AiExplanation({ overview, diagnostics, alerts }) {
  const action = getLatestAction(diagnostics)
  const room = getRoom(overview, action)
  const mode = overview?.mode ?? diagnostics?.ai?.mode ?? 'Manual'
  const armed = mode === 'AI'
  const signals = buildSignals(room, alerts)

  return (
    <section className="ai-explanation" aria-label="AI explanation">
      <div className="activity-header">
        <div>
          <span className="panel-label">AI Explanation</span>
          <h2>Decision Trace</h2>
        </div>
        <BrainCircuit size={20} />
      </div>

      <div className={armed ? 'ai-status is-armed' : 'ai-status'}>
        {armed ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />}
        <span>{armed ? 'AI armed' : 'AI paused'}</span>
      </div>

      <div className="decision-card">
        <span className="panel-label">Latest decision</span>
        <strong>
          {action
            ? `${formatRoomName(action.room)} ${formatDeviceName(action.device)} -> ${action.command}`
            : 'No AI decision logged yet'}
        </strong>
        <p>{action?.reason || diagnostics?.ai?.message || 'Switch to AI mode and wait for a sensor change.'}</p>
      </div>

      <div className="signal-list">
        <span className="panel-label">Signals used</span>
        {signals.map((signal) => (
          <div className="signal-item" key={signal}>
            <Route size={14} />
            {signal}
          </div>
        ))}
      </div>
    </section>
  )
}
