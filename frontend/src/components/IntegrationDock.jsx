import { BrainCircuit, ExternalLink, MessageCircle, Music2, Send } from 'lucide-react'

function actionText(action) {
  if (!action) return 'No AI actions logged yet'
  const room = String(action.room || 'room').replaceAll('_', ' ')
  const device = String(action.device || 'device').replaceAll('_', ' ')
  return `${room} ${device} -> ${action.command || 'command'}`
}

export default function IntegrationDock({ diagnostics, mode }) {
  const spotify = diagnostics?.spotify
  const ai = diagnostics?.ai
  const recentAiAction = ai?.recent_actions?.[0]
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
        <span>{mode === 'AI' ? 'Armed' : 'Paused'}</span>
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
