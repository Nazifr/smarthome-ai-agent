import { motion } from 'framer-motion'
import { Power } from 'lucide-react'

export default function ActuatorToggle({
  device,
  roomId,
  state,
  onToggle,
  loading,
  label,
}) {
  const isOn = state === 'ON'
  const isLoadingOn = loading === `${roomId}-${device}-ON`
  const isLoadingOff = loading === `${roomId}-${device}-OFF`

  return (
    <div className="actuator-line">
      <div>
        <strong>{label}</strong>
        <span>{isOn ? 'Powered' : 'Standby'}</span>
      </div>
      <div className="power-switch" aria-label={`${label} control`}>
        <motion.button
          type="button"
          className={isOn ? 'is-active' : ''}
          onClick={() => onToggle(roomId, device, 'ON')}
          disabled={Boolean(loading)}
          whileTap={{ scale: 0.94 }}
        >
          <Power size={14} />
          {isLoadingOn ? 'Sending' : 'On'}
        </motion.button>
        <motion.button
          type="button"
          className={!isOn ? 'is-active is-off' : 'is-off'}
          onClick={() => onToggle(roomId, device, 'OFF')}
          disabled={Boolean(loading)}
          whileTap={{ scale: 0.94 }}
        >
          {isLoadingOff ? 'Sending' : 'Off'}
        </motion.button>
      </div>
    </div>
  )
}
