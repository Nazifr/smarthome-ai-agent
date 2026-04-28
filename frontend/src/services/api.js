const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

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