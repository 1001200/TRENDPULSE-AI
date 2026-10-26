import React, { useState } from 'react'
import { Ruler, Sparkles, Info } from 'lucide-react'

export default function SizeHorizontalBarChart({ salesBySize = [], dominantSize, totalUnits = 0 }) {
  const [metricMode, setMetricMode] = useState('units') // 'units' | 'revenue'
  const [hoveredIdx, setHoveredIdx] = useState(null)

  const sizeList = salesBySize || []
  const hasData = sizeList.length > 0 && sizeList.some(s => s.units_sold > 0)

  // Calculate totals if not passed
  const calcTotalUnits = totalUnits || sizeList.reduce((acc, s) => acc + (s.units_sold || 0), 0)
  const calcTotalRev = sizeList.reduce((acc, s) => acc + (s.revenue || 0), 0)

  const maxVal = Math.max(
    ...sizeList.map(s => metricMode === 'units' ? (s.units_sold || 0) : (s.revenue || 0)),
    1
  )

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
              fontSize: '1rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sales by Size
            </h3>
            {dominantSize?.size && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 600,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(6, 78, 53, 0.12)'
              }}>
                Top: Size {dominantSize.size} ({dominantSize.pct_of_sales}%)
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Garment unit volume and revenue share across sizes
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
            type="button"
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
          <button
            type="button"
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
        </div>
      </div>

      {/* Column Headers */}
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
        <span>SIZE LABEL</span>
        <span>{metricMode === 'units' ? 'UNITS (% OF GARMENTS)' : 'REVENUE (% OF TOTAL)'}</span>
      </div>

      {/* Content */}
      {!hasData ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No size sales recorded for the selected period.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', flex: 1, justifyContent: 'center' }}>
          {sizeList.map((sz, idx) => {
            const val = metricMode === 'units' ? sz.units_sold : sz.revenue
            const pct = metricMode === 'units'
              ? (sz.pct_of_sales || (calcTotalUnits > 0 ? ((sz.units_sold / calcTotalUnits) * 100).toFixed(1) : 0))
              : (calcTotalRev > 0 ? ((sz.revenue / calcTotalRev) * 100).toFixed(1) : 0)

            const barWidthPct = Math.min(100, Math.max(8, (val / maxVal) * 100))
            const isDominant = idx === 0
            const isHovered = hoveredIdx === idx

            return (
              <div
                key={sz.size}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.3rem',
                  padding: '4px 6px',
                  borderRadius: 'var(--radius-sm)',
                  background: isHovered ? 'rgba(6, 78, 53, 0.03)' : 'transparent',
                  transition: 'background 0.15s ease'
                }}
              >
                {/* Labels Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      minWidth: '32px',
                      height: '22px',
                      padding: '0 6px',
                      borderRadius: '6px',
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      background: isDominant ? 'var(--forest-green)' : '#EAF3EE',
                      color: isDominant ? '#FFFFFF' : 'var(--forest-dark)',
                      letterSpacing: '0.02em'
                    }}>
                      Size {sz.size}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {metricMode === 'units'
                        ? (sz.revenue_formatted ? `${sz.revenue_formatted} rev` : '')
                        : `${sz.units_sold} units`}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <span style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--forest-green)' }}>
                      {metricMode === 'units' ? `${sz.units_sold} units` : (sz.revenue_formatted || `₹${sz.revenue?.toLocaleString()}`)}
                    </span>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: isDominant ? 'var(--forest-dark)' : 'var(--text-secondary)',
                      background: isDominant ? 'var(--mint-soft)' : '#F3F4F3',
                      padding: '2px 7px',
                      borderRadius: 'var(--radius-pill)',
                      border: isDominant ? '1px solid rgba(6, 78, 53, 0.12)' : '1px solid rgba(0, 0, 0, 0.04)'
                    }}>
                      {pct}%
                    </span>
                  </div>
                </div>

                {/* Progress Bar Container */}
                <div style={{
                  width: '100%',
                  height: '9px',
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
                      background: isDominant
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

          {/* Scale Legend */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.62rem',
            color: 'var(--text-muted)',
            marginTop: '0.2rem',
            paddingTop: '0.25rem',
            borderTop: '1px solid rgba(0, 0, 0, 0.03)'
          }}>
            <span>0%</span>
            <span>25%</span>
            <span>50%</span>
            <span>75%</span>
            <span>100% of top size</span>
          </div>
        </div>
      )}
    </div>
  )
}
