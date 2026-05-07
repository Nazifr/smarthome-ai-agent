import React, { useEffect, useState } from 'react'
import DeviceRow from '../components/DeviceRow.jsx'
import { adaptRoom } from '../adapters.js'
import { getRoomHistory } from '../../services/api.js'

function Sparkline({ points }) {
  if (!points || points.length < 2) return null
  const vals = points.map(p => p.value)
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min || 1
  const w = 200
  const h = 40
  const pad = 2
  const d = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * w
    const y = pad + (1 - (v - min) / range) * (h - pad * 2)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')

  return (
    <div className="m-sparkline-card">
      <div className="m-sparkline-header">
        <span className="m-sparkline-label">Temperature · 1h</span>
        <span className="m-sparkline-range">{min.toFixed(1)}° – {max.toFixed(1)}°</span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="m-sparkline-svg" preserveAspectRatio="none">
        <path d={d} fill="none" stroke="var(--m-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

export default function RoomScreen({ overview, roomId, onBack, onToggleDevice }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    let cancelled = false
    getRoomHistory(roomId, 'temperature', 60)
      .then(pts => { if (!cancelled) setHistory(pts) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [roomId])

  const data = adaptRoom(overview, roomId)

  if (!data) {
    return (
      <>
        <button className="m-back-btn" onClick={onBack} aria-label="Back" style={{ marginBottom: '16px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
        </button>
        <div className="m-loading">Room not found</div>
      </>
    )
  }

  const humPct = data.humidity != null ? Math.round(Math.max(0, Math.min(100, data.humidity))) : null
  const circumference = 2 * Math.PI * 42
  const dashOffset = humPct != null ? circumference * (1 - humPct / 100) : circumference

  return (
    <>
      {/* Hero banner */}
      <div className="m-room-hero">
        <div className="m-hero-top">
          <button className="m-back-btn" onClick={onBack} aria-label="Back">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15,18 9,12 15,6"/>
            </svg>
          </button>
          <div style={{ display: 'flex', gap: '6px' }}>
            {data.smoke && <span className="m-badge m-badge-alert">Smoke</span>}
            {data.motion && <span className="m-badge m-badge-accent">Occupied</span>}
          </div>
        </div>
        <div className="m-hero-body">
          <p className="m-hero-name">{data.name}</p>
          <p className="m-hero-meta">{data.devicesOn} of {data.devices.length} devices on</p>
        </div>
        <div className="m-hero-temp">
          {data.temp != null ? data.temp.toFixed(1) : '—'}<sup>°</sup>
        </div>
      </div>

      {/* Humidity dial */}
      {humPct != null && (
        <div className="m-dial-card">
          <svg className="m-dial" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--m-bg-soft)" strokeWidth="8"/>
            <circle
              cx="50" cy="50" r="42"
              fill="none"
              stroke="var(--m-accent)"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              transform="rotate(-90 50 50)"
              style={{ transition: '0.6s ease' }}
            />
            <text x="50" y="46" textAnchor="middle" fill="var(--m-text)" fontFamily="Fraunces, serif" fontSize="20" fontWeight="400">{humPct}</text>
            <text x="50" y="62" textAnchor="middle" fill="var(--m-muted)" fontFamily="Inter, sans-serif" fontSize="9">% humid</text>
          </svg>
          <div className="m-dial-info">
            <div className="m-dial-lbl">Humidity</div>
            <div className="m-dial-val">{humPct}<sup>%</sup></div>
            <div className="m-dial-desc">
              {humPct < 30 ? 'Dry — consider a humidifier' :
               humPct > 70 ? 'High — ventilate the room' :
               'Comfortable range'}
            </div>
          </div>
        </div>
      )}

      {/* Temperature history sparkline */}
      <Sparkline points={history} />

      {/* Devices */}
      <div className="m-sec-title">
        <span>Devices</span>
        <span style={{ fontSize: '11px', color: 'var(--m-accent)', fontFamily: 'Inter,sans-serif', textTransform: 'none', letterSpacing: '0.04em' }}>
          {data.devicesOn} on
        </span>
      </div>

      {data.devices.length === 0 ? (
        <p className="m-empty-msg">No devices configured in this room.</p>
      ) : (
        data.devices.map(device => (
          <DeviceRow
            key={device.id}
            device={device}
            onToggle={(key) => onToggleDevice(roomId, key)}
          />
        ))
      )}
    </>
  )
}
