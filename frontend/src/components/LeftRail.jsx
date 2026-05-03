import { I } from './Icons'
import { sparkPath, sparkArea } from '../config/floorplan'

export default function LeftRail({ presence, climate, energy, decisions, activeDecisionId, onSelectDecision, climateSpark }) {
  return (
    <aside className="left">
      <div className="rail-section">
        <h3 className="rail-title">Presence</h3>
        <div className="presence-stack">
          {presence.map((p) => (
            <div key={p.id} className="presence-row">
              <div className="avatar is-home" style={{ background: p.color }}>{p.initials}</div>
              <div className="presence-info">
                <strong>{p.name}</strong>
                <span>{p.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rail-section">
        <h3 className="rail-title">Indoor climate</h3>
        <div className="climate-stack">
          <div className="climate-temp">{climate.temp.toFixed(1)}<sup>°C</sup></div>
          <div className="climate-meta">
            <span>{climate.humidity}% humidity</span>
            <span className="dot"/>
            <span>Outside {climate.outside}°</span>
          </div>
          <div className="climate-spark">
            <svg className="spark" viewBox="0 0 200 28" preserveAspectRatio="none">
              <path className="area" d={sparkArea(climateSpark, 200, 28)}/>
              <path d={sparkPath(climateSpark, 200, 28)}/>
            </svg>
          </div>
        </div>
      </div>

      <div className="rail-section">
        <h3 className="rail-title">Energy today</h3>
        <div className="energy-mini">
          <div className="energy-cell">
            <strong>{energy.kwh.toFixed(1)}<span className="unit">kWh</span></strong>
            <span>Used so far</span>
          </div>
          <div className="energy-cell delta">
            <strong>−{energy.savings.toFixed(1)}<span className="unit">kWh</span></strong>
            <span>AI savings</span>
          </div>
        </div>
      </div>

      <div className="rail-section">
        <div className="rail-title-row">
          <h3 className="rail-title">Decision feed</h3>
          <span className="mono" style={{ fontSize: 10, color: 'var(--dim)' }}>
            {decisions.length} events
          </span>
        </div>
        <div className="feed">
          {decisions.map((d) => (
            <div key={d.id}
              className={`decision is-${d.kind} ${activeDecisionId === d.id ? 'is-active' : ''}`}
              onClick={() => onSelectDecision(d.id)}>
              <div className="decision-bullet"/>
              <div className="decision-body">
                <div className="decision-head">
                  <strong>{d.title}</strong>
                  <time className="mono">{d.at}</time>
                </div>
                <div className="decision-reason">{d.reason}</div>
                <span className="decision-tag">{d.tag}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
