import { useEffect, useRef, useState, useCallback } from 'react'
import {
  getSystemOverview,
  controlActuator,
  sendUserFeedback,
  setSystemMode,
  triggerDemoScenario,
} from '../services/api'
import { mapOverviewToUiShape, uiModeToApiMode } from '../services/neuronest-adapter'

export function useNeuroNest() {
  const [uiData, setUiData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const fetchOverview = useCallback(async () => {
    try {
      const raw = await getSystemOverview()
      const shaped = mapOverviewToUiShape(raw)
      setUiData(shaped)
      setError(null)
    } catch (err) {
      setError(err.message ?? 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchOverview()
    intervalRef.current = setInterval(fetchOverview, 2000)
    return () => clearInterval(intervalRef.current)
  }, [fetchOverview])

  const toggleDevice = useCallback(async (uiRoomId, deviceKey) => {
    const ROOM_ID_REVERSE = {
      living:   'living_room',
      bedroom:  'bedroom',
      kitchen:  'kitchen',
      bathroom: 'bathroom',
      hallway:  'hallway',
      office:   'office',
    }
    const backendRoomId = ROOM_ID_REVERSE[uiRoomId] ?? uiRoomId

    const currentDevice = uiData?.devices?.[uiRoomId]?.find(d => d.deviceKey === deviceKey)
    const newState = currentDevice?.on ? 'OFF' : 'ON'
    const sensorData = uiData?.sensors?.[uiRoomId]
    const feedbackSensorData = sensorData ? {
      temperature: sensorData.temp ?? 22,
      humidity: sensorData.humidity ?? 50,
      motion: sensorData.motion ? 1 : 0,
      smoke: sensorData.smoke ? 1 : 0,
      light: sensorData.lux ?? 0,
      timestamp: new Date().toISOString(),
      room: backendRoomId,
    } : undefined

    // Optimistic update
    setUiData(prev => {
      if (!prev) return prev
      return {
        ...prev,
        devices: {
          ...prev.devices,
          [uiRoomId]: (prev.devices[uiRoomId] ?? []).map(d =>
            d.deviceKey === deviceKey ? { ...d, on: newState === 'ON', meta: newState === 'ON' ? 'On' : 'Off' } : d
          ),
        },
      }
    })

    try {
      await controlActuator(backendRoomId, deviceKey, newState)
      await sendUserFeedback(backendRoomId, deviceKey, newState, feedbackSensorData)
    } catch {
      // revert on error
      fetchOverview()
    }
  }, [uiData, fetchOverview])

  const setMode = useCallback(async (uiMode) => {
    const apiMode = uiModeToApiMode(uiMode)
    try {
      await setSystemMode(apiMode)
      setUiData(prev => prev ? { ...prev, mode: uiMode } : prev)
    } catch (err) {
      setError(err.message ?? 'Failed to set mode')
    }
  }, [])

  const runScenario = useCallback(async (scenarioId) => {
    try {
      const result = await triggerDemoScenario(scenarioId)
      await fetchOverview()
      return result
    } catch (err) {
      setError(err.message ?? 'Failed to run scenario')
      throw err
    }
  }, [fetchOverview])

  return { uiData, loading, error, fetchOverview, toggleDevice, setMode, runScenario }
}
