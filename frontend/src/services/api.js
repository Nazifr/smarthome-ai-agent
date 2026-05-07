function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL
  const browserHost = window.location.hostname

  if (!configuredUrl) {
    return `${window.location.protocol}//${browserHost}:8000`
  }

  try {
    const url = new URL(configuredUrl)
    const pointsToLocalhost = url.hostname === "localhost" || url.hostname === "127.0.0.1"
    const browserIsRemote = browserHost !== "localhost" && browserHost !== "127.0.0.1"

    if (pointsToLocalhost && browserIsRemote) {
      url.hostname = browserHost
      return url.toString().replace(/\/$/, "")
    }

    return configuredUrl
  } catch {
    return configuredUrl
  }
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
