function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL
  const browserHost = window.location.hostname
  const isLocal = browserHost === "localhost" || browserHost === "127.0.0.1"

  // On localhost: use configured URL or fall back to :8000
  if (isLocal) {
    return configuredUrl || `${window.location.protocol}//${browserHost}:8000`
  }

  // On a remote host (ngrok, hotspot, etc.): if the configured API URL
  // also points to localhost, use a relative base so the Vite proxy
  // forwards /api/* to the backend container automatically.
  if (configuredUrl) {
    try {
      const url = new URL(configuredUrl)
      const apiIsLocal = url.hostname === "localhost" || url.hostname === "127.0.0.1"
      if (!apiIsLocal) return configuredUrl  // real remote API — use as-is
    } catch { /* fall through */ }
  }

  // Relative base → Vite proxy handles it (works for ngrok, hotspot, etc.)
  return ""
}

const API_BASE_URL = resolveApiBaseUrl()

export async function getSystemOverview() {
  const response = await fetch(`${API_BASE_URL}/api/system/overview`)

  if (!response.ok) {
    throw new Error("Failed to fetch system overview")
  }

  return response.json()
}

export async function controlActuator(roomId, device, state) {
  const response = await fetch(
    `${API_BASE_URL}/api/rooms/${roomId}/actuators/${device}?state=${state}`,
    {
      method: "POST",
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to set ${device} to ${state}`)
  }

  return response.json()
}

export async function setSystemMode(mode) {
  const response = await fetch(
    `${API_BASE_URL}/api/system/mode?mode=${mode}`,
    { method: "POST" }
  )

  if (!response.ok) {
    throw new Error("Failed to set mode")
  }

  return response.json()
}

export async function getRoomHistory(roomId, sensorType = "temperature", minutes = 60) {
  const response = await fetch(
    `${API_BASE_URL}/api/rooms/${roomId}/history?sensor_type=${sensorType}&minutes=${minutes}`
  )

  if (!response.ok) {
    throw new Error("Failed to fetch room history")
  }

  return response.json()
}

export async function getSystemDiagnostics() {
  const response = await fetch(`${API_BASE_URL}/api/system/diagnostics`)

  if (!response.ok) {
    throw new Error("Failed to fetch system diagnostics")
  }

  return response.json()
}

export async function triggerDemoScenario(scenario) {
  const response = await fetch(`${API_BASE_URL}/api/system/demo?scenario=${scenario}`, {
    method: "POST",
  })

  if (!response.ok) {
    throw new Error("Failed to trigger demo scenario")
  }

  return response.json()
}
