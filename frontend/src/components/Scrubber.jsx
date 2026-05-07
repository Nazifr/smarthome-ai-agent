import { I } from './Icons'

const SCENARIOS = [
  { id: 'live',          name: 'Live data',         desc: 'Resume real sensors' },
  { id: 'evening',       name: 'Evening wind-down', desc: 'Warm light, low volume' },
  { id: 'kitchen_smoke', name: 'Kitchen smoke',     desc: 'Safety alarm scenario' },
  { id: 'empty',         name: 'Empty home',        desc: 'Energy-saving mode' },
  { id: 'morning',       name: 'Morning routine',   desc: 'Gradual wake' },
]

const bars = Array.from({ length: 60 }, (_, i) => {
  const phase = Math.sin(i / 6) * 0.5 + 0.5
  const noise = ((i * 9301 + 49297) % 233280) / 233280
  return Math.max(0.08, phase * 0.7 + noise * 0.4)
})

export default function Scrubber({ time, onSeek, playing, onTogglePlay, activeScenario, onScenario }) {
  const handleClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    onSeek(Math.max(0, Math.min(1, x)))
  }

  return (
    <footer className="footer">
      <div className="scrub-info">
        <span>Replay last 60 min</span>
        <span className="pill">−{Math.round((1 - time) * 60)}m</span>
      </div>

      <div className="scrub">
        <button className="play-btn" onClick={onTogglePlay} aria-label={playing ? 'Pause' : 'Play'}>
          {playing ? <I.Pause/> : <I.Play/>}
        </button>
        <div className="scrub-track" onClick={handleClick}>
          <svg viewBox="0 0 600 28" preserveAspectRatio="none">
            {bars.map((h, i) => (
              <rect key={i}
                x={i * 10 + 1} y={28 - h * 24}
                width="6" height={h * 24} rx="1"
                fill={i / 60 <= time ? 'var(--accent)' : 'var(--line-2)'}
                opacity={i / 60 <= time ? 0.9 : 1}/>
            ))}
          </svg>
          <div className="scrub-handle" style={{ left: `${time * 100}%` }}/>
        </div>
      </div>

      <div className="scrub-actions">
        {SCENARIOS.map((s) => (
          <button key={s.id}
            className={`ghost-btn ${activeScenario === s.id ? 'is-active' : ''}`}
            onClick={() => onScenario(s.id)}
            title={s.desc}>
            {s.name}
          </button>
        ))}
      </div>
    </footer>
  )
}
