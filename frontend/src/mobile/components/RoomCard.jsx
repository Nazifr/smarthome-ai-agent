import React from 'react'

const ROOM_ICONS = {
  living_room: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 9V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v2"/>
      <path d="M2 9h20v2a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V9z"/>
      <path d="M4 15v4M20 15v4"/>
    </svg>
  ),
  bedroom: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 7h20M2 7v10M22 7v10M2 17h20M7 7v4M17 7v4M2 12h20"/>
    </svg>
  ),
  kitchen: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 2v11M12 2v3M17 2v7M3 13h18v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7z"/>
    </svg>
  ),
  bathroom: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 6a3 3 0 0 1 6 0v6H9V6z"/>
      <path d="M2 12h20v4a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4v-4z"/>
    </svg>
  ),
  hallway: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <path d="M3 9h18M3 15h18M9 9v6M15 9v6"/>
    </svg>
  ),
}

const defaultIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
  </svg>
)

export default function RoomCard({ room, onClick }) {
  const isActive = room.devicesOn > 0
  const hasAlert = room.smoke

  return (
    <button
      className={`m-room-card${isActive ? ' is-on' : ''}${hasAlert ? ' is-alert' : ''}`}
      data-room={room.id}
      onClick={() => onClick(room.id)}
    >
      <div className="m-room-icn">
        {ROOM_ICONS[room.id] || defaultIcon}
      </div>
      <div className="m-room-nm">{room.name}</div>
      <div className="m-room-st">{room.status.text}</div>
      {room.motion && <div className="m-occ-dot" />}
    </button>
  )
}
