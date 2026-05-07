import { BatteryCharging, Leaf, TrendingDown, Zap } from 'lucide-react'

function estimateSavings(overview, diagnostics) {
  const actions = diagnostics?.ai?.recent_actions ?? []
  const rooms = overview?.rooms ?? []
  const offActions = actions.filter((action) => String(action.command).toUpperCase() === 'OFF').length
  const dimActions = actions.filter((action) => String(action.command).toUpperCase() === 'DIM').length
  const activeDevices = rooms.reduce(
    (count, room) => count + Object.values(room.actuators ?? {}).filter((state) => state === 'ON').length,
    0
  )
  const estimatedKwh = Math.max(0.2, offActions * 0.18 + dimActions * 0.08 + Math.max(0, 5 - activeDevices) * 0.04)
  const comfortScore = Math.max(72, Math.min(98, 94 - activeDevices * 3 + dimActions))

  return {
    estimatedKwh: estimatedKwh.toFixed(2),
    offActions,
    dimActions,
    activeDevices,
    comfortScore,
  }
}

export default function EnergySavings({ overview, diagnostics }) {
  const savings = estimateSavings(overview, diagnostics)

  return (
    <section className="energy-panel" aria-label="Energy savings estimate">
      <div className="energy-copy">
        <span className="panel-label">Energy Impact</span>
        <h2>AI Savings Estimate</h2>
        <p>
          Approximate reduction derived from recent AI OFF/DIM decisions and current active
          actuator count.
        </p>
      </div>

      <div className="energy-metrics">
        <div className="energy-meter">
          <Leaf size={22} />
          <strong>{savings.estimatedKwh} kWh</strong>
          <span>estimated saved</span>
        </div>
        <div className="energy-stat">
          <TrendingDown size={18} />
          <strong>{savings.offActions}</strong>
          <span>AI shutoffs</span>
        </div>
        <div className="energy-stat">
          <BatteryCharging size={18} />
          <strong>{savings.comfortScore}%</strong>
          <span>comfort score</span>
        </div>
        <div className="energy-stat">
          <Zap size={18} />
          <strong>{savings.activeDevices}</strong>
          <span>active devices</span>
        </div>
      </div>
    </section>
  )
}
