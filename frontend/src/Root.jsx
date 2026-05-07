import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import MobileApp from './mobile/MobileApp.jsx'

function getViewMode() {
  const params = new URLSearchParams(window.location.search)

  // ?desktop=1  → force desktop (and save)
  if (params.get('desktop') === '1') {
    localStorage.setItem('viewMode', 'desktop')
    return 'desktop'
  }
  // ?mobile=1  → force mobile and CLEAR any desktop lock
  if (params.get('mobile') === '1') {
    localStorage.removeItem('viewMode')
    return 'mobile'
  }
  // ?reset=1  → clear override and fall through to viewport detection
  if (params.get('reset') === '1') {
    localStorage.removeItem('viewMode')
  }

  // localStorage override
  const saved = localStorage.getItem('viewMode')
  if (saved === 'desktop') return 'desktop'
  if (saved === 'mobile')  return 'mobile'
  // viewport detection — no user-agent sniffing
  return window.matchMedia('(max-width: 820px)').matches ? 'mobile' : 'desktop'
}

export default function Root() {
  const [view, setView] = useState(() => getViewMode())

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 820px)')
    const handler = (e) => {
      // only auto-switch if user hasn't manually overridden
      const saved = localStorage.getItem('viewMode')
      if (!saved) {
        setView(e.matches ? 'mobile' : 'desktop')
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  if (view === 'mobile') return <MobileApp />
  return <App />
}
