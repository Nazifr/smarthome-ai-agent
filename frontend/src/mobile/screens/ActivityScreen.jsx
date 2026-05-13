import React from 'react'

const ROOM_NAMES = {
  living_room: 'Living Room',
  bedroom:     'Bedroom',
  kitchen:     'Kitchen',
  bathroom:    'Bathroom',
  hallway:     'Hallway',
  office:      'Office',
}

// Per-room accent hues (oklch) — same palette as desktop room cards
const ROOM_HUE = {
  living_room: { bg: 'oklch(88% 0.07 65)',  fg: 'oklch(44% 0.14 55)'  },
  bedroom:     { bg: 'oklch(88% 0.06 290)', fg: 'oklch(44% 0.12 285)' },
  kitchen:     { bg: 'oklch(88% 0.07 155)', fg: 'oklch(40% 0.14 150)' },
  bathroom:    { bg: 'oklch(88% 0.06 220)', fg: 'oklch(42% 0.12 220)' },
  hallway:     { bg: 'oklch(87% 0.04 60)',  fg: 'oklch(48% 0.07 55)'  },
  office:      { bg: 'oklch(88% 0.07 300)', fg: 'oklch(44% 0.13 300)' },
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

function pipClass(action) {
  const cmd = (action.command ?? '').toUpperCase()
  const dev = (action.device ?? '').toLowerCase()
  if (dev.includes('smoke') || dev.includes('alert')) return 'alert'
  if (cmd === 'OFF') return 'dim'
  if (dev.includes('ac') || dev.includes('thermo')) return 'cool'
  if (dev.includes('fan')) return 'green'
  return 'terra'
}

function formatReason(reason) {
  if (!reason) return ''
  // Translate common Turkish ML context labels
  return reason
    .replace('ML kararı: is_modu', 'ML decision: work mode')
    .replace('ML kararı: ev_bos', 'ML decision: home empty')
    .replace('ML kararı: gece_modu', 'ML decision: night mode')
    .replace('ML kararı: aktif_ev', 'ML decision: active home')
    .replace('ML kararı:', 'ML decision:')
}

export default function ActivityScreen({ diag, overview }) {
  const actions = diag?.ai?.recent_actions ?? []
  const hasAlerts = (overview?.rooms ?? []).some(r => Number(r.smoke) > 0)

  return (
    <>
      <div className="m-greet-eyebrow">Activity</div>
      <h2 className="m-greet-h" style={{ fontSize: '26px', marginBottom: '4px' }}>
        What's been <em>happening</em>
      </h2>
      <p className="m-greet-sub" style={{ marginBottom: '0' }}>
        {actions.length > 0
          ? `${actions.length} AI decision${actions.length !== 1 ? 's' : ''} in this session.`
          : 'No activity yet. Trigger a demo scene to see AI decisions.'}
      </p>

      {/* Live pill */}
      <div className="m-activity-live" style={{ marginTop: '14px' }}>
        <span className="m-live-dot" />
        <span>Updating live</span>
      </div>

      {/* Smoke alert banner */}
      {hasAlerts && (
        <div className="m-alert-banner" style={{ marginTop: '12px' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Smoke detected in one or more rooms
        </div>
      )}

      {/* AI status badges */}
      {diag && (
        <div className="m-activity-status-row">
          <div className={`m-activity-status-badge${diag.ai?.armed ? ' armed' : ''}`}>
            <span className={`m-live-dot${diag.ai?.armed ? '' : ' dim'}`} />
            {diag.ai?.armed ? 'AI Armed' : 'AI Standby'}
          </div>
          {diag.demo?.active && diag.demo.active !== 'live' && (
            <div className="m-activity-status-badge scene">
              Demo: {diag.demo.active.replace(/_/g, ' ')}
            </div>
          )}
        </div>
      )}

      {/* Feed */}
      <div className="m-sec-title" style={{ marginTop: '18px' }}>
        <span>AI Decisions</span>
        {actions.length > 0 && (
          <span style={{
            fontSize: '11px', color: 'var(--m-muted)',
            fontFamily: 'Inter,sans-serif', textTransform: 'none', letterSpacing: '0.04em',
          }}>
            {actions.length} total
          </span>
        )}
      </div>

      {actions.length === 0 ? (
        <div className="m-empty-msg">
          No decisions yet.<br />Trigger a scene to watch the AI respond.
        </div>
      ) : (
        <div className="m-activity-feed">
          {[...actions].reverse().map((action, i) => {
            const roomKey = action.room ?? ''
            const roomName = ROOM_NAMES[roomKey] ?? roomKey ?? 'Unknown'
            const hue = ROOM_HUE[roomKey]
            const device = (action.device ?? '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
            const isOn = (action.command ?? '').toUpperCase() !== 'OFF'

            return (
              <div key={i} className="m-activity-row">
                <span className={`m-activity-pip ${pipClass(action)}`} />
                <div className="m-activity-body">
                  <div className="m-activity-title-row">
                    {hue && (
                      <span className="m-activity-room-chip" style={{ background: hue.bg, color: hue.fg }}>
                        {roomName}
                      </span>
                    )}
                    {!hue && <span className="m-activity-title">{roomName}</span>}
                    <span className="m-activity-device">{device}</span>
                  </div>
                  <div className="m-activity-cmd-row">
                    <span className={`m-activity-cmd${isOn ? ' is-on' : ' is-off'}`}>
                      {action.command ?? ''}
                    </span>
                    {action.context && (
                      <span className="m-activity-ctx">{action.context.replace(/_/g, ' ')}</span>
                    )}
                    {action.time && (
                      <span className="m-activity-time">{formatTime(action.time)}</span>
                    )}
                  </div>
                  {action.reason && (
                    <div className="m-activity-reason">{formatReason(action.reason)}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}
