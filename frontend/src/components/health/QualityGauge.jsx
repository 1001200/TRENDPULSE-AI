import React, { useEffect, useState } from 'react'

/**
 * QualityGauge — Circular SVG gauge showing data quality score (0-100%).
 * 
 * Props:
 *   score: number (0-100)
 *   size: number (px, default 140)
 */
export default function QualityGauge({ score = 0, size = 140 }) {
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    // Animate from 0 to score
    const timer = setTimeout(() => setAnimatedScore(score), 100)
    return () => clearTimeout(timer)
  }, [score])

  const strokeWidth = 8
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedScore / 100) * circumference

  // Color based on score
  let color = '#f43f5e' // Rose for poor
  if (animatedScore >= 80) color = '#10b981' // Emerald for good
  else if (animatedScore >= 60) color = '#f59e0b' // Amber for ok
  else if (animatedScore >= 40) color = '#f97316' // Orange for warning

  return (
    <div className="quality-gauge">
      <div className="gauge-circle" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle
            className="gauge-circle-bg"
            cx={size / 2}
            cy={size / 2}
            r={radius}
          />
          <circle
            className="gauge-circle-fill"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="gauge-value">
          <div className="gauge-number" style={{ color }}>
            {Math.round(animatedScore)}
          </div>
          <div className="gauge-label">Quality</div>
        </div>
      </div>
    </div>
  )
}
