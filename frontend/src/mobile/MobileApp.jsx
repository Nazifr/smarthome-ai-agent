import React, { useEffect, useRef, useState, useCallback } from 'react'
import './styles/mobile-tokens.css'
import './styles/mobile.css'

import TabBar        from './components/TabBar.jsx'
import RoomSheet     from './components/RoomSheet.jsx'
import HomeScreen    from './screens/HomeScreen.jsx'
import ActivityScreen from './screens/ActivityScreen.jsx'
import AiScreen      from './screens/AiScreen.jsx'
import EnergyScreen  from './screens/EnergyScreen.jsx'
import MeScreen      from './screens/MeScreen.jsx'

import {
  getSystemOverview,
  getSystemDiagnostics,
  controlActuator,
  setSystemMode,
  triggerDemoScenario,
  getWeather,
} from '../services/api.js'

export default function MobileApp() {
  const [tab, setTab]               = useState('home')
  const [sheetRoomId, setSheetRoomId] = useState(null)
  const [overview, setOverview]     = useState(null)
  const [diag, setDiag]             = useState(null)
  const [loading, setLoading]       = useState(true)
  const [toast, setToast]           = useState(null)
  const [activeScene, setActiveScene] = useState(null)
  const [weather, setWeather]       = useState(null)
  const intervalRef  = useRef(null)
  const diagInterval = useRef(null)
  const toastTimer   = useRef(null)

  // ── data fetching ──────────────────────────────────────────────
  const fetchOverview = useCallback(async () => {
    try {
      const data = await getSystemOverview()
      setOverview(data)
    } catch {
      // keep stale data on transient errors
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchDiag = useCallback(async () => {
    try {
      const data = await getSystemDiagnostics()
      setDiag(data)
    } catch {
      // keep stale
    }
  }, [])

  useEffect(() => {
    fetchOverview()
    fetchDiag()
    getWeather().then(setWeather).catch(() => {})

    intervalRef.current  = setInterval(fetchOverview, 3000)
    diagInterval.current = setInterval(fetchDiag, 5000)

    const weatherInterval = setInterval(() => {
      getWeather().then(setWeather).catch(() => {})
    }, 600000)

    return () => {
      clearInterval(intervalRef.current)
      clearInterval(diagInterval.current)
      clearInterval(weatherInterval)
    }
  }, [fetchOverview, fetchDiag])

  // ── toast helper ───────────────────────────────────────────────
  const showToast = useCallback((msg) => {
    setToast(msg)
    clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 2200)
  }, [])

  // ── device toggle ──────────────────────────────────────────────
  const handleToggleDevice = useCallback(async (backendRoomId, deviceKey) => {
    if (!overview) return
    const room = (overview.rooms ?? []).find(r => r.room_id === backendRoomId)
    if (!room) return
    const currentState = room.actuators?.[deviceKey]
    const newState = currentState !== 'OFF' ? 'OFF' : 'ON'

    setOverview(prev => {
      if (!prev) return prev
      return {
        ...prev,
        rooms: prev.rooms.map(r =>
          r.room_id === backendRoomId
            ? { ...r, actuators: { ...r.actuators, [deviceKey]: newState } }
            : r
        ),
      }
    })

    try {
      await controlActuator(backendRoomId, deviceKey, newState)
    } catch {
      fetchOverview()
      showToast('Could not update device')
    }
  }, [overview, fetchOverview, showToast])

  // ── mode change ────────────────────────────────────────────────
  const handleSetMode = useCallback(async (apiMode) => {
    try {
      await setSystemMode(apiMode)
      setOverview(prev => prev ? { ...prev, mode: apiMode } : prev)
      const labels = { AI: 'Auto', Manual: 'Manual', Static: 'Away' }
      showToast(`Mode: ${labels[apiMode] ?? apiMode}`)
      if (apiMode === 'Static' && overview) {
        const offs = []
        for (const room of overview.rooms ?? []) {
          for (const [key, state] of Object.entries(room.actuators ?? {})) {
            if (state !== 'OFF') offs.push(controlActuator(room.room_id, key, 'OFF').catch(() => {}))
          }
        }
        await Promise.allSettled(offs)
        fetchOverview()
      }
    } catch {
      showToast('Could not change mode')
    }
  }, [showToast, overview, fetchOverview])

  // ── scene ──────────────────────────────────────────────────────
  const handleSceneClick = useCallback(async (scenarioId) => {
    setActiveScene(scenarioId)
    try {
      await triggerDemoScenario(scenarioId)
      await fetchOverview()
      await fetchDiag()
      showToast('Scene activated')
    } catch {
      setActiveScene(null)
      showToast('Could not activate scene')
    }
  }, [fetchOverview, fetchDiag, showToast])

  // ── room sheet ─────────────────────────────────────────────────
  const handleRoomClick = useCallback((id) => {
    setSheetRoomId(id)
  }, [])

  const handleSheetClose = useCallback(() => {
    setSheetRoomId(null)
  }, [])

  // ── tab change ─────────────────────────────────────────────────
  const handleTabChange = useCallback((newTab) => {
    setTab(newTab)
  }, [])

  // ── loading splash ─────────────────────────────────────────────
  if (loading) {
    return (
      <div className="m-root">
        <div className="m-loading-splash">
          <div className="m-loading-brand">NeuroNest</div>
          <div className="m-loading-sub">connecting…</div>
        </div>
      </div>
    )
  }

  const currentMode = overview?.mode ?? 'AI'

  // ── render ─────────────────────────────────────────────────────
  return (
    <div className="m-root">
      {/* Cosmetic status bar */}
      <div className="m-statusbar">
        <span className="m-statusbar-time">
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <div className="m-status-icons">
          <svg width="16" height="11" viewBox="0 0 16 11" fill="currentColor">
            <rect x="0"    y="7"  width="3"   height="4"  rx="0.4" opacity="0.4"/>
            <rect x="4.5"  y="5"  width="3"   height="6"  rx="0.4" opacity="0.6"/>
            <rect x="9"    y="3"  width="3"   height="8"  rx="0.4" opacity="0.8"/>
            <rect x="13.5" y="0"  width="2.5" height="11" rx="0.4"/>
          </svg>
          <svg width="22" height="11" viewBox="0 0 22 11" fill="none">
            <rect x="0.5" y="0.5" width="18" height="10" rx="2" stroke="currentColor" opacity="0.5"/>
            <rect x="20"  y="3"   width="1.5" height="5" rx="0.5" fill="currentColor" opacity="0.5"/>
            <rect x="2"   y="2"   width="14"  height="7" rx="1" fill="currentColor"/>
          </svg>
        </div>
      </div>

      {/* Screen content */}
      <div className="m-shell">
        <div className="m-screen">
          {tab === 'home' && (
            <HomeScreen
              overview={overview}
              weather={weather}
              onRoomClick={handleRoomClick}
              onSceneClick={handleSceneClick}
              activeScene={activeScene}
            />
          )}
          {tab === 'activity' && (
            <ActivityScreen
              diag={diag}
              overview={overview}
            />
          )}
          {tab === 'ai' && (
            <AiScreen
              diag={diag}
              mode={currentMode}
              onSetMode={handleSetMode}
            />
          )}
          {tab === 'energy' && (
            <EnergyScreen overview={overview} />
          )}
          {tab === 'me' && (
            <MeScreen diag={diag} />
          )}
        </div>

        <TabBar activeTab={tab} onTabChange={handleTabChange} />
      </div>

      {/* Room sheet — rendered outside m-shell to overlay tab bar */}
      <RoomSheet
        overview={overview}
        roomId={sheetRoomId}
        onClose={handleSheetClose}
        onToggleDevice={handleToggleDevice}
      />

      {/* Toast */}
      <div className={`m-toast${toast ? ' show' : ''}`} aria-live="polite">
        {toast || ''}
      </div>
    </div>
  )
}
