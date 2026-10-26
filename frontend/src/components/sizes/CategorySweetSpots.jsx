import React from 'react'
import { Tag, DollarSign, TrendingUp, Sparkles, CheckCircle2 } from 'lucide-react'

export default function CategorySweetSpots({ categoryXPrice = [] }) {
  const catList = categoryXPrice || []
  const hasData = catList.length > 0 && catList.some(c => c.has_data)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Section Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem'
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
              Category Price Sweet Spots
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
              Optimal Price Tiers
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Highest-revenue price bands and average price points by clothing category
          </span>
        </div>
      </div>

      {/* Cards Grid */}
      {!hasData ? (
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No category price sweet spot data available for the selected period.
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1rem'
        }}>
          {catList.map(cp => {
            const hasCatData = cp.has_data && cp.units_sold > 0

            return (
              <div
                key={cp.category}
                className="card"
                style={{
                  padding: '1.25rem 1.3rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {/* Top Row: Category Name & Average Price Tag */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <span style={{
                      fontSize: '0.92rem',
                      fontWeight: 800,
                      fontFamily: 'var(--font-display)',
                      color: 'var(--text-primary)'
                    }}>
                      {cp.category}
                    </span>
                  </div>

                  {hasCatData ? (
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: 'var(--forest-green)',
                      background: 'var(--mint-soft)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-pill)',
                      border: '1px solid rgba(6, 78, 53, 0.12)'
                    }}>
                      Avg: {cp.avg_price_formatted}
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      No sales
                    </span>
                  )}
                </div>

                {/* Sweet Spot Highlight Box */}
                {hasCatData ? (
                  <>
                    <div style={{
                      padding: '0.75rem 0.85rem',
                      borderRadius: 'var(--radius-md)',
                      background: 'linear-gradient(135deg, rgba(6, 78, 53, 0.05) 0%, rgba(202, 220, 210, 0.25) 100%)',
                      border: '1px solid rgba(6, 78, 53, 0.1)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.66rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Primary Sweet Spot
                        </span>
                        <span style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          color: 'var(--forest-dark)',
                          background: 'rgba(255, 255, 255, 0.8)',
                          padding: '1px 6px',
                          borderRadius: '4px'
                        }}>
                          {cp.rev_pct}% of rev
                        </span>
                      </div>
                      <div style={{
                        fontSize: '1.05rem',
                        fontWeight: 800,
                        color: 'var(--forest-green)',
                        fontFamily: 'var(--font-display)'
                      }}>
                        {cp.sweet_spot_bracket}
                      </div>
                    </div>

                    {/* Key Stats Row */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '0.6rem',
                      fontSize: '0.72rem',
                      paddingTop: '0.2rem'
                    }}>
                      <div>
                        <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.66rem' }}>Revenue in Tier</span>
                        <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.82rem' }}>
                          {cp.revenue_formatted}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.66rem' }}>Volume Sold</span>
                        <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.82rem' }}>
                          {cp.units_sold} {cp.units_sold === 1 ? 'unit' : 'units'}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar showing share of category revenue */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <div style={{
                        width: '100%',
                        height: '5px',
                        background: '#EAF3EE',
                        borderRadius: 'var(--radius-pill)',
                        overflow: 'hidden'
                      }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${Math.min(100, cp.rev_pct)}%`,
                            background: 'var(--forest-green)',
                            borderRadius: 'var(--radius-pill)'
                          }}
                        />
                      </div>
                    </div>

                    {/* Finding summary text */}
                    <p style={{
                      fontSize: '0.72rem',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.4,
                      margin: 0
                    }}>
                      {cp.finding}
                    </p>
                  </>
                ) : (
                  <div style={{
                    padding: '1.25rem 0.5rem',
                    textAlign: 'center',
                    color: 'var(--text-muted)',
                    fontSize: '0.74rem'
                  }}>
                    Insufficient sales data in this period.
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
