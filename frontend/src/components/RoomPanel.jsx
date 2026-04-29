import { motion } from 'framer-motion'
import { X } from 'lucide-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  formatDeviceName,
  formatRoomName,
  formatSensorValue,
  ROOM_CONFIG,
  SENSOR_LABELS,
} from '../App'
import ActuatorToggle from './ActuatorToggle'

export default function RoomPanel({
  room,
  history,
  historyLoading,
  historyMinutes,
  actionLoading,
  localStates,
  onHistoryMinutesChange,
  onClose,
  onActuator,
}) {
  const config = ROOM_CONFIG[room.room_id] ?? {
    sensors: ['temperature', 'humidity', 'motion', 'smoke'],
    controls: Object.keys(room.actuators ?? {}).map((key) => ({ key, label: formatDeviceName(key) })),
  }

  return (
    <motion.div
      className="panel-backdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.section
        className="room-panel"
        initial={{ opacity: 0, x: 42, scale: 0.98 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 42, scale: 0.98 }}
        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
        onClick={(event) => event.stopPropagation()}
        aria-label={`${formatRoomName(room.room_id)} details`}
      >
        <header className="room-panel-header">
          <div>
            <span className="panel-label">Room Detail</span>
            <h2>{formatRoomName(room.room_id)}</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close panel">
            <X size={20} />
          </button>
        </header>

        <div className="panel-grid">
          <section className="sensor-board">
            <span className="panel-label">Sensor Stack</span>
            {config.sensors.map((sensor) => (
              <div className="sensor-readout" key={sensor}>
                <span>{SENSOR_LABELS[sensor] ?? formatDeviceName(sensor)}</span>
                <strong>{formatSensorValue(sensor, room[sensor])}</strong>
              </div>
            ))}
          </section>

          <section className="actuator-board">
            <span className="panel-label">Actuator Control</span>
            <div className="actuator-list">
              {config.controls.map((control) => {
                const currentState =
                  localStates[`${room.room_id}-${control.key}`] ??
                  room.actuators?.[control.key] ??
                  'UNKNOWN'

                return (
                  <ActuatorToggle
                    key={control.key}
                    roomId={room.room_id}
                    device={control.key}
                    label={control.label}
                    state={currentState}
                    loading={actionLoading}
                    onToggle={onActuator}
                  />
                )
              })}
            </div>
          </section>
        </div>

        <section className="history-panel">
          <div className="chart-heading">
            <div>
              <span className="panel-label">Temperature Trace</span>
              <h3>Recent Thermal Behavior</h3>
            </div>
            <select
              value={historyMinutes}
              onChange={(event) => onHistoryMinutesChange(Number(event.target.value))}
            >
              <option value={15}>15 min</option>
              <option value={60}>60 min</option>
              <option value={180}>180 min</option>
            </select>
          </div>

          <div className="chart-frame">
            {historyLoading ? (
              <p>Loading history...</p>
            ) : history.length === 0 ? (
              <p>No history data available.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis dataKey="time" tick={{ fill: '#9da6a3', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#9da6a3', fontSize: 12 }} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#111613',
                      border: '1px solid rgba(109, 255, 194, 0.25)',
                      borderRadius: 8,
                      color: '#f3f8f5',
                    }}
                    labelStyle={{ color: '#f3f8f5' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#6dffc2"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 5, fill: '#ffcf5a', stroke: '#101411' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>
      </motion.section>
    </motion.div>
  )
}
