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

const MODE_LABELS = { AI: 'Auto', Manual: 'Manual', Static: 'Away' }

function formatTime(ts) {
  if (!ts) return ''
  try { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  catch { return '' }
}

function formatReason(reason) {
  if (!reason) return ''
  return reason
    .replace('ML kararı: is_modu',   'ML decision: work mode')
    .replace('ML kararı: ev_bos',    'ML decision: home empty')
    .replace('ML kararı: gece_modu', 'ML decision: night mode')
    .replace('ML kararı: aktif_ev',  'ML decision: active home')
    .replace('ML kararı:', 'ML decision:')
}

function pipClassForDevice(device, command) {
  const dev = (device ?? '').toLowerCase()
  const cmd = (command ?? '').toUpperCase()
  if (cmd === 'OFF') return 'dim'
  if (dev.includes('ac') || dev.includes('thermo')) return 'cool'
  if (dev.includes('fan')) return 'green'
  return 'terra'
}

// Merge + sort all event sources, newest first, max 20
function buildFeed(diagActions, activityLog) {
  const aiEvents = (diagActions ?? []).map(a => ({ ...a, type: 'ai' }))
  const localEvents = (activityLog ?? [])   // already have type set
  const all = [...aiEvents, ...localEvents]
  all.sort((a, b) => new Date(b.time) - new Date(a.time))
  return all.slice(0, 20)
}

// ── Mode change row ────────────────────────────────────────────────
function ModeRow({ event }) {
  const label = MODE_LABELS[event.command] ?? event.command
  const icon = event.command === 'AI'
    ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l2.4 7.4L22 12l-7.6 2.6L12 22l-2.4-7.4L2 12l7.6-2.6L12 2z"/></svg>
    : event.command === 'Static'
    ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/><line x1="12" y1="3" x2="12" y2="9.5"/></svg>

  return (
    <div className="m-activity-mode-row">
      <div className="m-activity-mode-icon">{icon}</div>
      <div className="m-activity-body">
        <div className="m-activity-mode-label">
          Mode → <strong>{label}</strong>
        </div>
        {event.reason && (
          <div className="m-activity-reason">{event.reason}</div>
        )}
      </div>
      <span className="m-activity-time">{formatTime(event.time)}</span>
    </div>
  )
}

// ── Device event row ───────────────────────────────────────────────
function DeviceRow({ event }) {
  const roomKey  = event.room ?? ''
  const roomName = ROOM_NAMES[roomKey] ?? roomKey ?? 'Unknown'
  const hue      = ROOM_HUE[roomKey]
  const device   = (event.device ?? '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  const isOn     = (event.command ?? '').toUpperCase() !== 'OFF'
  const pip      = event.type === 'manual' ? 'manual' : pipClassForDevice(event.device, event.command)

  return (
    <div className="m-activity-row">
      <span className={`m-activity-pip ${pip}`} />
      <div className="m-activity-body">
        <div className="m-activity-title-row">
          {hue
            ? <span className="m-activity-room-chip" style={{ background: hue.bg, color: hue.fg }}>{roomName}</span>
            : <span className="m-activity-title">{roomName}</span>
          }
          <span className="m-activity-device">{device}</span>
          {event.type === 'manual' && (
            <span className="m-activity-source">manual</span>
          )}
        </div>
        <div className="m-activity-cmd-row">
          <span className={`m-activity-cmd${isOn ? ' is-on' : ' is-off'}`}>{event.command}</span>
          {event.context && (
            <span className="m-activity-ctx">{event.context.replace(/_/g, ' ')}</span>
          )}
          <span className="m-activity-time">{formatTime(event.time)}</span>
        </div>
        {event.reason && event.type !== 'manual' && (
          <div className="m-activity-reason">{formatReason(event.reason)}</div>
        )}
      </div>
    </div>
  )
}

// ── Main screen ────────────────────────────────────────────────────
export default function ActivityScreen({ diag, overview, activityLog }) {
  const feed = buildFeed(diag?.ai?.recent_actions, activityLog)
  const hasAlerts = (overview?.rooms ?? []).some(r => Number(r.smoke) > 0)

  return (
    <>
      <div className="m-greet-eyebrow">Activity</div>
      <h2 className="m-greet-h" style={{ fontSize: '26px', marginBottom: '4px' }}>
        What's been <em>happening</em>
      </h2>
      <p className="m-greet-sub" style={{ marginBottom: '0' }}>
        {feed.length > 0
          ? `${feed.length} event${feed.length !== 1 ? 's' : ''} — AI decisions, manual overrides, mode changes.`
          : 'No activity yet. Trigger a demo scene or toggle a device.'}
      </p>

      {/* Live pill */}
      <div className="m-activity-live" style={{ marginTop: '14px' }}>
        <span className="m-live-dot" />
        <span>Updating live</span>
      </div>

      {/* Smoke alert */}
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

      {/* Status badges */}
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

      {/* Feed legend */}
      <div className="m-sec-title" style={{ marginTop: '18px' }}>
        <span>All Events</span>
        <div className="m-activity-legend">
          <span><span className="m-activity-pip terra" style={{ display:'inline-block' }} /> AI</span>
          <span><span className="m-activity-pip manual" style={{ display:'inline-block' }} /> Manual</span>
        </div>
      </div>

      {feed.length === 0 ? (
        <div className="m-empty-msg">
          No events yet.<br />Trigger a scene or toggle a device.
        </div>
      ) : (
        <div className="m-activity-feed">
          {feed.map((event, i) =>
            event.type === 'mode'
              ? <ModeRow key={i} event={event} />
              : <DeviceRow key={i} event={event} />
          )}
        </div>
      )}
    </>
  )
}
