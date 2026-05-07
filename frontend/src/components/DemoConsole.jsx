import { FlaskConical, Play } from 'lucide-react'

const FALLBACK_SCENARIOS = [
  { id: 'live', label: 'Live Data', description: 'Return to simulator data.' },
  { id: 'kitchen_smoke', label: 'Kitchen Smoke', description: 'Safety critical smoke event.' },
  { id: 'night_routine', label: 'Night Routine', description: 'Evening comfort automation.' },
  { id: 'bathroom_humidity', label: 'Bathroom Humidity', description: 'Ventilation response.' },
  { id: 'empty_home', label: 'Empty Home', description: 'Energy-saving behavior.' },
]

export default function DemoConsole({ diagnostics, loading, onScenario }) {
  const demo = diagnostics?.demo
  const scenarios = demo?.scenarios?.length ? demo.scenarios : FALLBACK_SCENARIOS

  return (
    <section className="demo-console" aria-label="Demo scenarios">
      <div className="demo-console__header">
        <div>
          <span className="panel-label">Demo Mode</span>
          <h2>Scenario Launcher</h2>
        </div>
        <div className="demo-active">
          <FlaskConical size={15} />
          {demo?.active?.replaceAll('_', ' ') ?? 'live'}
        </div>
      </div>

      <div className="scenario-grid">
        {scenarios.map((scenario) => (
          <button
            type="button"
            key={scenario.id}
            className={demo?.active === scenario.id ? 'scenario-button is-active' : 'scenario-button'}
            onClick={() => onScenario(scenario.id)}
            disabled={Boolean(loading)}
          >
            <Play size={14} />
            <strong>{loading === scenario.id ? 'Triggering...' : scenario.label}</strong>
            <span>{scenario.description}</span>
          </button>
        ))}
      </div>
    </section>
  )
}
