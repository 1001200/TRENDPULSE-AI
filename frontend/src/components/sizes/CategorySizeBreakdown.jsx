import React from 'react'
import { Layers, Sparkles } from 'lucide-react'

export default function CategorySizeBreakdown({ categoryXSize = [], catSizeInsight }) {
  const catList = categoryXSize || []
  const hasData = catList.length > 0 && catList.some(c => c.total_units > 0)

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem'
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
              Category × Size Breakdown
            </h3>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              color: 'var(--forest-green)',
              background: 'var(--mint-soft)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid rgba(6, 78, 53, 0.12)'
            }}>
              {catList.length} Categories
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Size distribution and dominant garment size across clothing categories
          </span>
        </div>

        {/* Legend */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.68rem',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: 'var(--forest-green)' }} />
            <span>Dominant Size</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: 'var(--forest-muted)' }} />
            <span>Secondary Size</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: 'var(--mint-light)' }} />
            <span>Other Sizes</span>
          </div>
        </div>
      </div>

      {/* Insight Callout if present */}
      {catSizeInsight && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.55rem 0.85rem',
          borderRadius: 'var(--radius-md)',
          background: 'var(--mint-soft)',
          border: '1px solid rgba(6, 78, 53, 0.1)',
          marginBottom: '1.1rem',
          fontSize: '0.75rem',
          color: 'var(--forest-dark)'
        }}>
          <Sparkles size={14} color="var(--forest-green)" style={{ flexShrink: 0 }} />
          <span>{catSizeInsight}</span>
        </div>
      )}

      {/* Category Grid */}
      {!hasData ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No category size data available for the selected period.
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))',
          gap: '1rem'
        }}>
          {catList.map((item, idx) => {
            const totalUnits = item.total_units || 1
            const breakdown = item.breakdown || []

            return (
              <div
                key={item.category}
                style={{
                  padding: '1rem 1.15rem',
                  borderRadius: 'var(--radius-lg)',
                  background: '#FAFAFA',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'transform var(--transition-fast), box-shadow var(--transition-fast)'
                }}
              >
                {/* Category Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <span style={{
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      fontFamily: 'var(--font-display)'
                    }}>
                      {item.category}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      ({item.total_units} units)
                    </span>
                  </div>

                  {item.dominant_size && item.dominant_size !== 'N/A' && (
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--forest-green)',
                      background: 'var(--mint-soft)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-pill)',
                      border: '1px solid rgba(6, 78, 53, 0.15)'
                    }}>
                      Top: Size {item.dominant_size} ({item.dominant_size_pct}%)
                    </span>
                  )}
                </div>

                {/* Size Distribution Bars */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {breakdown.map((b, bIdx) => {
                    const isDominant = b.size === item.dominant_size
                    const pctOfCat = b.pct !== undefined ? b.pct : Math.round((b.units / totalUnits) * 100)

                    return (
                      <div key={b.size} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              minWidth: '24px',
                              height: '18px',
                              padding: '0 4px',
                              borderRadius: '4px',
                              fontSize: '0.68rem',
                              fontWeight: 700,
                              background: isDominant ? 'var(--forest-green)' : '#E8EBE9',
                              color: isDominant ? '#FFFFFF' : 'var(--text-primary)'
                            }}>
                              {b.size}
                            </span>
                            <span style={{ color: 'var(--text-secondary)' }}>
                              {b.units} {b.units === 1 ? 'unit' : 'units'} sold
                            </span>
                          </div>
                          <span style={{
                            fontWeight: 700,
                            color: isDominant ? 'var(--forest-green)' : 'var(--text-secondary)'
                          }}>
                            {pctOfCat}%
                          </span>
                        </div>

                        {/* Bar */}
                        <div style={{
                          width: '100%',
                          height: '6px',
                          background: '#EAECE9',
                          borderRadius: 'var(--radius-pill)',
                          overflow: 'hidden'
                        }}>
                          <div
                            style={{
                              height: '100%',
                              width: `${pctOfCat}%`,
                              background: isDominant
                                ? 'var(--forest-green)'
                                : bIdx === 1
                                ? 'var(--forest-muted)'
                                : 'var(--mint-light)',
                              borderRadius: 'var(--radius-pill)',
                              transition: 'width 0.3s ease'
                            }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
