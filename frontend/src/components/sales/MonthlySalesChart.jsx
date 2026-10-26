import React, { useState } from 'react'
import { TrendingUp, Calendar, Info } from 'lucide-react'

export default function MonthlySalesChart({ salesByMonth = [], insightText, period }) {
  const [hoveredIndex, setHoveredIndex] = useState(null)
  const [chartMode, setChartMode] = useState('line') // 'line' | 'bar'

  const points = salesByMonth || []
  const hasData = points.length > 0 && points.some(p => p.revenue > 0)

  // Chart dimensions & padding
  const svgWidth = 640
  const svgHeight = 210
  const padLeft = 56
  const padRight = 24
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
    if (val >= 100000) return `₹${(val / 1000).toFixed(0)}K`
    if (val >= 1000) return `₹${(val / 1000).toFixed(1).replace('.0', '')}K`
    return `₹${val}`
  }

  // Calculate coordinates for points
  const coords = points.map((pt, idx) => {
    const x = points.length === 1
      ? padLeft + plotWidth / 2
      : padLeft + (idx / Math.max(1, points.length - 1)) * plotWidth
    const y = padTop + plotHeight - ((pt.revenue || 0) / maxRevenue) * plotHeight
    return { ...pt, x, y, idx }
  })

  // Build SVG path strings
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

  const activePoint = hoveredIndex !== null && coords[hoveredIndex] ? coords[hoveredIndex] : null

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
            {insightText && (
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 9px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(6, 78, 53, 0.12)'
              }}>
                {insightText}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            {chartMode === 'line' ? 'Continuous revenue trend across calendar months' : 'Vertical monthly revenue comparison'}
          </span>
        </div>

        {/* View Toggle */}
        <div className="segmented-control">
          <button
            type="button"
            className={`segmented-control-btn ${chartMode === 'line' ? 'active' : ''}`}
            onClick={() => setChartMode('line')}
          >
            Trend Line
          </button>
          <button
            type="button"
            className={`segmented-control-btn ${chartMode === 'bar' ? 'active' : ''}`}
            onClick={() => setChartMode('bar')}
          >
            Bar Comparison
          </button>
        </div>
      </div>

      {/* SVG Chart Area */}
      {!hasData ? (
        <div style={{
          height: '210px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          background: '#FAFBF9',
          borderRadius: 'var(--radius-md)',
          gap: '0.5rem'
        }}>
          <Calendar size={24} color="var(--forest-green)" opacity={0.5} />
          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>No monthly sales data for this period</span>
        </div>
      ) : (
        <div style={{ width: '100%', position: 'relative', overflow: 'hidden' }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
          >
            <defs>
              <linearGradient id="monthlyAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#064E35" stopOpacity="0.20" />
                <stop offset="60%" stopColor="#064E35" stopOpacity="0.05" />
                <stop offset="100%" stopColor="#064E35" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Light horizontal gridlines & Y-axis labels */}
            {yTicks.map((tickVal, idx) => {
              const yPos = padTop + plotHeight - (tickVal / maxRevenue) * plotHeight
              return (
                <g key={idx}>
                  <line
                    x1={padLeft}
                    y1={yPos}
                    x2={padLeft + plotWidth}
                    y2={yPos}
                    stroke="rgba(18, 38, 28, 0.06)"
                    strokeWidth="1"
                    strokeDasharray={idx === 0 ? 'none' : '3 3'}
                  />
                  <text
                    x={padLeft - 10}
                    y={yPos + 4}
                    textAnchor="end"
                    fontSize="10"
                    fill="var(--text-muted)"
                    fontWeight="500"
                  >
                    {formatYTick(tickVal)}
                  </text>
                </g>
              )
            })}

            {chartMode === 'line' ? (
              /* --- LINE CHART MODE --- */
              <>
                {/* Gradient Area beneath line */}
                {areaPath && (
                  <path
                    d={areaPath}
                    fill="url(#monthlyAreaGrad)"
                  />
                )}

                {/* Main Forest-Green Trend Line */}
                {linePath && (
                  <path
                    d={linePath}
                    fill="none"
                    stroke="var(--forest-green)"
                    strokeWidth="2.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* X-axis labels and points */}
                {coords.map((pt, idx) => (
                  <g key={idx}>
                    {/* Vertical guide on hover */}
                    {hoveredIndex === idx && (
                      <line
                        x1={pt.x}
                        y1={padTop}
                        x2={pt.x}
                        y2={padTop + plotHeight}
                        stroke="var(--forest-green)"
                        strokeWidth="1"
                        strokeDasharray="2 2"
                        opacity="0.5"
                      />
                    )}

                    {/* X-Axis Month Label */}
                    <text
                      x={pt.x}
                      y={padTop + plotHeight + 18}
                      textAnchor="middle"
                      fontSize="11"
                      fill={hoveredIndex === idx ? 'var(--forest-green)' : 'var(--text-secondary)'}
                      fontWeight={hoveredIndex === idx ? '700' : '600'}
                    >
                      {pt.display_month || pt.month}
                    </text>

                    {/* Data point circle */}
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r={hoveredIndex === idx ? 6 : 4}
                      fill="#ffffff"
                      stroke="var(--forest-green)"
                      strokeWidth={hoveredIndex === idx ? 3 : 2.2}
                      style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                      onMouseEnter={() => setHoveredIndex(idx)}
                      onMouseLeave={() => setHoveredIndex(null)}
                    />

                    {/* Invisible hover area for easy interaction */}
                    <rect
                      x={pt.x - 20}
                      y={padTop}
                      width={40}
                      height={plotHeight + 20}
                      fill="transparent"
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredIndex(idx)}
                      onMouseLeave={() => setHoveredIndex(null)}
                    />
                  </g>
                ))}
              </>
            ) : (
              /* --- VERTICAL BAR CHART MODE --- */
              <>
                {points.map((pt, idx) => {
                  const slotWidth = plotWidth / points.length
                  const barWidth = Math.min(52, slotWidth * 0.55)
                  const x = padLeft + idx * slotWidth + (slotWidth - barWidth) / 2
                  const barHeight = Math.max(4, ((pt.revenue || 0) / maxRevenue) * plotHeight)
                  const y = padTop + plotHeight - barHeight
                  const isHovered = hoveredIndex === idx

                  return (
                    <g key={idx}>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={barHeight}
                        rx={5}
                        fill={isHovered ? '#0F6B4B' : '#064E35'}
                        style={{
                          cursor: 'pointer',
                          transition: 'fill 0.15s ease, filter 0.15s ease',
                          filter: isHovered ? 'drop-shadow(0 4px 12px rgba(6, 78, 53, 0.3))' : 'none'
                        }}
                        onMouseEnter={() => setHoveredIndex(idx)}
                        onMouseLeave={() => setHoveredIndex(null)}
                      />

                      {/* Revenue on top */}
                      <text
                        x={x + barWidth / 2}
                        y={y - 6}
                        textAnchor="middle"
                        fontSize="10"
                        fill="var(--forest-green)"
                        fontWeight="700"
                      >
                        {pt.revenue_formatted}
                      </text>

                      {/* X-axis Month Label */}
                      <text
                        x={x + barWidth / 2}
                        y={padTop + plotHeight + 18}
                        textAnchor="middle"
                        fontSize="11"
                        fill={isHovered ? 'var(--forest-green)' : 'var(--text-secondary)'}
                        fontWeight={isHovered ? '700' : '600'}
                      >
                        {pt.display_month || pt.month}
                      </text>
                    </g>
                  )
                })}
              </>
            )}

            {/* Hover Tooltip Box */}
            {activePoint && chartMode === 'line' && (
              <g
                transform={`translate(${
                  Math.min(Math.max(activePoint.x - 65, 10), svgWidth - 140)
                }, ${Math.max(activePoint.y - 56, 6)})`}
                style={{ pointerEvents: 'none' }}
              >
                <rect
                  width="130"
                  height="48"
                  rx="8"
                  fill="#064E35"
                  filter="drop-shadow(0 4px 10px rgba(0,0,0,0.18))"
                />
                <text
                  x="10"
                  y="18"
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="600"
                >
                  {activePoint.month}
                </text>
                <text
                  x="10"
                  y="34"
                  fill="#CADCD2"
                  fontSize="12"
                  fontWeight="800"
                  fontFamily="var(--font-display)"
                >
                  {activePoint.revenue_formatted}
                </text>
                <text
                  x="76"
                  y="34"
                  fill="rgba(255,255,255,0.75)"
                  fontSize="9.5"
                  fontWeight="500"
                >
                  • {activePoint.orders} orders
                </text>
              </g>
            )}
          </svg>
        </div>
      )}
    </div>
  )
}
