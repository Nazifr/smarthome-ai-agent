import React, { useEffect, useState } from 'react'
import { getSystemDiagnostics } from '../../services/api.js'

const MODES = [
  { id: 'AI',     label: 'Auto',   desc: 'NeuroNest decides' },
  { id: 'Manual', label: 'Manual', desc: 'Full manual control' },
  { id: 'Static', label: 'Away',   desc: 'Low-power standby' },
]

export default function MeScreen({ mode, onSetMode, onSwitchToDesktop }) {
  const [diag, setDiag] = useState(null)

  useEffect(() => {
    getSystemDiagnostics().then(setDiag).catch(() => {})
  }, [mode])

  return (
    <>
      <div className="m-greet-eyebrow">Settings</div>
      <h2 className="m-greet-h" style={{ fontSize: '26px', marginBottom: '4px' }}>
        Your home, <em>your rules</em>
      </h2>
      <p className="m-greet-sub" style={{ marginBottom: '0' }}>
        Configure how NeuroNest manages your space.
      </p>

      {/* Mode picker */}
      <div className="m-sec-title"><span>System Mode</span></div>
      <div className="m-mode-grid">
        {MODES.map(m => (
          <button
            key={m.id}
            className={`m-mode-btn${mode === m.id ? ' is-active' : ''}`}
            onClick={() => onSetMode(m.id)}
            title={m.desc}
          >
            <span style={{ fontSize: '18px', lineHeight: 1 }}>
              {m.id === 'AI' ? '✦' : m.id === 'Manual' ? '⊙' : '⌂'}
            </span>
            <span>{m.label}</span>
          </button>
        ))}
      </div>
      <p style={{ fontSize: '12px', color: 'var(--m-dim)', marginTop: '8px', lineHeight: 1.4 }}>
        {mode === 'AI' ? 'NeuroNest is making automated decisions.'
          : mode === 'Manual' ? 'You are in full control of all devices.'
          : 'Away mode — minimum energy use.'}
      </p>

      {/* System status */}
      <div className="m-sec-title" style={{ marginTop: '28px' }}><span>System Status</span></div>
      <div className="m-about-card">
        <div className="m-about-row">
          <span>AI Engine</span>
          <span className="m-about-val">{diag?.ai?.armed ? '🟢 Armed' : '⚪ Standby'}</span>
        </div>
        {diag?.ai?.recent_actions?.length > 0 && (
          <div className="m-about-row">
            <span>Recent actions</span>
            <span className="m-about-val">{diag.ai.recent_actions.length}</span>
          </div>
        )}
        <div className="m-about-row">
          <span>Demo scenario</span>
          <span className="m-about-val">{diag?.demo?.active ?? 'live'}</span>
        </div>
        {diag?.spotify?.playing && (
          <div className="m-about-row">
            <span>Now playing</span>
            <span className="m-about-val" style={{ fontSize: '11.5px', maxWidth: '160px', textAlign: 'right' }}>
              🎵 {diag.spotify.track}
            </span>
          </div>
        )}
      </div>

      {/* About */}
      <div className="m-sec-title" style={{ marginTop: '20px' }}><span>About</span></div>
      <div className="m-about-card">
        <div className="m-about-row">
          <span>App</span>
          <span className="m-about-val">NeuroNest Companion</span>
        </div>
        <div className="m-about-row">
          <span>Version</span>
          <span className="m-about-val">Mobile v1.0</span>
        </div>
        <div className="m-about-row">
          <span>Backend</span>
          <span className="m-about-val">FastAPI</span>
        </div>
      </div>

      {/* Switch to desktop */}
      <div style={{ marginTop: '24px' }}>
        <button className="m-desktop-link" onClick={onSwitchToDesktop}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          View on desktop instead
        </button>
      </div>
    </>
  )
}
