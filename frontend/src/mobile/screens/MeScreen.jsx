import React from 'react'

export default function MeScreen({ diag }) {
  return (
    <>
      <div className="m-greet-eyebrow">Profile</div>
      <h2 className="m-greet-h" style={{ fontSize: '26px', marginBottom: '4px' }}>
        Your home, <em>your rules</em>
      </h2>
      <p className="m-greet-sub" style={{ marginBottom: '0' }}>
        System status, integrations, and app info.
      </p>

      {/* System status */}
      <div className="m-sec-title" style={{ marginTop: '22px' }}><span>System Status</span></div>
      <div className="m-about-card">
        <div className="m-about-row">
          <span>AI Engine</span>
          <span className="m-about-val" style={{ color: diag?.ai?.armed ? 'var(--m-green)' : 'var(--m-dim)' }}>
            {diag?.ai?.armed ? 'Armed' : diag === null ? '–' : 'Standby'}
          </span>
        </div>
        {diag?.ai?.recent_actions?.length > 0 && (
          <div className="m-about-row">
            <span>Decisions this session</span>
            <span className="m-about-val">{diag.ai.recent_actions.length}</span>
          </div>
        )}
        <div className="m-about-row">
          <span>Demo scenario</span>
          <span className="m-about-val">{diag?.demo?.active ?? (diag === null ? '–' : 'live')}</span>
        </div>
      </div>

      {/* Integrations */}
      <div className="m-sec-title" style={{ marginTop: '22px' }}><span>Integrations</span></div>
      <div className="m-about-card">
        {/* Spotify */}
        <div className="m-about-row">
          <span>Spotify</span>
          <span className="m-about-val">
            {diag?.spotify?.playing
              ? <span style={{ color: 'var(--m-green)', fontSize: '11.5px' }}>
                  {diag.spotify.track ?? 'Playing'}
                </span>
              : diag === null ? '–' : 'Not playing'}
          </span>
        </div>
        {/* Telegram */}
        {(() => {
          const tg = diag?.services?.find(
            s => s.label?.toLowerCase().includes('telegram') || s.id === 'telegram'
          )
          return (
            <div className="m-about-row">
              <span>Telegram</span>
              <span className="m-about-val" style={{
                color: diag === null ? 'var(--m-dim)'
                  : tg?.ok ? 'var(--m-green)' : 'var(--m-alert)',
              }}>
                {diag === null ? '–' : tg ? (tg.ok ? 'Connected' : 'Offline') : 'Inactive'}
              </span>
            </div>
          )
        })()}
        {/* MQTT */}
        {(() => {
          const mqtt = diag?.services?.find(s => s.label?.toLowerCase().includes('mqtt'))
          return (
            <div className="m-about-row">
              <span>MQTT Broker</span>
              <span className="m-about-val" style={{
                color: diag === null ? 'var(--m-dim)'
                  : mqtt?.ok ? 'var(--m-green)' : 'var(--m-alert)',
              }}>
                {diag === null ? '–' : mqtt ? (mqtt.ok ? 'Connected' : 'Offline') : '–'}
              </span>
            </div>
          )
        })()}
        {/* InfluxDB */}
        {(() => {
          const influx = diag?.services?.find(
            s => s.label?.toLowerCase().includes('influx') || s.id === 'influx'
          )
          return influx ? (
            <div className="m-about-row">
              <span>InfluxDB</span>
              <span className="m-about-val" style={{ color: influx.ok ? 'var(--m-green)' : 'var(--m-alert)' }}>
                {influx.ok ? 'Connected' : 'Offline'}
              </span>
            </div>
          ) : null
        })()}
      </div>

      {/* Quick link to desktop */}
      <div className="m-sec-title" style={{ marginTop: '22px' }}><span>Navigation</span></div>
      <a
        href="/"
        className="m-desktop-link"
        style={{ display: 'flex', textDecoration: 'none' }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
        Open Desktop Dashboard
      </a>

      {/* About */}
      <div className="m-sec-title" style={{ marginTop: '22px' }}><span>About</span></div>
      <div className="m-about-card">
        <div className="m-about-row">
          <span>App</span>
          <span className="m-about-val">NeuroNest Companion</span>
        </div>
        <div className="m-about-row">
          <span>Version</span>
          <span className="m-about-val">Mobile v2.0</span>
        </div>
        <div className="m-about-row">
          <span>Backend</span>
          <span className="m-about-val">FastAPI · LightGBM</span>
        </div>
        <div className="m-about-row">
          <span>University</span>
          <span className="m-about-val">DEÜ · 2026</span>
        </div>
      </div>
    </>
  )
}
