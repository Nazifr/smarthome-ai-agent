import React from 'react'

const ICONS = {
  lightbulb: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18h6M10 22h4M12 2a7 7 0 0 1 4.9 11.9C16 15 15 16 15 17H9c0-1-1-2-1.9-3.1A7 7 0 0 1 12 2z"/>
    </svg>
  ),
  fan: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="2"/>
      <path d="M12 2a3 3 0 0 1 3 3c0 2-1 4-3 5V2zM22 12a3 3 0 0 1-3 3c-2 0-4-1-5-3h8zM12 22a3 3 0 0 1-3-3c0-2 1-4 3-5v8zM2 12a3 3 0 0 1 3-3c2 0 4 1 5 3H2z"/>
    </svg>
  ),
  thermo: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>
    </svg>
  ),
  speaker: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="20" rx="3"/>
      <circle cx="12" cy="13" r="3"/>
      <circle cx="12" cy="6" r="1" fill="currentColor" stroke="none"/>
    </svg>
  ),
  lock: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  ),
}

const defaultIcon = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4"/>
    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
  </svg>
)

const STATE_LABELS = {
  ON: 'On', OFF: 'Off', DIM: 'Dimmed', COOL_LOW: 'Cool (low)',
  COOL_HIGH: 'Cool (high)', HEAT: 'Heating',
}

export default function DeviceRow({ device, onToggle }) {
  // device.key holds the raw actuator state from the backend after adaptRoom
  // Resolve a display label from the raw state coming through
  const rawState = device.rawState
  const stateLabel = STATE_LABELS[rawState] || (device.on ? 'On' : 'Off')

  return (
    <div className={`m-device-row${device.on ? ' is-on' : ''}`}>
      <div className="m-device-icn">
        {ICONS[device.icon] || defaultIcon}
      </div>
      <div className="m-device-info">
        <div className="m-device-nm">{device.name}</div>
        <div className="m-device-st">{stateLabel}</div>
      </div>
      <button
        className={`m-switch${device.on ? ' is-on' : ''}`}
        onClick={() => onToggle(device.key)}
        aria-label={`Toggle ${device.name}`}
        aria-pressed={device.on}
      />
    </div>
  )
}
