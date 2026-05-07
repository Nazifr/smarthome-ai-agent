import { motion } from 'framer-motion'
import { formatRoomName, formatSensorValue, ROOM_CONFIG } from '../App'

const ROOM_AREAS = {
  living_room: 'floor-living',
  bedroom: 'floor-bedroom',
  kitchen: 'floor-kitchen',
  bathroom: 'floor-bathroom',
  hallway: 'floor-hallway',
}

export default function FloorPlan({ rooms, selectedRoomId, onRoomClick }) {
  return (
    <motion.div
      className="floor-plan"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {rooms.map((room) => {
        const hasAlert = Number(room.smoke) > 0
        const occupied = Number(room.motion) > 0

        return (
          <button
            type="button"
            key={room.room_id}
            className={`floor-room floor-room--${room.room_id} ${ROOM_AREAS[room.room_id] ?? ''} ${
              selectedRoomId === room.room_id ? 'is-selected' : ''
            } ${hasAlert ? 'has-alert' : ''} ${occupied ? 'is-occupied' : ''}`}
            onClick={() => onRoomClick(room.room_id)}
          >
            <span>{ROOM_CONFIG[room.room_id]?.zone ?? 'Zone'}</span>
            <strong>{formatRoomName(room.room_id)}</strong>
            <small>
              {formatSensorValue('temperature', room.temperature)} / {formatSensorValue('motion', room.motion)}
            </small>
          </button>
        )
      })}
    </motion.div>
  )
}
