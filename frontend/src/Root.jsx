import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import MobileApp from './mobile/MobileApp.jsx'

// Touch device (phone/tablet) OR narrow viewport
const MOBILE_QUERY = '(pointer: coarse), (max-width: 1080px)'

function getViewMode() {
  return window.matchMedia(MOBILE_QUERY).matches ? 'mobile' : 'desktop'
}

export default function Root() {
  const [view, setView] = useState(() => getViewMode())

  useEffect(() => {
    // Listen to both conditions
    const mqPointer = window.matchMedia('(pointer: coarse)')
    const mqWidth   = window.matchMedia('(max-width: 1080px)')
    const handler = () => setView(getViewMode())
    mqPointer.addEventListener('change', handler)
    mqWidth.addEventListener('change', handler)
    return () => {
      mqPointer.removeEventListener('change', handler)
      mqWidth.removeEventListener('change', handler)
    }
  }, [])

  if (view === 'mobile') return <MobileApp />
  return <App />
}
