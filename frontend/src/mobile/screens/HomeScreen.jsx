import React from 'react'
import FloorGrid from '../components/FloorGrid.jsx'
import { adaptHome } from '../adapters.js'

const SCENES = [
  { id: 'live',               label: 'Live',    icon: '📡' },
  { id: 'night_routine',      label: 'Evening', icon: '🌙' },
  { id: 'empty_home',         label: 'Away',    icon: '🚗' },
  { id: 'kitchen_smoke',      label: 'Smoke',   icon: '🔥' },
  { id: 'bathroom_humidity',  label: 'Shower',  icon: '🚿' },
]

function dayLabel() {
  const d = new Date()
  const days   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const tod    = d.getHours() < 12 ? 'Morning' : d.getHours() < 17 ? 'Afternoon' : 'Evening'
  return `${days[d.getDay()]} · ${months[d.getMonth()]} ${d.getDate()} · ${tod}`
}

function greeting() {
  const h = new Date().getHours()
  if (h < 5)  return 'Late night'
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function HomeScreen({ overview, weather, onRoomClick, onSceneClick, activeScene }) {
  const data = adaptHome(overview)
  if (!data) return <div className="m-loading">Loading…</div>

  const modeLabel = data.mode === 'AI' ? 'Auto' : data.mode === 'Static' ? 'Away' : 'Manual'

  return (
    <>
      <div className="m-greet-eyebrow">{dayLabel()}</div>
      <h2 className="m-greet-h">{greeting()}, <em>your home</em></h2>
      <p className="m-greet-sub">
        {data.activeAlerts > 0
          ? `${data.activeAlerts} alert${data.activeAlerts > 1 ? 's' : ''} need attention.`
          : data.totalDevicesOn > 0
          ? `${data.totalDevicesOn} device${data.totalDevicesOn > 1 ? 's' : ''} running smoothly.`
          : 'Everything is quiet.'}
      </p>

      {/* Summary card */}
      <div className="m-summary-card">
        <div className="m-stat">
          <div className="m-stat-label">Indoor</div>
          <div className="m-stat-v">
            {data.temp != null ? data.temp.toFixed(1) : '—'}<sup>°</sup>
          </div>
          <div className="m-stat-meta">
            {data.humidity != null ? `${data.humidity}% humidity` : 'No data'}
          </div>
        </div>
        <div className="m-stat">
          <div className="m-stat-label">Outside</div>
          {weather?.available ? (
            <>
              <div className="m-stat-v">{Math.round(weather.temperature)}<sup>°</sup></div>
              <div className="m-stat-meta">{weather.condition}</div>
            </>
          ) : (
            <>
              <div className="m-stat-v" style={{ fontSize: '18px', paddingTop: '5px' }}>{modeLabel}</div>
              <div className="m-stat-meta">System mode</div>
            </>
          )}
        </div>
        <div className="m-summary-divider" />
        <div className="m-stat">
          <div className="m-stat-label">Est. today</div>
          <div className="m-stat-v">
            {(8.4 + data.totalDevicesOn * 0.3).toFixed(1)}<sup style={{ fontSize: '11px' }}>kWh</sup>
          </div>
          <div className="m-stat-meta">Estimated</div>
        </div>
        <div className="m-stat">
          <div className="m-stat-label">Devices on</div>
          <div className="m-stat-v">
            {data.totalDevicesOn}<sup style={{ fontSize: '11px' }}>/{data.totalDevices}</sup>
          </div>
          <div className="m-stat-meta">
            {data.activeAlerts > 0
              ? `${data.activeAlerts} alert${data.activeAlerts > 1 ? 's' : ''}`
              : 'All normal'}
          </div>
        </div>
      </div>

      {/* Scenes */}
      <div className="m-sec-title"><span>Scenes</span></div>
      <div className="m-scenes-row">
        {SCENES.map(s => (
          <button
            key={s.id}
            className={`m-scene-pill${activeScene === s.id ? ' is-active' : ''}`}
            onClick={() => onSceneClick(s.id)}
          >
            <span role="img" aria-hidden="true">{s.icon}</span>
            {s.label}
          </button>
        ))}
      </div>

      {/* Floor grid — tap a room to open the sheet */}
      <div className="m-sec-title">
        <span>Rooms</span>
        <span style={{
          fontSize: '11px', color: 'var(--m-accent)',
          fontFamily: 'Inter,sans-serif', textTransform: 'none', letterSpacing: '0.04em',
        }}>
          {data.rooms.length} rooms
        </span>
      </div>
      <FloorGrid rooms={data.rooms} onRoomClick={onRoomClick} />
    </>
  )
}
