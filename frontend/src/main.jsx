import React from 'react'
import ReactDOM from 'react-dom/client'
import Root from './Root.jsx'
import './index.css'
import './App.css'
import './styles/tokens.css'
import './styles/dashboard.css'

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    registrations.forEach((registration) => registration.unregister())
  })
}

if ('caches' in window) {
  caches.keys().then((keys) => {
    keys.forEach((key) => caches.delete(key))
  })
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
)
