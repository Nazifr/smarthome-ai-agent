import { ROOMS } from '../config/floorplan'

const doors = [
  { x: 360, y: 130, w: 0, h: 24 },
  { x: 200, y: 260, w: 24, h: 0 },
  { x: 360, y: 300, w: 0, h: 20 },
  { x: 490, y: 300, w: 0, h: 20 },
  { x: 560, y: 130, w: 0, h: 24 },
]

export default function FloorPlanV2({ sensors, devices = {}, selectedRoom, onSelectRoom, alerts, showFurniture = true }) {
  const roomList = Object.values(ROOMS)

  return (
    <svg className="plan-svg" viewBox="0 0 800 420" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="nn-roomGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="rgba(255,255,255,0.04)"/>
          <stop offset="1" stopColor="rgba(0,0,0,0.04)"/>
        </linearGradient>
      </defs>

      <rect x="32" y="32" width="736" height="356" rx="14" ry="14"
        fill="none" stroke="var(--line-2)" strokeWidth="1.5" strokeDasharray="2 4" opacity="0.6"/>

      {roomList.map((r) => {
        const s = sensors[r.id] || {}
        const occupied = Boolean(s.motion)
        const alert = alerts[r.id]
        const selected = selectedRoom === r.id
        const roomDevices = devices[r.id] ?? []
        const lightsOn = roomDevices.some(d => d.on && (d.icon === 'Lightbulb' || d.icon === 'Sun'))
        const fanOn    = roomDevices.some(d => d.on && d.icon === 'Fan')
        const cls = [
          'room-shape',
          occupied ? 'is-occupied' : '',
          alert ? 'is-alert' : '',
          selected ? 'is-selected' : '',
          lightsOn ? 'is-lit' : '',
        ].filter(Boolean).join(' ')

        return (
          <g key={r.id} className={lightsOn ? 'room-group is-lit' : 'room-group'} onClick={() => onSelectRoom(r.id)}>
            <rect className={cls} x={r.x} y={r.y} width={r.w} height={r.h} rx="6" ry="6"/>
            {/* warm glow overlay when light is on */}
            {lightsOn && !alert && (
              <rect x={r.x + 2} y={r.y + 2} width={r.w - 4} height={r.h - 4} rx="5" ry="5"
                fill="rgba(255, 200, 100, 0.10)" pointerEvents="none"/>
            )}

            {showFurniture && r.furniture.map((f, i) =>
              f.type === 'rect' ? (
                <rect key={i} className="furniture" x={f.x} y={f.y} width={f.w} height={f.h} rx={f.r || 0}/>
              ) : (
                <circle key={i} className="furniture" cx={f.cx} cy={f.cy} r={f.r}/>
              )
            )}

            {occupied && !alert && (
              <>
                <circle className="motion-pulse" cx={r.motion.x} cy={r.motion.y} r="5"/>
                <circle cx={r.motion.x} cy={r.motion.y} r="3" fill="var(--accent)"/>
              </>
            )}
            {alert && (
              <>
                <circle className="motion-pulse" cx={r.motion.x} cy={r.motion.y} r="5" style={{ fill: 'var(--alert)' }}/>
                <circle cx={r.motion.x} cy={r.motion.y} r="3" fill="var(--alert)"/>
              </>
            )}

            {/* fan indicator badge */}
            {fanOn && !alert && (
              <g transform={`translate(${r.x + r.w - 14}, ${r.y + r.h - 14})`} opacity="0.8" pointerEvents="none">
                <circle r="8" fill="var(--accent-soft)" stroke="var(--accent-line)" strokeWidth="1"/>
                <line x1="-4" y1="0" x2="4" y2="0" stroke="var(--accent)" strokeWidth="1.4" strokeLinecap="round"/>
                <line x1="0" y1="-4" x2="0" y2="4" stroke="var(--accent)" strokeWidth="1.4" strokeLinecap="round"/>
                <line x1="-3" y1="-3" x2="3" y2="3" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"/>
                <line x1="3" y1="-3" x2="-3" y2="3" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"/>
              </g>
            )}
            <text className="room-label-name" x={r.label.x} y={r.label.y}>{r.name}</text>
            <text className="room-label-temp" x={r.label.x} y={r.label.y + 16}>
              {s.temp != null ? s.temp.toFixed(1) : '—'}°  ·  {s.humidity ?? '—'}% rh
            </text>

            {alert ? (
              <g transform={`translate(${r.icon.x}, ${r.icon.y})`}>
                <circle r="9" fill="var(--alert-soft)" stroke="var(--alert)" strokeWidth="1"/>
                <text x="0" y="3.5" textAnchor="middle" fontSize="10" fontWeight="700" fill="var(--alert)" fontFamily="JetBrains Mono">!</text>
              </g>
            ) : occupied ? (
              <g transform={`translate(${r.icon.x}, ${r.icon.y})`}>
                <circle r="9" fill="var(--accent-soft)" stroke="var(--accent-line)" strokeWidth="1"/>
                <circle r="3" fill="var(--accent)"/>
              </g>
            ) : null}
          </g>
        )
      })}

      {doors.map((d, i) => (
        <line key={i} x1={d.x} y1={d.y} x2={d.x + d.w} y2={d.y + d.h}
          stroke="var(--bg-2)" strokeWidth="6" strokeLinecap="round"/>
      ))}

      <g transform="translate(740, 60)" opacity="0.5">
        <circle r="14" fill="none" stroke="var(--line-2)" strokeWidth="1"/>
        <line x1="0" y1="-10" x2="0" y2="10" stroke="var(--muted)" strokeWidth="0.8"/>
        <line x1="-10" y1="0" x2="10" y2="0" stroke="var(--muted)" strokeWidth="0.8"/>
        <text x="0" y="-15" textAnchor="middle" fontSize="9" fill="var(--muted)" fontFamily="JetBrains Mono">N</text>
      </g>

      <g transform="translate(60, 400)" opacity="0.5">
        <line x1="0" y1="0" x2="80" y2="0" stroke="var(--muted)" strokeWidth="1"/>
        <line x1="0" y1="-3" x2="0" y2="3" stroke="var(--muted)" strokeWidth="1"/>
        <line x1="40" y1="-2" x2="40" y2="2" stroke="var(--muted)" strokeWidth="1"/>
        <line x1="80" y1="-3" x2="80" y2="3" stroke="var(--muted)" strokeWidth="1"/>
        <text x="0" y="14" fontSize="9" fill="var(--muted)" fontFamily="JetBrains Mono">0</text>
        <text x="80" y="14" fontSize="9" fill="var(--muted)" fontFamily="JetBrains Mono">4m</text>
      </g>
    </svg>
  )
}
