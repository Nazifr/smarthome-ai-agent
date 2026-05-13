import React from 'react'

const ROOM_NAMES = {
  living_room: 'Living Room',
  bedroom:     'Bedroom',
  kitchen:     'Kitchen',
  bathroom:    'Bathroom',
  hallway:     'Hallway',
  office:      'Office',
}

const ROOM_HUE = {
  living_room: { bg: 'oklch(88% 0.07 65)',  fg: 'oklch(44% 0.14 55)'  },
  bedroom:     { bg: 'oklch(88% 0.06 290)', fg: 'oklch(44% 0.12 285)' },
  kitchen:     { bg: 'oklch(88% 0.07 155)', fg: 'oklch(40% 0.14 150)' },
  bathroom:    { bg: 'oklch(88% 0.06 220)', fg: 'oklch(42% 0.12 220)' },
  hallway:     { bg: 'oklch(87% 0.04 60)',  fg: 'oklch(48% 0.07 55)'  },
  office:      { bg: 'oklch(88% 0.07 300)', fg: 'oklch(44% 0.13 300)' },
}

const PIPELINE = [
  {
    id: 'sensors',
    label: 'Sensors',
    desc: 'Temp · Humidity · Motion · Smoke',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>
      </svg>
    ),
  },
  {
    id: 'context',
    label: 'Context',
    desc: 'Time · Weather · Occupancy',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12,6 12,12 16,14"/>
      </svg>
    ),
  },
  {
    id: 'brain',
    label: 'LightGBM',
    desc: '2s cycle · ML model',
    accent: true,
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2l2.4 7.4L22 12l-7.6 2.6L12 22l-2.4-7.4L2 12l7.6-2.6L12 2z"/>
      </svg>
    ),
  },
  {
    id: 'actions',
    label: 'Actions',
    desc: 'Light · AC · Fan · Alerts',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
    ),
  },
]

const MODES = [
  {
    id: 'AI',
    label: 'Auto',
    desc: 'NeuroNest decides',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2l2.4 7.4L22 12l-7.6 2.6L12 22l-2.4-7.4L2 12l7.6-2.6L12 2z"/>
      </svg>
    ),
  },
  {
    id: 'Manual',
    label: 'Manual',
    desc: 'Full control',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/>
        <line x1="12" y1="3" x2="12" y2="9.5"/>
      </svg>
    ),
  },
  {
    id: 'Static',
    label: 'Away',
    desc: 'Low power',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    ),
  },
]

function formatReason(reason) {
  if (!reason) return ''
  return reason
    .replace('ML kararı: is_modu', 'ML decision: work mode')
    .replace('ML kararı: ev_bos', 'ML decision: home empty')
    .replace('ML kararı: gece_modu', 'ML decision: night mode')
    .replace('ML kararı: aktif_ev', 'ML decision: active home')
    .replace('ML kararı:', 'ML decision:')
}

export default function AiScreen({ diag, mode, onSetMode }) {
  const armed = diag?.ai?.armed ?? false
  const actions = diag?.ai?.recent_actions ?? []
  const recentFive = [...actions].slice(-5).reverse()

  const modeDesc = {
    AI:     'NeuroNest is making automated decisions every 2 seconds based on sensor data, time of day, and learned patterns.',
    Manual: 'All automation is paused. You have direct control over every device.',
    Static: 'Away mode — energy use is minimised, non-essential devices are off.',
  }

  return (
    <>
      <div className="m-greet-eyebrow">Intelligence</div>
      <h2 className="m-greet-h" style={{ fontSize: '26px', marginBottom: '4px' }}>
        NeuroNest <em>decides</em>
      </h2>
      <p className="m-greet-sub">
        {armed
          ? 'AI engine armed — monitoring all 6 rooms in real time.'
          : 'AI engine is in standby mode.'}
      </p>

      {/* Pipeline */}
      <div className="m-pipeline-wrap">
        {PIPELINE.map((step, i) => (
          <React.Fragment key={step.id}>
            <div className={`m-pipeline-step${step.accent ? ' is-accent' : ''}`}>
              <div className="m-pipeline-icon">{step.icon}</div>
              <div className="m-pipeline-label">{step.label}</div>
              <div className="m-pipeline-desc">{step.desc}</div>
            </div>
            {i < PIPELINE.length - 1 && (
              <div className="m-pipeline-arrow" aria-hidden="true">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9,18 15,12 9,6"/>
                </svg>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Stats row */}
      <div className="m-ai-stats-row">
        <div className="m-ai-stat">
          <div className="m-ai-stat-v">6</div>
          <div className="m-ai-stat-l">Rooms</div>
        </div>
        <div className="m-ai-stat">
          <div className="m-ai-stat-v">2s</div>
          <div className="m-ai-stat-l">Cycle</div>
        </div>
        <div className="m-ai-stat">
          <div className="m-ai-stat-v">{actions.length}</div>
          <div className="m-ai-stat-l">Decisions</div>
        </div>
      </div>

      {/* Mode picker */}
      <div className="m-sec-title"><span>System Mode</span></div>
      <div className="m-mode-grid">
        {MODES.map(m => (
          <button
            key={m.id}
            className={`m-mode-btn${mode === m.id ? ' is-active' : ''}`}
            onClick={() => onSetMode(m.id)}
            title={m.desc}
          >
            <div className="m-mode-btn-icon">{m.icon}</div>
            <span>{m.label}</span>
            <span className="m-mode-btn-desc">{m.desc}</span>
          </button>
        ))}
      </div>
      <p className="m-mode-explain">{modeDesc[mode] ?? ''}</p>

      {/* Recent decisions */}
      <div className="m-sec-title" style={{ marginTop: '24px' }}>
        <span>Recent Decisions</span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
          <span className="m-live-dot" style={{ width: '5px', height: '5px' }} />
          <span style={{
            fontSize: '10px', color: 'var(--m-muted)',
            fontFamily: 'Inter,sans-serif', textTransform: 'none', letterSpacing: '0.04em',
          }}>Live</span>
        </span>
      </div>

      {recentFive.length === 0 ? (
        <div className="m-empty-msg">
          No decisions yet — trigger a demo scene to see the AI in action.
        </div>
      ) : (
        <div className="m-decisions-list">
          {recentFive.map((action, i) => {
            const roomKey = action.room ?? ''
            const roomName = ROOM_NAMES[roomKey] ?? roomKey ?? 'Unknown'
            const hue = ROOM_HUE[roomKey]
            const device = (action.device ?? '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
            const isOn = (action.command ?? '').toUpperCase() !== 'OFF'

            return (
              <div key={i} className="m-decision-card">
                {/* Room chip */}
                <div className="m-decision-header">
                  {hue ? (
                    <span className="m-decision-room-chip" style={{ background: hue.bg, color: hue.fg }}>
                      {roomName}
                    </span>
                  ) : (
                    <span className="m-decision-room">{roomName}</span>
                  )}
                  {action.context && (
                    <span className="m-decision-ctx">
                      {action.context.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>

                {/* Device + command */}
                <div className="m-decision-action">
                  <span className="m-decision-actuator">{device}</span>
                  <span className={`m-decision-cmd${isOn ? ' is-on' : ' is-off'}`}>
                    {action.command ?? ''}
                  </span>
                </div>

                {/* Reason */}
                {action.reason && (
                  <div className="m-decision-reason">{formatReason(action.reason)}</div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}
