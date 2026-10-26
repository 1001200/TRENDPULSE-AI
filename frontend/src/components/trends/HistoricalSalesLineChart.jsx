import React, { useState } from 'react'
import { TrendingUp, Calendar, ArrowUpRight } from 'lucide-react'

export default function HistoricalSalesLineChart({ salesByMonth = [], strongestMonth }) {
  const [hoveredIdx, setHoveredIdx] = useState(null)

  const points = salesByMonth || []
  const hasData = points.length > 0 && points.some(p => p.revenue > 0)

  // Chart dimensions & padding
  const svgWidth = 620
  const svgHeight = 210
  const padLeft = 60
  const padRight = 28
  const padTop = 22
  const padBottom = 34
  const plotWidth = svgWidth - padLeft - padRight
  const plotHeight = svgHeight - padTop - padBottom

  const maxRevenueRaw = Math.max(...points.map(p => p.revenue || 0), 0)
  const maxRevenue = maxRevenueRaw > 0 ? Math.ceil(maxRevenueRaw * 1.15) : 1000

  // 4 Y-axis ticks
  const yTicks = [
    0,
    Math.round(maxRevenue * 0.33),
    Math.round(maxRevenue * 0.66),
    maxRevenue
  ]

  const formatYTick = (val) => {
    if (val === 0) return '₹0'
    if (val >= 1000) return `₹${(val / 1000).toFixed(1).replace('.0', '')}K`
    return `₹${val}`
  }

  // Calculate coordinates
  const coords = points.map((pt, idx) => {
    const x = points.length === 1
      ? padLeft + plotWidth / 2
      : padLeft + (idx / Math.max(1, points.length - 1)) * plotWidth
    const y = padTop + plotHeight - ((pt.revenue || 0) / maxRevenue) * plotHeight
    return { ...pt, x, y, idx }
  })

  // Paths
  let linePath = ''
  let areaPath = ''
  if (coords.length === 1) {
    const pt = coords[0]
    linePath = `M ${padLeft} ${pt.y} L ${padLeft + plotWidth} ${pt.y}`
    const yBottom = padTop + plotHeight
    areaPath = `M ${padLeft} ${yBottom} L ${padLeft} ${pt.y} L ${padLeft + plotWidth} ${pt.y} L ${padLeft + plotWidth} ${yBottom} Z`
  } else if (coords.length > 1) {
    linePath = `M ${coords[0].x} ${coords[0].y}`
    coords.slice(1).forEach(pt => {
      linePath += ` L ${pt.x} ${pt.y}`
    })

    const yBottom = padTop + plotHeight
    areaPath = `M ${coords[0].x} ${yBottom} L ${coords[0].x} ${coords[0].y}`
    coords.slice(1).forEach(pt => {
      areaPath += ` L ${pt.x} ${pt.y}`
    })
    areaPath += ` L ${coords[coords.length - 1].x} ${yBottom} Z`
  }

  const activePoint = hoveredIdx !== null && coords[hoveredIdx] ? coords[hoveredIdx] : null

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', position: 'relative' }}>
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '0.85rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h3 style={{
              fontSize: '1.08rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Monthly Sales Trajectory
            </h3>
            {strongestMonth && (
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 9px',
                borderRadius: 'var(--radius-pill)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px'
              }}>
                <ArrowUpRight size={12} />
                Peak: {strongestMonth.month} ({strongestMonth.revenue_formatted})
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
            Historical monthly revenue from verified checkouts.
          </span>
        </div>
      </div>

      {/* SVG Chart */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
          onMouseLeave={() => setHoveredIdx(null)}
        >
          <defs>
            <linearGradient id="histSalesAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#064E35" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#064E35" stopOpacity="0.01" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {yTicks.map((val, idx) => {
            const y = padTop + plotHeight - (val / maxRevenue) * plotHeight
            return (
              <g key={idx}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={padLeft + plotWidth}
                  y2={y}
                  stroke="rgba(0,0,0,0.06)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padLeft - 10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="var(--text-muted)"
                  fontFamily="var(--font-sans)"
                >
                  {formatYTick(val)}
                </text>
              </g>
            )
          })}

          {/* Area Fill */}
          {areaPath && (
            <path d={areaPath} fill="url(#histSalesAreaGradient)" />
          )}

          {/* Line */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke="var(--forest-green)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Points */}
          {coords.map((pt, idx) => {
            const isHovered = hoveredIdx === idx
            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                style={{ cursor: 'pointer' }}
              >
                <circle cx={pt.x} cy={pt.y} r="16" fill="transparent" />
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r="8"
                    fill="rgba(6, 78, 53, 0.2)"
                  />
                )}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="4.5"
                  fill="var(--forest-green)"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
                <text
                  x={pt.x}
                  y={padTop + plotHeight + 18}
                  textAnchor="middle"
                  fontSize="11"
                  fill="var(--text-secondary)"
                  fontFamily="var(--font-sans)"
                >
                  {typeof pt.month === 'string' ? pt.month.replace(' 2026', '') : (pt.month || '')}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Floating Tooltip */}
      {activePoint && (
        <div style={{
          position: 'absolute',
          top: '3.8rem',
          left: `${Math.min(75, Math.max(15, (activePoint.x / svgWidth) * 100))}%`,
          transform: 'translateX(-50%)',
          background: '#073B28',
          color: '#ffffff',
          padding: '0.5rem 0.8rem',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          fontSize: '0.75rem',
          pointerEvents: 'none',
          zIndex: 10,
          whiteSpace: 'nowrap'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '2px' }}>
            {activePoint.month}
          </div>
          <div style={{ fontSize: '0.92rem', fontWeight: 800 }}>
            ₹{activePoint.revenue?.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#CADCD2', marginTop: '2px' }}>
            {activePoint.orders || activePoint.units || 0} orders completed
          </div>
        </div>
      )}
    </div>
  )
}
