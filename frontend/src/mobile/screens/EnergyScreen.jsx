import React, { useEffect, useState } from 'react'
import { getEnergySummary } from '../../services/api.js'
import { adaptEnergy } from '../adapters.js'

export default function EnergyScreen({ overview }) {
  const [energy, setEnergy]         = useState(null)
  const [selectedIdx, setSelectedIdx] = useState(null) // null = show today
  const fallback = adaptEnergy(overview)

  useEffect(() => {
    let cancelled = false
    const load = () =>
      getEnergySummary()
        .then(data => { if (!cancelled) setEnergy(data) })
        .catch(() => {})
    load()
    const interval = setInterval(load, 15000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  const hasReal     = energy && energy.daily && energy.daily.some(d => d.kwh > 0)
  const todayKwh    = hasReal ? energy.today_kwh   : (fallback?.estimatedKwh ?? 0)
  const deltaPct    = hasReal ? energy.delta_pct   : null
  const dailyBars   = hasReal
    ? energy.daily.map(d => d.kwh)
    : (fallback?.syntheticBars ?? [])
  const dayLabels   = hasReal
    ? energy.daily.map(d => d.day)
    : (fallback?.dayLabels ?? [])
  const breakdown   = (hasReal
    ? (energy.daily[displayIdx]?.breakdown ?? energy?.breakdown)
    : energy?.breakdown) ?? []
  const totalDevicesOn = fallback?.totalDevicesOn ?? 0

  const maxBar = Math.max(...dailyBars, 0.01)

  // What the chart header shows (today or selected day)
  const displayIdx  = selectedIdx ?? (dailyBars.length - 1)
  const displayKwh  = hasReal
    ? (energy.daily[displayIdx]?.kwh ?? todayKwh)
    : (displayIdx === dailyBars.length - 1 ? todayKwh : null)
  const displayDay  = dayLabels[displayIdx] ?? 'Today'
  const isToday     = displayIdx === dailyBars.length - 1

  return (
    <>
      {/* Hero */}
      <div className="m-energy-hero">
        <div className="m-energy-eyebrow">
          {isToday
            ? (hasReal ? "Today's Usage" : "Today's Estimate")
            : `${displayDay}'s Usage`}
        </div>
        <div className="m-energy-big">
          {displayKwh != null ? displayKwh : '—'}
          <span className="m-energy-unit">kWh</span>
        </div>

        {/* Delta only for today */}
        {isToday && deltaPct != null && deltaPct !== 0 && (
          <div className="m-energy-saving">
            {deltaPct < 0 ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
                <polyline points="17 18 23 18 23 12"/>
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                <polyline points="17 6 23 6 23 12"/>
              </svg>
            )}
            {deltaPct > 0 ? '+' : ''}{deltaPct}% vs 7-day avg
          </div>
        )}

        {/* 7-day bar chart — bars are clickable */}
        <div className="m-energy-chart">
          {dailyBars.map((val, i) => {
            const isTodayBar  = i === dailyBars.length - 1
            const isSelected  = i === displayIdx
            const heightPct   = Math.round((val / maxBar) * 100)
            return (
              <button
                key={i}
                className={[
                  'm-energy-bar',
                  isTodayBar  ? 'is-today'    : '',
                  isSelected  ? 'is-selected' : '',
                ].filter(Boolean).join(' ')}
                style={{ height: `${Math.max(heightPct, 3)}%` }}
                onClick={() => setSelectedIdx(i === displayIdx && !isToday ? null : i)}
                aria-label={`${dayLabels[i]}: ${hasReal ? (energy.daily[i]?.kwh ?? 0) + ' kWh' : 'relative usage'}`}
              />
            )
          })}
        </div>
        <div className="m-energy-axis">
          {dayLabels.map((label, i) => (
            <span
              key={i}
              style={{ color: i === displayIdx ? 'var(--m-accent)' : undefined, fontWeight: i === displayIdx ? 600 : undefined }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Device breakdown */}
      {breakdown.length > 0 && (
        <>
          <div className="m-sec-title"><span>Top Consumers{!isToday ? ` — ${displayDay}` : ''}</span></div>
          <div className="m-savings-card">
            {breakdown.slice(0, 6).map((item, i) => (
              <div className="m-savings-row" key={i}>
                <span className="m-savings-nm">
                  {item.device.replace(/_/g, ' ')}
                  <span style={{ color: 'var(--m-dim)', fontSize: '10px', marginLeft: '6px' }}>
                    {item.room.replace(/_/g, ' ')}
                  </span>
                </span>
                <span className="m-savings-v">
                  {item.kwh > 0.01 ? `${item.kwh} kWh` : `${item.on_hours}h on`}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Summary stats */}
      <div className="m-sec-title"><span>Summary</span></div>
      <div className="m-savings-card">
        <div className="m-savings-row">
          <span className="m-savings-nm">Devices on now</span>
          <span className="m-savings-v">{totalDevicesOn} active</span>
        </div>
        <div className="m-savings-row">
          <span className="m-savings-nm">Today so far</span>
          <span className="m-savings-v">{todayKwh} kWh</span>
        </div>
        {hasReal && energy.avg_7d_kwh > 0 && (
          <div className="m-savings-row">
            <span className="m-savings-nm">7-day average</span>
            <span className="m-savings-v">{energy.avg_7d_kwh} kWh</span>
          </div>
        )}
      </div>

      <div className="m-energy-note">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {hasReal
          ? "kWh accumulates throughout the day as devices run — it won't jump when you toggle a device, it grows as devices stay on."
          : 'No tracking data yet — values estimated from device count. Toggle some devices to start collecting real data.'}
      </div>
    </>
  )
}
