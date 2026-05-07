import React from 'react'
import DeviceRow from '../components/DeviceRow.jsx'
import { adaptRoom } from '../adapters.js'

export default function RoomScreen({ overview, roomId, onBack, onToggleDevice }) {
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
