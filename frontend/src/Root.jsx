import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import MobileApp from './mobile/MobileApp.jsx'

function getViewMode() {
  // ?desktop=1  → force desktop (and save)
  const params = new URLSearchParams(window.location.search)
  if (params.get('desktop') === '1') {
    localStorage.setItem('viewMode', 'desktop')
    return 'desktop'
  }
  // ?mobile=1  → force mobile (useful for testing on desktop)
  if (params.get('mobile') === '1') {
    localStorage.setItem('viewMode', 'mobile')
    return 'mobile'
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
