const SCENARIOS = [
  { id: 'live',              name: 'Live data',         desc: 'Resume real sensors' },
  { id: 'night_routine',     name: 'Evening wind-down', desc: 'Warm light, low volume' },
  { id: 'kitchen_smoke',     name: 'Kitchen smoke',     desc: 'Safety alarm scenario' },
  { id: 'empty_home',        name: 'Empty home',        desc: 'Energy-saving mode' },
  { id: 'bathroom_humidity', name: 'Bathroom shower',   desc: 'High humidity scenario' },
  { id: 'fair_arriving',     name: 'Arriving home',     desc: 'Mood-based personalisation' },
]

export default function Scrubber({ activeScenario, loadingScenario, onScenario }) {
  return (
    <footer className="footer">
      <div className="scenario-label">
        Demo: {activeScenario.replace(/_/g, ' ')}
      </div>

      <div className="scrub-actions">
        {SCENARIOS.map((s) => (
          <button key={s.id}
            className={`ghost-btn ${activeScenario === s.id ? 'is-active' : ''}`}
            onClick={() => onScenario(s.id)}
            disabled={Boolean(loadingScenario)}
            title={s.desc}>
            {loadingScenario === s.id ? 'Running...' : s.name}
          </button>
        ))}
      </div>
    </footer>
  )
}
