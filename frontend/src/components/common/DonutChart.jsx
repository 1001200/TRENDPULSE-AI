import React, { useState } from 'react'

/**
 * DonutChart — High-precision SVG Donut Chart with center label, hover tooltips, and legend
 * 
 * Props:
 *  - title: string
 *  - subtitle: string
 *  - data: Array of { label: string, value: number, formattedValue: string, percentage: number, sublabel?: string }
 *  - centerPrimary: string (e.g. "₹17.7L")
 *  - centerSecondary: string (e.g. "Total Revenue")
 *  - colors: string[] (Palette of Forest, Emerald, Sage, and Mint greens)
 *  - height: number (default 260)
 */
export default function DonutChart({
  title,
  subtitle,
  data = [],
  centerPrimary,
  centerSecondary = 'Total Revenue',
  colors = ['#064E35', '#0F6B4B', '#2D8A68', '#5AB892', '#A3DAC3', '#CADCD2', '#E2F0E8'],
  action
}) {
  const [hoveredIdx, setHoveredIdx] = useState(null)

  const validData = (data || []).filter(d => (d.value || d.percentage) > 0)
  const totalValue = validData.reduce((acc, d) => acc + (d.value || 0), 0)

  // Auto-compute percentages if not provided
  const items = validData.map((d, i) => {
    const pct = d.percentage !== undefined 
      ? Number(d.percentage) 
      : (totalValue > 0 ? (d.value / totalValue) * 100 : 0)
    return {
      ...d,
      pctClean: Math.round(pct * 10) / 10,
      color: colors[i % colors.length]
    }
  })

  // Dimensions
  const size = 200
  const center = size / 2
  const outerRadius = 82
  const innerRadius = 56
  const gapAngle = items.length > 1 ? 0.025 : 0 // Radians gap between slices

  // Compute angles for each slice
  let currentAngle = -Math.PI / 2 // Start at top (12 o'clock)
  const totalPct = items.reduce((acc, d) => acc + d.pctClean, 0) || 100

  const slices = items.map((item, idx) => {
    const sliceAngle = (item.pctClean / totalPct) * (Math.PI * 2)
    const startAngle = currentAngle + gapAngle / 2
    const endAngle = currentAngle + sliceAngle - gapAngle / 2
    currentAngle += sliceAngle

    // Coordinates for outer arc
    const x1 = center + outerRadius * Math.cos(startAngle)
    const y1 = center + outerRadius * Math.sin(startAngle)
    const x2 = center + outerRadius * Math.cos(endAngle)
    const y2 = center + outerRadius * Math.sin(endAngle)

    // Coordinates for inner arc
    const x3 = center + innerRadius * Math.cos(endAngle)
    const y3 = center + innerRadius * Math.sin(endAngle)
    const x4 = center + innerRadius * Math.cos(startAngle)
    const y4 = center + innerRadius * Math.sin(startAngle)

    const largeArc = sliceAngle > Math.PI ? 1 : 0

    // Path command
    const path = `
      M ${x1} ${y1}
      A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x2} ${y2}
      L ${x3} ${y3}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4}
      Z
    `

    return {
      ...item,
      path,
      idx,
      startAngle,
      endAngle
    }
  })

  // Active hover item
  const activeItem = hoveredIdx !== null ? items[hoveredIdx] : null

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.1rem' }}>
        <div>
          <h3 style={{
            fontSize: '1.08rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            {title}
          </h3>
          {subtitle && (
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
              {subtitle}
            </span>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>

      {items.length === 0 ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No distribution data recorded for this period.
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.05fr 1fr',
          gap: '1rem',
          alignItems: 'center'
        }}>
          {/* Donut SVG with Center Label */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg
              viewBox={`0 0 ${size} ${size}`}
              style={{ width: '100%', maxWidth: '210px', height: 'auto', display: 'block' }}
            >
              {slices.map((slice) => {
                const isHovered = hoveredIdx === slice.idx
                return (
                  <path
                    key={slice.idx}
                    d={slice.path}
                    fill={slice.color}
                    style={{
                      cursor: 'pointer',
                      transition: 'transform 0.18s ease, filter 0.18s ease',
                      transformOrigin: `${center}px ${center}px`,
                      transform: isHovered ? 'scale(1.04)' : 'scale(1)',
                      filter: isHovered ? 'drop-shadow(0 3px 8px rgba(6, 78, 53, 0.3))' : 'none'
                    }}
                    onMouseEnter={() => setHoveredIdx(slice.idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                  />
                )
              })}
            </svg>

            {/* Center Label (Matches Reference Image) */}
            <div style={{
              position: 'absolute',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
              textAlign: 'center',
              width: `${innerRadius * 1.8}px`
            }}>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.25rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                lineHeight: 1.1,
                fontVariantNumeric: 'tabular-nums'
              }}>
                {activeItem ? (activeItem.formattedValue || `₹${activeItem.value?.toLocaleString()}`) : centerPrimary}
              </span>
              <span style={{
                fontSize: '0.64rem',
                fontWeight: 600,
                color: activeItem ? 'var(--forest-green)' : 'var(--text-muted)',
                marginTop: '2px',
                textTransform: 'uppercase',
                letterSpacing: '0.04em'
              }}>
                {activeItem ? activeItem.label : centerSecondary}
              </span>
              {activeItem && (
                <span style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  color: 'var(--forest-green)',
                  marginTop: '1px'
                }}>
                  {activeItem.pctClean}%
                </span>
              )}
            </div>
          </div>

          {/* Slices Legend on Right (Matches Reference Image) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {items.map((item, idx) => {
              const isHovered = hoveredIdx === idx
              return (
                <div
                  key={idx}
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '3px 6px',
                    borderRadius: 'var(--radius-sm)',
                    background: isHovered ? 'var(--mint-soft)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                  title={`${item.label}: ${item.formattedValue || `₹${item.value}`} (${item.pctClean}%)`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
                    <span style={{
                      width: '9px',
                      height: '9px',
                      borderRadius: '50%',
                      backgroundColor: item.color,
                      flexShrink: 0
                    }} />
                    <span style={{
                      fontSize: '0.78rem',
                      fontWeight: isHovered ? 700 : 600,
                      color: isHovered ? 'var(--forest-green)' : 'var(--text-secondary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {item.label}
                    </span>
                  </div>

                  <span style={{
                    fontSize: '0.76rem',
                    fontWeight: 700,
                    color: isHovered ? 'var(--forest-green)' : 'var(--text-primary)',
                    fontVariantNumeric: 'tabular-nums',
                    marginLeft: '0.5rem'
                  }}>
                    {item.pctClean}%
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
