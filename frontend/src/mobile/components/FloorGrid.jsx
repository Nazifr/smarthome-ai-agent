import React from 'react'

// Per-room identity hues (oklch) — subtle wall tint for inactive, stronger when active
const ROOM_TINTS = {
  living_room: { h: 30,  c: 0.018 },   // warm amber
  bedroom:     { h: 260, c: 0.016 },   // soft violet
  kitchen:     { h: 140, c: 0.016 },   // sage green
  bathroom:    { h: 200, c: 0.018 },   // cool aqua
  hallway:     { h: 55,  c: 0.014 },   // neutral gold
  office:      { h: 220, c: 0.016 },   // slate blue
}

function roomTintStyle(roomId, isActive) {
  const t = ROOM_TINTS[roomId]
  if (!t) return {}
  const l = isActive ? 0.22 : 0.18
  const c = isActive ? t.c * 1.6 : t.c
  return { background: `oklch(${l} ${c} ${t.h})` }
}

function glowClass(room) {
  if (room.smoke) return 'alert'
  if (room.deviceTypes.includes('ac')) return 'ac'
  if (room.deviceTypes.includes('fan')) return 'fan'
  if (room.deviceTypes.includes('light')) return 'light'
  return null
}

export default function FloorGrid({ rooms, onRoomClick }) {
  return (
    <div className="m-floor-grid">
      {rooms.map(room => {
        const gc = glowClass(room)
        const isActive = room.devicesOn > 0
        const cls = [
          'm-floor-cell',
          room.smoke ? 'is-alert' : isActive ? 'is-active' : '',
        ].filter(Boolean).join(' ')

        const tintStyle = room.smoke ? {} : roomTintStyle(room.id, isActive)

        return (
          <button
            key={room.id}
            className={cls}
            style={tintStyle}
            onClick={() => onRoomClick(room.id)}
            aria-label={`Open ${room.name}`}
          >
            {/* radial glow overlay */}
            {gc && <div className={`m-cell-glow glow-${gc}`} />}

            <div className="m-cell-top">
              <span className="m-cell-name">{room.name}</span>
              <div className="m-dev-dots">
                {room.deviceTypes.includes('light') && <span className="m-dev-dot light" title="Light on" />}
                {room.deviceTypes.includes('ac')    && <span className="m-dev-dot ac"    title="AC on" />}
                {room.deviceTypes.includes('fan')   && <span className="m-dev-dot fan"   title="Fan on" />}
              </div>
            </div>

            <div className="m-cell-bottom">
              <span className="m-cell-temp">
                {room.temp != null ? room.temp.toFixed(1) : '—'}
                <span className="m-cell-deg">°</span>
              </span>
              <span className="m-cell-humidity">
                {room.humidity != null ? `${Math.round(room.humidity)}%` : ''}
              </span>
              <div className="m-cell-indicators">
                {room.smoke  && <span className="m-cell-dot alert" />}
                {room.motion && !room.smoke && <span className="m-cell-dot occ" />}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
