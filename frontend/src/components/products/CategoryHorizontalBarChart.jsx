import React, { useState } from 'react'

export default function CategoryHorizontalBarChart({ categories, totalSalesRaw, totalUnitsSold, selectedCategory }) {
  const [metricMode, setMetricMode] = useState('revenue') // 'revenue' | 'units'

  const catList = categories || []
  const isSingleCatSelected = selectedCategory && selectedCategory !== 'All'

  // Safe totals
  const totalRev = totalSalesRaw || catList.reduce((acc, c) => acc + (c.revenue || 0), 0)
  const totalUnits = totalUnitsSold || catList.reduce((acc, c) => acc + (c.units_sold || 0), 0)

  // Max value for bar width scaling
  const maxShare = Math.max(
    ...catList.map(c => metricMode === 'revenue' ? (c.pct_of_total || 0) : (c.pct_of_units || 0)),
    1
  )

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem',
        marginBottom: '0.85rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sales by Clothing Category
            </h3>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              color: 'var(--forest-green)',
              background: 'var(--mint-soft)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid rgba(6, 78, 53, 0.1)'
            }}>
              {catList.length} {catList.length === 1 ? 'category' : 'categories'}
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            {isSingleCatSelected
              ? `Filtered view for ${selectedCategory}`
              : 'Apparel category revenue and unit volume breakdown'}
          </span>
        </div>

        {/* Metric Switcher Segmented Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-segment)',
          padding: '3px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid rgba(18, 38, 28, 0.05)'
        }}>
          <button
            onClick={() => setMetricMode('revenue')}
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.68rem',
              fontWeight: metricMode === 'revenue' ? 700 : 500,
              color: metricMode === 'revenue' ? '#ffffff' : 'var(--text-secondary)',
              background: metricMode === 'revenue' ? 'var(--forest-green)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            By Revenue (₹)
          </button>
          <button
            onClick={() => setMetricMode('units')}
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.68rem',
              fontWeight: metricMode === 'units' ? 700 : 500,
              color: metricMode === 'units' ? '#ffffff' : 'var(--text-secondary)',
              background: metricMode === 'units' ? 'var(--forest-green)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            By Units
          </button>
        </div>
      </div>

      {/* Grid scale legend / column header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.66rem',
        color: 'var(--text-muted)',
        fontWeight: 600,
        marginBottom: '0.75rem',
        paddingBottom: '0.35rem',
        borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
        letterSpacing: '0.02em'
      }}>
        <span>CLOTHING CATEGORY</span>
        <span>{metricMode === 'revenue' ? 'REVENUE (% OF TOTAL)' : 'UNITS (% OF TOTAL)'}</span>
      </div>

      {/* Content */}
      {catList.length === 0 ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No category sales recorded for the selected filter.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem', position: 'relative' }}>
          {catList.map((cat, idx) => {
            const pct = metricMode === 'revenue'
              ? (cat.pct_of_total || (totalRev > 0 ? ((cat.revenue / totalRev) * 100).toFixed(1) : 0))
              : (cat.pct_of_units || (totalUnits > 0 ? ((cat.units_sold / totalUnits) * 100).toFixed(1) : 0))

            // Progress bar width scaled relative to leader
            const barWidthPct = Math.min(100, Math.max(10, ((pct / maxShare) * 100)))

            return (
              <div
                key={idx}
                title={`${cat.category}: ${cat.revenue_formatted || `₹${cat.revenue}`} (${cat.pct_of_total}% revenue) • ${cat.units_sold} units sold (${cat.pct_of_units || 0}% volume)`}
                style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}
              >
                {/* Labels row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {cat.category}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {metricMode === 'revenue' ? `(${cat.units_sold} items)` : `(${cat.revenue_formatted})`}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <span style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--forest-green)' }}>
                      {metricMode === 'revenue' ? (cat.revenue_formatted || `₹${cat.revenue?.toLocaleString()}`) : `${cat.units_sold} units`}
                    </span>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--forest-dark)',
                      background: 'var(--mint-soft)',
                      padding: '2px 7px',
                      borderRadius: 'var(--radius-pill)',
                      border: '1px solid rgba(6, 78, 53, 0.1)'
                    }}>
                      {pct}%
                    </span>
                  </div>
                </div>

                {/* Horizontal Progress Bar with Subtle Grid Background */}
                <div style={{
                  width: '100%',
                  height: '10px',
                  background: '#EAF3EE',
                  borderRadius: 'var(--radius-pill)',
                  overflow: 'hidden',
                  position: 'relative'
                }}>
                  {/* Subtle 25%, 50%, 75% tick marks */}
                  <div style={{ position: 'absolute', left: '25%', top: 0, bottom: 0, width: '1px', background: 'rgba(6, 78, 53, 0.08)' }} />
                  <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', background: 'rgba(6, 78, 53, 0.08)' }} />
                  <div style={{ position: 'absolute', left: '75%', top: 0, bottom: 0, width: '1px', background: 'rgba(6, 78, 53, 0.08)' }} />

                  {/* Filled bar */}
                  <div
                    style={{
                      height: '100%',
                      width: `${barWidthPct}%`,
                      background: idx === 0
                        ? 'linear-gradient(90deg, #064E35 0%, #115E43 100%)'
                        : idx === 1
                        ? 'linear-gradient(90deg, #0F6B4B 0%, #1A7F5B 100%)'
                        : idx === 2
                        ? 'linear-gradient(90deg, #1A7F5B 0%, #2A9D74 100%)'
                        : 'linear-gradient(90deg, #2A9D74 0%, #52B788 100%)',
                      borderRadius: 'var(--radius-pill)',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
              </div>
            )
          })}

          {/* Subtle gridline labels at bottom */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.62rem',
            color: 'var(--text-muted)',
            marginTop: '0.35rem',
            paddingTop: '0.25rem',
            borderTop: '1px solid rgba(0, 0, 0, 0.03)'
          }}>
            <span>0%</span>
            <span>25%</span>
            <span>50%</span>
            <span>75%</span>
            <span>100% of leader</span>
          </div>
        </div>
      )}
    </div>
  )
}
