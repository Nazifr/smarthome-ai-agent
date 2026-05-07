import { Activity, BrainCircuit, Cpu, RadioTower, Zap } from 'lucide-react'
import { formatDeviceName, formatRoomName, formatSensorValue } from '../App'

function latestAction(diagnostics) {
  return diagnostics?.ai?.recent_actions?.[0] ?? null
}

export default function AiTimeline({ overview, diagnostics, alerts }) {
  const action = latestAction(diagnostics)
  const room = overview?.rooms?.find((item) => item.room_id === action?.room)
  const hasAlert = action && alerts.some((alert) => alert.room === action.room)
  const mode = overview?.mode ?? 'Manual'

  const steps = [
    {
      icon: RadioTower,
      title: 'Sensor input',
      text: room
        ? `${formatRoomName(room.room_id)}: ${formatSensorValue('temperature', room.temperature)}, ${formatSensorValue('motion', room.motion)}`
        : 'Waiting for live sensor context',
    },
    {
      icon: Cpu,
      title: 'Context layer',
      text: action?.context ? action.context.replaceAll('_', ' ') : hasAlert ? 'safety critical' : 'live monitoring',
    },
    {
      icon: BrainCircuit,
      title: 'AI decision',
      text: action
        ? `${formatDeviceName(action.device)} -> ${action.command}`
        : mode === 'AI'
          ? 'AI armed, waiting for next meaningful change'
          : 'AI paused until AI mode is selected',
    },
    {
      icon: Zap,
      title: 'Actuator output',
      text: action ? `${formatRoomName(action.room)} command published` : 'No command published yet',
    },
  ]

  return (
    <section className="ai-timeline" aria-label="AI decision timeline">
      <div className="activity-header">
        <div>
          <span className="panel-label">AI Timeline</span>
          <h2>Signal To Action</h2>
        </div>
        <Activity size={20} />
      </div>

      <div className="timeline-steps">
        {steps.map((step) => {
          const Icon = step.icon
          return (
            <div className="timeline-step" key={step.title}>
              <div className="timeline-dot">
                <Icon size={15} />
              </div>
              <div>
                <strong>{step.title}</strong>
                <p>{step.text}</p>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
