import React from 'react'

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

        return (
          <button
            key={room.id}
            className={cls}
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
                {room.temp != null ? room.temp.toFixed(0) : '—'}
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
