import React from 'react'
import { adaptEnergy } from '../adapters.js'

export default function EnergyScreen({ overview }) {
  const data = adaptEnergy(overview)
  if (!data) return <div className="m-loading">Loading…</div>

  const maxBar = Math.max(...data.syntheticBars)

  return (
    <>
      {/* Hero */}
      <div className="m-energy-hero">
        <div className="m-energy-eyebrow">Today's Estimate</div>
        <div className="m-energy-big">
          {data.estimatedKwh}
          <span className="m-energy-unit">kWh</span>
        </div>
        {data.estimatedSavings > 0 && (
          <div className="m-energy-saving">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
            {data.estimatedSavings} kWh saved est.
          </div>
        )}

        {/* 7-day bar chart */}
        <div className="m-energy-chart">
          {data.syntheticBars.map((frac, i) => {
            const isToday = i === data.syntheticBars.length - 1
            const heightPct = Math.round((frac / maxBar) * 100)
            return (
              <div
                key={i}
                className={`m-energy-bar${isToday ? ' is-today' : ''}`}
                style={{ height: `${heightPct}%` }}
              />
            )
          })}
        </div>
        <div className="m-energy-axis">
          {data.dayLabels.map((label, i) => (
            <span key={i}>{label}</span>
          ))}
        </div>
      </div>

      {/* Breakdown */}
      <div className="m-sec-title"><span>Breakdown</span></div>
      <div className="m-savings-card">
        <div className="m-savings-row">
          <span className="m-savings-nm">Devices on</span>
          <span className="m-savings-v">{data.totalDevicesOn} active</span>
        </div>
        <div className="m-savings-row">
          <span className="m-savings-nm">Estimated today</span>
          <span className="m-savings-v">{data.estimatedKwh} kWh</span>
        </div>
        <div className="m-savings-row">
          <span className="m-savings-nm">Weekly pace</span>
          <span className="m-savings-v">{(data.estimatedKwh * 7).toFixed(1)} kWh</span>
        </div>
        {data.estimatedSavings > 0 && (
          <div className="m-savings-row">
            <span className="m-savings-nm">Savings (est.)</span>
            <span className="m-savings-v">−{data.estimatedSavings} kWh</span>
          </div>
        )}
      </div>

      <div className="m-energy-note">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        Values estimated from device count. Real metering not yet available.
      </div>
    </>
  )
}
