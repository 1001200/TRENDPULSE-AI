import React, { useState } from 'react'
import { DollarSign, Tag, TrendingUp } from 'lucide-react'

/**
 * PriceBracketBarChart — Vertical bar chart showing apparel revenue and unit volume across retail price tiers
 * Provides clear comparison across pricing brackets with currency formatting and interactive tooltips
 */
export default function PriceBracketBarChart({
  salesByPriceRange = [],
  dominantPriceBracket,
  totalRevenue = 0,
  totalUnits = 0
}) {
  const [metricMode, setMetricMode] = useState('revenue') // 'revenue' | 'units'
  const [hoveredIdx, setHoveredIdx] = useState(null)

  const bracketList = salesByPriceRange || []
  const hasData = bracketList.length > 0 && bracketList.some(b => (b.revenue > 0) || (b.units > 0))

  const calcTotalRev = totalRevenue || bracketList.reduce((acc, b) => acc + (b.revenue || 0), 0)
  const calcTotalUnits = totalUnits || bracketList.reduce((acc, b) => acc + (b.units || 0), 0)

  // Max value for scaling
  const maxVal = Math.max(
    ...bracketList.map(b => (metricMode === 'revenue' ? (b.revenue || 0) : (b.units || 0))),
    1
  ) * 1.15

  // SVG dimensions
  const svgWidth = 480
  const svgHeight = 220
  const padLeft = 56
  const padRight = 20
  const padTop = 22
  const padBottom = 40
  const plotWidth = svgWidth - padLeft - padRight
  const plotHeight = svgHeight - padTop - padBottom

  // Y-axis ticks
  const yTicks = [0, Math.round(maxVal * 0.5), Math.round(maxVal)]

  const formatY = (val) => {
    if (val === 0) return '₹0'
    if (metricMode === 'revenue') {
      if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`
      if (val >= 100000) return `₹${Math.round(val / 100000)}L`
      if (val >= 1000) return `₹${Math.round(val / 1000)}K`
      return `₹${val}`
    } else {
      if (val >= 1000) return `${(val / 1000).toFixed(1)}K`
      return val
    }
  }

  // Shorten label for clean X-axis readability
  const shortenBracketLabel = (range) => {
    if (!range) return ''
    return range
      .replace('Under ₹1,000', '< ₹1,000')
      .replace('Over ₹2,000', '> ₹2,000')
      .replace('₹1,000 - ₹1,499', '₹1K – ₹1.5K')
      .replace('₹1,500 - ₹1,999', '₹1.5K – ₹2K')
      .replace(' - ', '–')
  }

  const barWidth = Math.min(48, Math.max(28, (plotWidth / Math.max(1, bracketList.length)) - 24))

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.65rem',
        marginBottom: '0.85rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h3 style={{
              fontSize: '1.08rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sales by Price Bracket
            </h3>
            {dominantPriceBracket?.range && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 600,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(6, 78, 53, 0.12)'
              }}>
                Top: {dominantPriceBracket.range} ({dominantPriceBracket.pct_of_sales}%)
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Vertical distribution of revenue and volume across pricing tiers
          </span>
        </div>

        {/* Metric Switcher Segmented Pill */}
        <div className="segmented-control">
          <button
            type="button"
            className={`segmented-control-btn ${metricMode === 'revenue' ? 'active' : ''}`}
            onClick={() => setMetricMode('revenue')}
          >
            By Revenue (₹)
          </button>
          <button
            type="button"
            className={`segmented-control-btn ${metricMode === 'units' ? 'active' : ''}`}
            onClick={() => setMetricMode('units')}
          >
            By Units
          </button>
        </div>
      </div>

      {/* Main Chart Content */}
      {!hasData ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No price tier data recorded for the selected period.
        </div>
      ) : (
        <div style={{ position: 'relative', width: '100%', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
          >
            {/* Grid Lines and Y-Axis */}
            {yTicks.map((val, idx) => {
              const y = padTop + plotHeight - (val / maxVal) * plotHeight
              return (
                <g key={idx}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={padLeft + plotWidth}
                    y2={y}
                    stroke="rgba(18, 38, 28, 0.06)"
                    strokeDasharray={idx === 0 ? 'none' : '3 3'}
                  />
                  <text
                    x={padLeft - 8}
                    y={y + 4}
                    textAnchor="end"
                    fontSize="9.5"
                    fill="var(--text-muted)"
                    fontWeight="500"
                    fontFamily="var(--font-sans)"
                  >
                    {formatY(val)}
                  </text>
                </g>
              )
            })}

            {/* Vertical Bars */}
            {bracketList.map((b, idx) => {
              const val = metricMode === 'revenue' ? (b.revenue || 0) : (b.units || 0)
              const isDominant = dominantPriceBracket?.range === b.range
              const isHovered = hoveredIdx === idx

              const slotWidth = plotWidth / bracketList.length
              const x = padLeft + idx * slotWidth + (slotWidth - barWidth) / 2
              const barHeight = Math.max(4, (val / maxVal) * plotHeight)
              const y = padTop + plotHeight - barHeight

              const barFill = isDominant ? '#064E35' : (isHovered ? '#0F6B4B' : '#2D8A68')

              return (
                <g key={b.range}>
                  {/* Bar */}
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={barHeight}
                    rx={5}
                    fill={barFill}
                    style={{
                      cursor: 'pointer',
                      transition: 'opacity 0.2s ease, fill 0.2s ease, filter 0.2s ease',
                      filter: isHovered || isDominant ? 'drop-shadow(0 4px 10px rgba(6, 78, 53, 0.25))' : 'none',
                      opacity: hoveredIdx !== null && !isHovered ? 0.6 : 1
                    }}
                    onMouseEnter={() => setHoveredIdx(idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                  />

                  {/* Value Above Bar */}
                  <text
                    x={x + barWidth / 2}
                    y={y - 6}
                    textAnchor="middle"
                    fontSize="9.5"
                    fontWeight="700"
                    fill={isDominant ? 'var(--forest-green)' : 'var(--text-secondary)'}
                    fontFamily="var(--font-sans)"
                  >
                    {metricMode === 'revenue'
                      ? (b.revenue_formatted || `₹${Math.round(b.revenue / 1000)}K`)
                      : b.units?.toLocaleString()}
                  </text>

                  {/* X-axis Label */}
                  <text
                    x={x + barWidth / 2}
                    y={padTop + plotHeight + 16}
                    textAnchor="middle"
                    fontSize="9.5"
                    fill={isDominant ? 'var(--forest-green)' : 'var(--text-secondary)'}
                    fontWeight={isDominant ? '700' : '600'}
                    fontFamily="var(--font-sans)"
                  >
                    {shortenBracketLabel(b.range)}
                  </text>

                  {/* Percentage Subtitle */}
                  <text
                    x={x + barWidth / 2}
                    y={padTop + plotHeight + 28}
                    textAnchor="middle"
                    fontSize="8.5"
                    fill="var(--text-muted)"
                    fontWeight="500"
                    fontFamily="var(--font-sans)"
                  >
                    {metricMode === 'revenue' ? `${b.pct_of_sales}%` : `${b.pct_of_units || 0}%`}
                  </text>
                </g>
              )
            })}
          </svg>

          {/* Tooltip on Hover */}
          {hoveredIdx !== null && bracketList[hoveredIdx] && (() => {
            const b = bracketList[hoveredIdx]
            return (
              <div
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: 'rgba(5, 61, 42, 0.95)',
                  color: '#ffffff',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: '0 4px 14px rgba(5, 61, 42, 0.25)',
                  pointerEvents: 'none',
                  zIndex: 10,
                  fontSize: '0.72rem',
                  border: '1px solid rgba(255, 255, 255, 0.15)'
                }}
              >
                <div style={{ fontWeight: 800, color: 'var(--accent-lime)' }}>{b.range}</div>
                <div>{b.revenue_formatted} revenue ({b.pct_of_sales}% share)</div>
                <div style={{ opacity: 0.85 }}>{b.units?.toLocaleString()} garments sold</div>
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}
