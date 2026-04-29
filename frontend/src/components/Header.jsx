import { motion } from 'framer-motion'
import { BrainCircuit, RadioTower, ShieldCheck } from 'lucide-react'

export default function Header({ overview, alerts, health }) {
  const mode = overview?.mode ?? 'Manual'
  const alertCount = alerts?.length ?? 0

  return (
    <motion.header
      className="hero-command"
      initial={{ opacity: 0, y: -18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="hero-copy">
        <div className="brand-lockup" aria-label="Project identity">
          <div className="project-logo">
            <span>AI</span>
          </div>
          <div>
            <strong>NeuroNest</strong>
            <small>Adaptive Smart Home</small>
          </div>
        </div>
        <div className="eyebrow">
          <RadioTower size={16} />
          Live IoT Control Surface
        </div>
        <h1>Smart Home Mission Control</h1>
        <p>
          Adaptive AI-based monitoring for rooms, sensors, safety events, and
          actuators in one exhibition-ready cockpit.
        </p>
      </div>

      <div className="hero-instrument" aria-label="System status summary">
        <div className="instrument-ring">
          <span>{health}</span>
          <small>Health</small>
        </div>
        <div className="instrument-stack">
          <div className="instrument-row">
            <BrainCircuit size={18} />
            <span>{mode}</span>
            <small>Mode</small>
          </div>
          <div className="instrument-row">
            <ShieldCheck size={18} />
            <span>{alertCount === 0 ? 'Clear' : `${alertCount} alert`}</span>
            <small>Safety</small>
          </div>
        </div>
      </div>
    </motion.header>
  )
}
