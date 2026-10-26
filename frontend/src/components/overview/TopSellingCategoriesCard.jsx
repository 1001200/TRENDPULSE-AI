import React, { useState } from 'react'

/**
 * TopSellingCategoriesCard — Clean progress bars with modern styling
 * Matches Reference Image #4
 */
export default function TopSellingCategoriesCard({ categories = [], totalSalesRaw, totalUnitsSold }) {
  const [metricMode, setMetricMode] = useState('revenue') // 'revenue' | 'units'

  const catList = categories || []
  const totalRev = totalSalesRaw || catList.reduce((acc, c) => acc + (c.revenue || 0), 0)
  const totalUnits = totalUnitsSold || catList.reduce((acc, c) => acc + (c.units_sold || 0), 0)

  // Max value for bar width scaling (relative to leader)
  const maxShare = Math.max(...catList.map(c => metricMode === 'revenue' ? (c.pct_of_total || 0) : (c.pct_of_units || 0)), 1)

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <h3 style={{
            fontSize: '1.08rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Top Selling Categories
          </h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Volume and revenue ranking
          </span>
        </div>

        {/* Metric Switcher Segmented Control */}
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
            Units Sold
          </button>
        </div>
      </div>

      {/* Progress Bars List */}
      {catList.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No category records available.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {catList.map((cat, idx) => {
            const pct = metricMode === 'revenue' 
              ? (cat.pct_of_total || (totalRev > 0 ? ((cat.revenue / totalRev) * 100).toFixed(1) : 0))
              : (cat.pct_of_units || (totalUnits > 0 ? ((cat.units_sold / totalUnits) * 100).toFixed(1) : 0))

            const barWidthPct = Math.min(100, Math.max(12, ((pct / maxShare) * 100)))

            return (
              <div 
                key={cat.category}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '75px 1fr auto auto',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '4px 0'
                }}
              >
                {/* Category Name */}
                <span style={{
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  whiteSpace: 'nowrap'
                }}>
                  {cat.category}
                </span>

                {/* Clean Sleek Progress Bar Track */}
                <div style={{
                  width: '100%',
                  height: '6px',
                  background: '#EAECE8',
                  borderRadius: 'var(--radius-pill)',
                  overflow: 'hidden'
                }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${barWidthPct}%`,
                      background: idx === 0 ? '#064E35' : idx === 1 ? '#0F6B4B' : idx === 2 ? '#2D8A68' : '#5AB892',
                      borderRadius: 'var(--radius-pill)',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>

                {/* Formatted Value */}
                <span style={{
                  fontSize: '0.82rem',
                  fontWeight: 800,
                  fontFamily: 'var(--font-display)',
                  color: 'var(--text-primary)',
                  fontVariantNumeric: 'tabular-nums',
                  minWidth: '70px',
                  textAlign: 'right'
                }}>
                  {metricMode === 'revenue' ? (cat.revenue_formatted || `₹${cat.revenue?.toLocaleString()}`) : `${cat.units_sold?.toLocaleString()} items`}
                </span>

                {/* Percentage Chip */}
                <span style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  color: 'var(--forest-green)',
                  background: 'var(--mint-soft)',
                  border: '1px solid var(--mint-border)',
                  padding: '2px 7px',
                  borderRadius: 'var(--radius-pill)',
                  minWidth: '42px',
                  textAlign: 'center'
                }}>
                  {pct}%
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
