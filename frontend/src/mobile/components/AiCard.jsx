import React from 'react'

export default function AiCard({ decision, onWhyClick }) {
  if (!decision) return null

  return (
    <div className="m-ai-card">
      <div className="m-ai-eyebrow">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        NeuroNest decided
      </div>
      <p className="m-ai-h">{decision.action}</p>
      <p className="m-ai-reason">{decision.reason}</p>
      <div className="m-ai-actions">
        {onWhyClick && (
          <button className="m-ai-btn ghost" onClick={onWhyClick}>
            Why?
          </button>
        )}
        <button className="m-ai-btn">Got it</button>
      </div>
    </div>
  )
}
