import React, { useState } from 'react'

/**
 * MonthlyCategoryBarChart — Grouped vertical bar chart for monthly apparel category performance
 * Matches Reference Image #6
 */
export default function MonthlyCategoryBarChart({ monthlyTrends = [] }) {
  const [metricMode, setMetricMode] = useState('revenue') // 'revenue' | 'units'
  const [hoveredBar, setHoveredBar] = useState(null) // { month, category, val }

  const categories = ['Bottoms', 'Tops', 'Outerwear', 'Dresses', 'Knitwear']
  const catColors = {
    'Bottoms': '#064E35',
    'Tops': '#0F6B4B',
    'Outerwear': '#2D8A68',
    'Dresses': '#5AB892',
    'Knitwear': '#A3DAC3'
  }

  // Parse monthly trends
  const monthsData = (monthlyTrends || []).map(m => {
    // Normalise categories array if it contains powershell @{} string notation or objects
    const catMap = {}
    const rawList = m.categories || []
    rawList.forEach(c => {
      if (typeof c === 'string') {
        const catMatch = c.match(/category=([^;]+)/)
        const revMatch = c.match(/revenue=([^;]+)/)
        const unitsMatch = c.match(/units=([^;]+)/)
        if (catMatch) {
          catMap[catMatch[1].trim()] = {
            category: catMatch[1].trim(),
            revenue: parseFloat(revMatch ? revMatch[1] : 0),
            units: parseInt(unitsMatch ? unitsMatch[1] : 0)
          }
        }
      } else if (c && typeof c === 'object') {
        catMap[c.category] = c
      }
    })

    return {
      month: m.month,
      shortMonth: m.month ? m.month.split(' ')[0].slice(0, 3) + ' ' + (m.month.split(' ')[1] || '') : '',
      displayMonth: m.month ? m.month.split(' ')[0].slice(0, 3) : '',
      catMap
    }
  })

  // Compute max value for scaling
  let maxVal = 0
  monthsData.forEach(m => {
    categories.forEach(cat => {
      const val = metricMode === 'revenue' 
        ? (m.catMap[cat]?.revenue || 0)
        : (m.catMap[cat]?.units || 0)
      if (val > maxVal) maxVal = val
    })
  })
  maxVal = maxVal > 0 ? Math.ceil(maxVal * 1.15) : 1000

  // SVG layout
  const svgWidth = 560
  const svgHeight = 220
  const padLeft = 48
  const padRight = 20
  const padTop = 20
  const padBottom = 34
  const plotWidth = svgWidth - padLeft - padRight
  const plotHeight = svgHeight - padTop - padBottom

  // Y-axis ticks
  const yTicks = [
    0,
    Math.round(maxVal * 0.5),
    maxVal
  ]

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

  const groupWidth = plotWidth / Math.max(1, monthsData.length)
  const barWidth = Math.max(6, Math.min(14, (groupWidth - 28) / categories.length))

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '0.85rem'
      }}>
        <div>
          <h3 style={{
            fontSize: '1.08rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Monthly Category Performance
          </h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Multi-month category comparison across seasons
          </span>
        </div>

        {/* Metric Switcher Toggle */}
        <div className="segmented-control">
          <button
            type="button"
            className={`segmented-control-btn ${metricMode === 'revenue' ? 'active' : ''}`}
            onClick={() => setMetricMode('revenue')}
          >
            Revenue (₹)
          </button>
          <button
            type="button"
            className={`segmented-control-btn ${metricMode === 'units' ? 'active' : ''}`}
            onClick={() => setMetricMode('units')}
          >
            Units Sold
          </button>
        </div>
      </div>

      {/* Category Legend */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        marginBottom: '0.75rem',
        flexWrap: 'wrap'
      }}>
        {categories.map(cat => (
          <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: catColors[cat] }} />
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{cat}</span>
          </div>
        ))}
      </div>

      {monthsData.length === 0 ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No monthly trend data recorded.
        </div>
      ) : (
        <div style={{ position: 'relative', width: '100%' }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
          >
            {/* Grid lines and Y axis */}
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

            {/* Monthly Groups with Vertical Bars */}
            {monthsData.map((m, mIdx) => {
              const groupX = padLeft + mIdx * groupWidth + (groupWidth - (categories.length * barWidth + (categories.length - 1) * 3)) / 2

              return (
                <g key={mIdx}>
                  {/* Category Bars inside this Month */}
                  {categories.map((cat, cIdx) => {
                    const item = m.catMap[cat]
                    const val = metricMode === 'revenue' ? (item?.revenue || 0) : (item?.units || 0)
                    const barHeight = Math.max(3, (val / maxVal) * plotHeight)
                    const x = groupX + cIdx * (barWidth + 3)
                    const y = padTop + plotHeight - barHeight

                    const isHovered = hoveredBar?.month === m.month && hoveredBar?.category === cat

                    return (
                      <g key={cat}>
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx={3}
                          fill={catColors[cat]}
                          style={{
                            cursor: 'pointer',
                            transition: 'opacity 0.15s ease, transform 0.15s ease',
                            opacity: hoveredBar && !isHovered ? 0.45 : 1,
                            filter: isHovered ? 'drop-shadow(0 2px 6px rgba(6, 78, 53, 0.35))' : 'none'
                          }}
                          onMouseEnter={() => setHoveredBar({
                            month: m.month,
                            category: cat,
                            val,
                            revenueFormatted: item?.revenue ? `₹${item.revenue.toLocaleString()}` : '₹0',
                            units: item?.units || 0,
                            x: x + barWidth / 2,
                            y
                          })}
                          onMouseLeave={() => setHoveredBar(null)}
                        />
                      </g>
                    )
                  })}

                  {/* X-axis Month Label */}
                  <text
                    x={groupX + (categories.length * barWidth) / 2}
                    y={padTop + plotHeight + 18}
                    textAnchor="middle"
                    fontSize="10"
                    fill="var(--text-secondary)"
                    fontWeight="600"
                    fontFamily="var(--font-sans)"
                  >
                    {m.displayMonth || m.shortMonth}
                  </text>
                </g>
              )
            })}
          </svg>

          {/* Floating Tooltip */}
          {hoveredBar && (
            <div
              style={{
                position: 'absolute',
                left: `${(hoveredBar.x / svgWidth) * 100}%`,
                top: `${Math.max(5, (hoveredBar.y / svgHeight) * 100 - 35)}%`,
                transform: 'translate(-50%, -100%)',
                background: 'rgba(5, 61, 42, 0.95)',
                color: '#ffffff',
                padding: '6px 11px',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 6px 18px rgba(5, 61, 42, 0.28)',
                pointerEvents: 'none',
                zIndex: 20,
                whiteSpace: 'nowrap',
                fontSize: '0.72rem',
                border: '1px solid rgba(255, 255, 255, 0.16)'
              }}
            >
              <div style={{ fontWeight: 800, color: 'var(--accent-lime)', fontSize: '0.76rem' }}>
                {hoveredBar.category}: {hoveredBar.revenueFormatted}
              </div>
              <div style={{ color: 'rgba(255, 255, 255, 0.85)', fontSize: '0.67rem', marginTop: '1px' }}>
                {hoveredBar.units} items sold in {hoveredBar.month}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
