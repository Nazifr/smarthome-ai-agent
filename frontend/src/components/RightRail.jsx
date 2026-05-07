import { I } from './Icons'
import { ROOMS } from '../config/floorplan'
import { sparkPath, sparkArea } from '../config/floorplan'

export default function RightRail({ roomId, sensors, alert, devices, onToggleDevice, activeDecision, sparkData }) {
  const room = ROOMS[roomId]
  if (!room) return null

  const s = sensors[roomId] || {}
  const tempCls = s.temp > 26 || s.temp < 18 ? 'is-warn' : ''
  const humCls = s.humidity > 65 ? 'is-warn' : ''
  const co2Cls = s.co2 > 800 ? 'is-warn' : ''
  const smokeCls = s.smoke ? 'is-alert' : ''

  return (
    <aside className="right">
      <div className="right-head">
        <div className="right-eyebrow">{alert ? 'Active alert' : 'Room detail'}</div>
        <h2 className="right-title">{room.name}</h2>
        <div className="right-sub">
          {s.motion ? 'Occupied · ' : 'Vacant · '}
          {devices.filter(d => d.on).length} of {devices.length} devices on
        </div>
      </div>
      <div className="right-body">
        {activeDecision && (
          <div className="trace-card">
            <div className="trace-head">
              <I.Sparkles/> Decision trace
            </div>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>{activeDecision.title}</div>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>{activeDecision.reason}</div>
            <div className="trace-flow">
              {activeDecision.trace.map((step, i) => (
                <div key={i} className="trace-step">
                  <div className="trace-num">{i + 1}</div>
                  <div className="trace-text">
                    <strong>{step.label}</strong> <span>· {step.text}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="sensor-grid">
          <div className="sensor-card">
            <div className="label">Temperature</div>
            <div className={`value ${tempCls}`}>{s.temp?.toFixed(1) ?? '—'}<span className="unit">°C</span></div>
            <svg className="spark" viewBox="0 0 100 28" preserveAspectRatio="none" style={{ marginTop: 6 }}>
              <path className="area" d={sparkArea(sparkData.temp, 100, 28)}/>
              <path d={sparkPath(sparkData.temp, 100, 28)}/>
            </svg>
          </div>
          <div className="sensor-card">
            <div className="label">Humidity</div>
            <div className={`value ${humCls}`}>{s.humidity ?? '—'}<span className="unit">%</span></div>
            <svg className="spark" viewBox="0 0 100 28" preserveAspectRatio="none" style={{ marginTop: 6 }}>
              <path className="area" d={sparkArea(sparkData.humidity, 100, 28)}/>
              <path d={sparkPath(sparkData.humidity, 100, 28)}/>
            </svg>
          </div>
          <div className="sensor-card">
            <div className="label">Light</div>
            <div className="value">{s.lux ?? '—'}<span className="unit">lux</span></div>
          </div>
          <div className="sensor-card">
            <div className="label">CO₂</div>
            <div className={`value ${co2Cls}`}>{s.co2 ?? '—'}<span className="unit">ppm</span></div>
          </div>
          {('smoke' in s) && (
            <div className="sensor-card" style={{ gridColumn: '1 / -1' }}>
              <div className="label">Smoke</div>
              <div className={`value ${smokeCls}`}>{s.smoke ? 'Detected' : 'Clear'}</div>
            </div>
          )}
        </div>

        <h3 className="rail-title" style={{ margin: '4px 0 10px' }}>Devices</h3>
        <div className="device-list">
          {devices.map((d) => {
            const Ico = I[d.icon] || I.Lightbulb
            return (
              <div key={d.id} className={`device-row ${d.on ? 'is-on' : ''}`}>
                <div className="device-icon"><Ico/></div>
                <div className="device-info">
                  <div className="device-name">{d.name}</div>
                  <div className="device-meta">{d.meta}</div>
                </div>
                <button
                  className={`toggle ${d.on ? 'is-on' : ''}`}
                  onClick={() => onToggleDevice(d.id, d.roomId, d.deviceKey)}
                  aria-label={`Toggle ${d.name}`}/>
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
