import React, { useEffect, useRef, useState } from 'react'
import DeviceRow from './DeviceRow.jsx'
import { adaptRoom } from '../adapters.js'
import { getRoomHistory } from '../../services/api.js'

function Sparkline({ points }) {
  if (!points || points.length < 2) return null
  const vals = points.map(p => p.value)
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min || 1
  const W = 260; const H = 44; const pad = 2
  const d = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * W
    const y = pad + (1 - (v - min) / range) * (H - pad * 2)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  return (
    <div className="m-sparkline-card" style={{ marginBottom: 12 }}>
      <div className="m-sparkline-header">
        <span className="m-sparkline-label">Temp · 1h</span>
        <span className="m-sparkline-range">{min.toFixed(1)}° – {max.toFixed(1)}°</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="m-sparkline-svg" preserveAspectRatio="none">
        <path d={d} fill="none" stroke="var(--m-accent)" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </div>
  )
}

export default function RoomSheet({ overview, roomId, onClose, onToggleDevice }) {
  const [history, setHistory] = useState([])
  const isOpen = Boolean(roomId)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (!roomId) { setHistory([]); return }
    // scroll to top when room changes
    if (scrollRef.current) scrollRef.current.scrollTop = 0
    let cancelled = false
    getRoomHistory(roomId, 'temperature', 60)
      .then(pts => { if (!cancelled) setHistory(pts) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [roomId])

  const data = roomId ? adaptRoom(overview, roomId) : null

  const humPct = data?.humidity != null
    ? Math.round(Math.max(0, Math.min(100, data.humidity)))
    : null

  return (
    <>
      {/* Backdrop */}
      <div
        className={`m-sheet-backdrop${isOpen ? ' is-open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sheet panel */}
      <div
        className={`m-sheet${isOpen ? ' is-open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={data?.name ?? 'Room'}
      >
        {/* Drag handle */}
        <div className="m-sheet-handle" onClick={onClose} />

        {data && (
          <>
            {/* Header */}
            <div className="m-sheet-header">
              <div className="m-sheet-header-left">
                <div className="m-sheet-room-name">{data.name}</div>
                <div className="m-sheet-room-meta">
                  {data.devicesOn} of {data.devices.length} devices on
                  {data.motion && !data.smoke && ' · Occupied'}
                  {data.smoke && ' · Smoke alert'}
                </div>
              </div>
              <button className="m-sheet-close" onClick={onClose} aria-label="Close room">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            {/* Quick stats strip */}
            <div className="m-sheet-stats">
              <div className="m-sheet-stat">
                <span className="m-sheet-stat-v">
                  {data.temp != null ? data.temp.toFixed(1) : '—'}°
                </span>
                <span className="m-sheet-stat-l">Temp</span>
              </div>
              <div className="m-sheet-stat-divider" />
              <div className="m-sheet-stat">
                <span className="m-sheet-stat-v">
                  {humPct != null ? `${humPct}%` : '—'}
                </span>
                <span className="m-sheet-stat-l">Humidity</span>
              </div>
              <div className="m-sheet-stat-divider" />
              <div className="m-sheet-stat">
                <span className="m-sheet-stat-v">{data.devicesOn}</span>
                <span className="m-sheet-stat-l">Active</span>
              </div>
            </div>

            {/* Scrollable body */}
            <div className="m-sheet-scroll" ref={scrollRef}>
              {/* Smoke alert banner */}
              {data.smoke && (
                <div className="m-alert-banner" style={{ marginBottom: 14 }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  Smoke detected — ventilate immediately
                </div>
              )}

              {/* Humidity comfort message */}
              {humPct != null && (
                <div className="m-sheet-comfort">
                  {humPct < 30
                    ? 'Dry air — consider a humidifier'
                    : humPct > 70
                    ? 'High humidity — ventilate the room'
                    : 'Comfortable humidity range'}
                </div>
              )}

              {/* Temperature sparkline */}
              <Sparkline points={history} />

              {/* Devices */}
              <div className="m-sec-title">
                <span>Devices</span>
                <span style={{
                  fontSize: '11px', color: 'var(--m-accent)',
                  fontFamily: 'Inter,sans-serif', textTransform: 'none',
                  letterSpacing: '0.04em',
                }}>
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
                    onToggle={key => onToggleDevice(roomId, key)}
                  />
                ))
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}
