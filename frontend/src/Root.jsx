import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import MobileApp from './mobile/MobileApp.jsx'

function getViewMode() {
  // Clear any stale desktop lock that may have been saved previously
  localStorage.removeItem('viewMode')
  // viewport detection — no user-agent sniffing
  return window.matchMedia('(max-width: 820px)').matches ? 'mobile' : 'desktop'
}

export default function Root() {
  const [view, setView] = useState(() => getViewMode())

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 820px)')
    const handler = (e) => setView(e.matches ? 'mobile' : 'desktop')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  if (view === 'mobile') return <MobileApp />
  return <App />
}
