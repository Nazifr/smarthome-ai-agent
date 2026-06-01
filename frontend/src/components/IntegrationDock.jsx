import { BrainCircuit, CheckCircle2, CircleAlert, ExternalLink, MessageCircle, Music2, Send, Server, SlidersHorizontal } from 'lucide-react'

function actionText(action) {
  if (!action) return 'No AI actions logged yet'
  const room = String(action.room || 'room').replaceAll('_', ' ')
  const device = String(action.device || 'device').replaceAll('_', ' ')
  return `${room} ${device} -> ${action.command || 'command'}`
}

export default function IntegrationDock({ diagnostics, mode }) {
  const spotify = diagnostics?.spotify
  const ai = diagnostics?.ai
  const services = diagnostics?.services ?? []
  const recentAiAction = ai?.recent_actions?.[0]
  const learning = ai?.learning
  const aiArmed = ai?.armed ?? (mode === 'Auto' || mode === 'AI')
  const spotifyReady = spotify?.available
  const spotifyTitle = spotify?.track || 'Spotify ambience'
  const spotifyDetail = spotifyReady
    ? `${spotify?.artist || 'Unknown artist'}${spotify?.playing ? ' is playing' : ' is paused'}`
    : spotify?.message || 'Connect Spotify token cache to show now playing.'

  return (
    <section className="integration-dock" aria-label="External integrations">
      <div className="activity-header">
        <div>
          <span className="panel-label">Integrations</span>
          <h2>Companion Systems</h2>
        </div>
        <Send size={19} />
      </div>

      <div className="integration-card integration-card--wide">
        <div className="integration-icon integration-icon--ai">
          <BrainCircuit size={18} />
        </div>
        <div>
          <strong>AI autonomy</strong>
          <p>{ai?.message || 'Waiting for diagnostics from the backend.'}</p>
          <small>{actionText(recentAiAction)}</small>
        </div>
        <span>{aiArmed ? 'Armed' : 'Paused'}</span>
      </div>

      <div className="integration-card integration-card--wide">
        <div className="integration-icon integration-icon--learned">
          <SlidersHorizontal size={18} />
        </div>
        <div>
          <strong>Personal learning</strong>
          <p>{learning?.message || 'Manual choices become high-priority learned preferences.'}</p>
          <small>
            {learning
              ? `${learning.feedback_count} feedback events, ${learning.rule_count} learned rule(s)`
              : 'Waiting for learning status'}
          </small>
        </div>
        <span>{learning?.rule_count ? 'Learning' : 'Ready'}</span>
      </div>

      <div className="service-health">
        <div className="service-health__title">
          <Server size={15} />
          Service health
        </div>
        <div className="service-grid">
          {services.map((service) => (
            <div className={service.ok ? 'service-chip is-ok' : 'service-chip is-bad'} key={service.id || service.label}>
              {service.ok ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}
              <span>{service.label}</span>
              <small>{service.detail}</small>
            </div>
          ))}
          {services.length === 0 && (
            <div className="service-chip">
              <CircleAlert size={14} />
              <span>Diagnostics</span>
              <small>Waiting for backend status</small>
            </div>
          )}
        </div>
      </div>

      <div className="integration-card integration-card--wide">
        <div className="integration-icon integration-icon--spotify">
          <Music2 size={18} />
        </div>
        <div>
          <strong>{spotifyTitle}</strong>
          <p>{spotifyDetail}</p>
          {spotify?.album && <small>{spotify.album}</small>}
        </div>
        {spotify?.url ? (
          <a href={spotify.url} target="_blank" rel="noreferrer" className="integration-link">
            <ExternalLink size={13} />
            Open
          </a>
        ) : (
          <span>{spotifyReady ? 'Idle' : 'Setup'}</span>
        )}
      </div>

      <div className="integration-card integration-card--wide">
        <div className="integration-icon integration-icon--telegram">
          <MessageCircle size={18} />
        </div>
        <div>
          <strong>Telegram alerts</strong>
          <p>Bot channel for safety alerts and mood input.</p>
          <small>/start, /mood, /status, /stop</small>
        </div>
        <span>MQTT</span>
      </div>
    </section>
  )
}
