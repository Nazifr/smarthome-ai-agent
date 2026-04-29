import { motion } from 'framer-motion'
import { Grid2X2, Map } from 'lucide-react'
import { useState } from 'react'
import FloorPlan from './FloorPlan'
import RoomCard from './RoomCard'

export default function RoomGrid({ rooms, selectedRoomId, localStates, onRoomClick }) {
  const [view, setView] = useState('cards')

  return (
    <section className="room-section" aria-label="Room telemetry">
      <div className="section-heading">
        <div>
          <span className="panel-label">Room Topology</span>
          <h2>{view === 'floor' ? 'Floor Plan Intelligence' : 'Live Floor Intelligence'}</h2>
        </div>
        <div className="section-actions">
          <div className="view-toggle" aria-label="Room view selector">
            <button
              type="button"
              className={view === 'cards' ? 'is-active' : ''}
              onClick={() => setView('cards')}
            >
              <Grid2X2 size={15} />
              Cards
            </button>
            <button
              type="button"
              className={view === 'floor' ? 'is-active' : ''}
              onClick={() => setView('floor')}
            >
              <Map size={15} />
              Plan
            </button>
          </div>
          <div className="scan-badge">
            <span />
            Scanning {rooms.length} rooms
          </div>
        </div>
      </div>

      {view === 'floor' ? (
        <FloorPlan rooms={rooms} selectedRoomId={selectedRoomId} onRoomClick={onRoomClick} />
      ) : (
        <motion.div
          className="room-map"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: { staggerChildren: 0.07 },
            },
          }}
        >
          {rooms.map((room, index) => (
            <RoomCard
              key={room.room_id}
              room={room}
              index={index}
              selected={room.room_id === selectedRoomId}
              localStates={localStates}
              onClick={() => onRoomClick(room.room_id)}
            />
          ))}
        </motion.div>
      )}
    </section>
  )
}
