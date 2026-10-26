import React, { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react'

export default function SalesOverviewChart({ timelineData, loading, externalPeriod }) {
  const [selectedPeriod, setSelectedPeriod] = useState('monthly') // '7d' | '30d' | 'monthly'
  const [hoveredIndex, setHoveredIndex] = useState(null)

  // Synchronize with external Overview selector when changed
  useEffect(() => {
    if (!externalPeriod) return
    if (externalPeriod === '7d' || externalPeriod === 'last_7_days') {
      setSelectedPeriod('7d')
    } else if (externalPeriod === '30d' || externalPeriod === 'last_30_days') {
      setSelectedPeriod('30d')
    } else if (externalPeriod === 'monthly' || externalPeriod === 'this_month' || externalPeriod === 'all' || (typeof externalPeriod === 'string' && (externalPeriod.startsWith('month') || externalPeriod.includes('-')))) {
      setSelectedPeriod('monthly')
    }
    setHoveredIndex(null)
  }, [externalPeriod])

  // Select appropriate dataset based on period
  let currentDataset = null
  let periodLabel = 'Monthly'
  if (selectedPeriod === '7d') {
    currentDataset = timelineData?.last_7_days
    periodLabel = 'Last 7 Days'
  } else if (selectedPeriod === '30d') {
    currentDataset = timelineData?.last_30_days
    periodLabel = 'Last 30 Days'
  } else if (selectedPeriod === 'monthly') {
    currentDataset = timelineData?.monthly
    periodLabel = 'Monthly'
  }

  const points = currentDataset?.points || []
  const summary = currentDataset?.summary || {}

  const hasPoints = points.length > 0
  const totalRevenue = summary.total_revenue ?? 0
  const totalRevenueFormatted = summary.total_revenue_formatted ?? `₹${totalRevenue.toLocaleString()}`
  const dateRange = summary.date_range || ''

  const avgLabel = selectedPeriod === 'monthly' ? 'Monthly Avg' : 'Daily Avg'
  const avgValFormatted = selectedPeriod === 'monthly' 
    ? (summary.avg_monthly_revenue_formatted || `₹${Math.round(totalRevenue / Math.max(1, points.length)).toLocaleString()}`)
    : (summary.avg_daily_revenue_formatted || `₹${Math.round(totalRevenue / Math.max(1, points.length)).toLocaleString()}`)

  const growthPct = summary.growth_pct ?? null
  const growthPositive = summary.growth_is_positive ?? (growthPct !== null && growthPct >= 0)

  // SVG Dimensions
  const svgWidth = 640
  const svgHeight = 230
  const padLeft = 52
  const padRight = 44
  const padTop = 26
  const padBottom = 34
  const plotWidth = svgWidth - padLeft - padRight
  const plotHeight = svgHeight - padTop - padBottom

  // Scales
  const maxRevenueRaw = Math.max(...points.map(p => p.revenue || 0), 0)
  const maxRevenue = maxRevenueRaw > 0 ? Math.ceil(maxRevenueRaw * 1.2) : 1000

  const maxUnitsRaw = Math.max(...points.map(p => p.units || 0), 0)
  const maxUnits = maxUnitsRaw > 0 ? Math.ceil(maxUnitsRaw * 1.25) : 100

  // 4 Y-axis ticks for Revenue (Left Axis)
  const yTicks = [
    0,
    Math.round(maxRevenue * 0.33),
    Math.round(maxRevenue * 0.66),
    maxRevenue
  ]

  // Y-axis ticks for Units (Right Axis)
  const formatRightY = (pct) => {
    const val = Math.round(maxUnits * pct)
    if (val >= 1000) return `${(val / 1000).toFixed(0)}K`
    return val
  }

  const formatYTick = (val) => {
    if (val === 0) return '₹0'
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`
    if (val >= 100000) return `₹${Math.round(val / 100000)}L`
    if (val >= 1000) return `₹${(val / 1000).toFixed(1).replace('.0', '')}K`
    return `₹${val}`
  }

  // Calculate coordinates for points and bars
  const coords = points.map((pt, idx) => {
    const x = points.length === 1 
      ? padLeft + plotWidth / 2 
      : padLeft + (idx / Math.max(1, points.length - 1)) * plotWidth
    const y = padTop + plotHeight - ((pt.revenue || 0) / maxRevenue) * plotHeight
    const barHeight = Math.max(4, ((pt.units || 0) / maxUnits) * plotHeight)
    const barY = padTop + plotHeight - barHeight

    return { ...pt, x, y, barHeight, barY, idx }
  })

  // Width of vertical unit bars
  const barWidth = points.length <= 4 
    ? 38 
    : points.length <= 8 
    ? 22 
    : Math.max(6, Math.min(12, (plotWidth / points.length) * 0.55))

  // Build SVG path strings for Line
  let linePath = ''
  if (coords.length === 1) {
    const pt = coords[0]
    linePath = `M ${padLeft} ${pt.y} L ${padLeft + plotWidth} ${pt.y}`
  } else if (coords.length > 1) {
    linePath = `M ${coords[0].x} ${coords[0].y}`
    coords.slice(1).forEach(pt => {
      linePath += ` L ${pt.x} ${pt.y}`
    })
  }

  // X-axis label filtering
  const shouldShowXLabel = (idx, total) => {
    if (total <= 8) return true
    if (total <= 16) return idx % 2 === 0 || idx === total - 1
    return idx % 5 === 0 || idx === total - 1
  }

  const activePoint = hoveredIndex !== null && coords[hoveredIndex] ? coords[hoveredIndex] : null

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', position: 'relative' }}>
      {/* 1. Header Row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.85rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h3 style={{ fontSize: '1.08rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
              Monthly Sales Trend
            </h3>
            {dateRange && (
              <span className="insights-badge">
                {dateRange}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Revenue and units sold over time
          </span>
        </div>

        {/* View Selection Segmented Control */}
        <div className="segmented-control">
          {[
            { id: '7d', label: 'Last 7 Days' },
            { id: '30d', label: 'Last 30 Days' },
            { id: 'monthly', label: 'Monthly' }
          ].map(view => (
            <button
              key={view.id}
              onClick={() => {
                setSelectedPeriod(view.id)
                setHoveredIndex(null)
              }}
              className={`segmented-control-btn ${selectedPeriod === view.id ? 'active' : ''}`}
            >
              {view.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Dual-Metric Legend & Summary Info (Matches Reference Image #2) */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.85rem',
        marginBottom: '0.75rem'
      }}>
        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.15rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--forest-green)' }} />
            <span style={{ fontSize: '0.73rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Revenue (₹)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#CADCD2' }} />
            <span style={{ fontSize: '0.73rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Units Sold</span>
          </div>
        </div>

        {/* Revenue Highlight */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{avgLabel}:</span>
          <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
            {avgValFormatted}
          </span>
          {growthPct !== null && growthPct !== 0 && (
            <span className={`pill-badge ${growthPositive ? 'green' : 'red'}`} style={{ fontSize: '0.66rem', marginLeft: '0.35rem' }}>
              {growthPositive ? `+${growthPct}%` : `${growthPct}%`}
            </span>
          )}
        </div>
      </div>

      {/* 3. SVG Line + Bar Combo Graph */}
      {!hasPoints ? (
        <div style={{ height: '190px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No sales recorded for this period.
        </div>
      ) : (
        <div style={{ position: 'relative', width: '100%', userSelect: 'none' }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
          >
            <defs>
              {/* Mint green gradient for unit bars */}
              <linearGradient id="unitsBarMintGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#CADCD2" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#DDF2E3" stopOpacity="0.6" />
              </linearGradient>
            </defs>

            {/* Horizontal Gridlines & Left Y-Axis Labels (Revenue) */}
            {yTicks.map((val, i) => {
              const yPos = padTop + plotHeight - (val / maxRevenue) * plotHeight
              const pct = val / maxRevenue
              return (
                <g key={i}>
                  <line
                    x1={padLeft}
                    y1={yPos}
                    x2={padLeft + plotWidth}
                    y2={yPos}
                    stroke="rgba(18, 38, 28, 0.05)"
                    strokeDasharray={val === 0 ? 'none' : '3 3'}
                    strokeWidth={val === 0 ? 1.2 : 1}
                  />
                  {/* Left Label: Revenue */}
                  <text
                    x={padLeft - 8}
                    y={yPos + 3.5}
                    textAnchor="end"
                    fontSize="9.5"
                    fontWeight="500"
                    fill="var(--text-muted)"
                    fontFamily="var(--font-sans)"
                  >
                    {formatYTick(val)}
                  </text>
                  {/* Right Label: Units */}
                  <text
                    x={padLeft + plotWidth + 8}
                    y={yPos + 3.5}
                    textAnchor="start"
                    fontSize="9.5"
                    fontWeight="500"
                    fill="var(--text-muted)"
                    fontFamily="var(--font-sans)"
                  >
                    {formatRightY(pct)}
                  </text>
                </g>
              )
            })}

            {/* Combo Element 1: Soft Mint Vertical Bars for Units Sold */}
            {coords.map((pt, idx) => {
              const isHovered = hoveredIndex === idx
              const xPos = pt.x - barWidth / 2

              return (
                <g key={`bar-${idx}`}>
                  <rect
                    x={xPos}
                    y={pt.barY}
                    width={barWidth}
                    height={pt.barHeight}
                    rx={4}
                    fill="url(#unitsBarMintGrad)"
                    style={{
                      transition: 'opacity 0.15s ease',
                      opacity: hoveredIndex !== null && !isHovered ? 0.45 : 1
                    }}
                  />
                </g>
              )
            })}

            {/* Combo Element 2: Deep Forest Green Trend Line for Revenue */}
            {linePath && (
              <path
                d={linePath}
                fill="none"
                stroke="var(--forest-green)"
                strokeWidth="2.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ transition: 'd 0.3s ease' }}
              />
            )}

            {/* Hover Guide Line */}
            {activePoint && (
              <line
                x1={activePoint.x}
                y1={padTop}
                x2={activePoint.x}
                y2={padTop + plotHeight}
                stroke="var(--forest-green)"
                strokeWidth="1.2"
                strokeDasharray="2 2"
                opacity="0.5"
              />
            )}

            {/* Circular Data Nodes on the Line */}
            {coords.map((pt, idx) => {
              const isHovered = hoveredIndex === idx
              return (
                <g key={`pt-${idx}`}>
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={isHovered ? 6 : 3.8}
                    fill={isHovered ? '#ffffff' : 'var(--forest-green)'}
                    stroke="var(--forest-green)"
                    strokeWidth={isHovered ? 3 : 2}
                    style={{
                      transition: 'all 0.15s ease',
                      cursor: 'pointer',
                      filter: isHovered ? 'drop-shadow(0 2px 6px rgba(6,78,53,0.35))' : 'none'
                    }}
                  />

                  {/* Invisible broad hover target */}
                  <rect
                    x={pt.x - (plotWidth / (points.length * 2))}
                    y={padTop}
                    width={plotWidth / points.length}
                    height={plotHeight + 20}
                    fill="transparent"
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHoveredIndex(idx)}
                    onMouseLeave={() => setHoveredIndex(null)}
                  />
                </g>
              )
            })}

            {/* X-Axis Labels */}
            {coords.map((pt, idx) => {
              if (!shouldShowXLabel(idx, coords.length)) return null
              const label = pt.display_date || pt.display_month || pt.month || ''
              return (
                <text
                  key={`lbl-${idx}`}
                  x={pt.x}
                  y={padTop + plotHeight + 17}
                  textAnchor="middle"
                  fontSize="9.5"
                  fontWeight="600"
                  fill={hoveredIndex === idx ? 'var(--forest-green)' : 'var(--text-secondary)'}
                  fontFamily="var(--font-sans)"
                >
                  {label}
                </text>
              )
            })}
          </svg>

          {/* Floating Tooltip */}
          {activePoint && (
            <div
              style={{
                position: 'absolute',
                left: `${(activePoint.x / svgWidth) * 100}%`,
                top: `${Math.max(5, (activePoint.y / svgHeight) * 100 - 35)}%`,
                transform: 'translate(-50%, -100%)',
                background: 'rgba(5, 61, 42, 0.95)',
                color: '#ffffff',
                padding: '7px 12px',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 8px 24px rgba(5, 61, 42, 0.28)',
                backdropFilter: 'blur(8px)',
                WebkitBackdropFilter: 'blur(8px)',
                pointerEvents: 'none',
                zIndex: 10,
                whiteSpace: 'nowrap',
                fontSize: '0.72rem',
                border: '1px solid rgba(255, 255, 255, 0.16)'
              }}
            >
              <div style={{ fontWeight: 800, color: 'var(--accent-lime)', fontSize: '0.78rem', fontVariantNumeric: 'tabular-nums' }}>
                {activePoint.revenue_formatted || `₹${activePoint.revenue?.toLocaleString()}`}
              </div>
              <div style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '0.68rem', marginTop: '2px', fontWeight: 500 }}>
                {activePoint.day_name ? `${activePoint.day_name}, ` : ''}{activePoint.display_date || activePoint.month}
              </div>
              {activePoint.units !== undefined && (
                <div style={{ color: '#CADCD2', fontSize: '0.67rem', marginTop: '2px', fontWeight: 600 }}>
                  {activePoint.units?.toLocaleString()} items sold • {activePoint.orders || 0} orders
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
