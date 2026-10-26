import React, { useState } from 'react'

/**
 * CategoryTreemapChart — Clean squarified treemap showing apparel category revenue distribution
 * Matches Reference Image #5
 */
export default function CategoryTreemapChart({ categories = [], totalRevenueRaw }) {
  const [hoveredCat, setHoveredCat] = useState(null)

  const catList = categories || []
  const totalRev = totalRevenueRaw || catList.reduce((acc, c) => acc + (c.revenue || 0), 0)

  // Curated editorial green shades (Deep Forest to Soft Mint)
  const colors = [
    { bg: '#064E35', text: '#FFFFFF', sub: 'rgba(255, 255, 255, 0.75)' }, // Deep Forest
    { bg: '#0F6B4B', text: '#FFFFFF', sub: 'rgba(255, 255, 255, 0.75)' }, // Rich Forest
    { bg: '#2D8A68', text: '#FFFFFF', sub: 'rgba(255, 255, 255, 0.75)' }, // Medium Forest
    { bg: '#5AB892', text: '#FFFFFF', sub: 'rgba(255, 255, 255, 0.85)' }, // Sage Mint
    { bg: '#CADCD2', text: '#053D2A', sub: 'rgba(5, 61, 42, 0.75)' },     // Soft Mint
  ]

  // Clean data sorted by revenue descending
  const sorted = [...catList].sort((a, b) => (b.revenue || 0) - (a.revenue || 0))

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <h3 style={{
            fontSize: '1.08rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Category Revenue Distribution
          </h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Proportional revenue volume across apparel categories
          </span>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          No category distribution data available.
        </div>
      ) : (
        /* Sized Treemap Layout Grid */
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.15fr 1fr',
          gap: '8px',
          height: '240px',
          width: '100%'
        }}>
          {/* Left Block: Largest Category (Bottoms) */}
          {sorted[0] && (() => {
            const c = sorted[0]
            const color = colors[0]
            const isHovered = hoveredCat === c.category
            return (
              <div
                key={c.category}
                onMouseEnter={() => setHoveredCat(c.category)}
                onMouseLeave={() => setHoveredCat(null)}
                style={{
                  background: color.bg,
                  color: color.text,
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.15rem 1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  transition: 'transform 0.18s ease, box-shadow 0.18s ease',
                  transform: isHovered ? 'scale(1.015)' : 'none',
                  boxShadow: isHovered ? '0 8px 20px rgba(6, 78, 53, 0.25)' : 'none',
                  border: '1px solid rgba(255, 255, 255, 0.12)'
                }}
              >
                <div>
                  <span style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-display)', display: 'block' }}>
                    {c.category}
                  </span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginTop: '4px', display: 'block' }}>
                    {c.revenue_formatted || `₹${c.revenue?.toLocaleString()}`}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, opacity: 0.9 }}>
                    {c.pct_of_total}%
                  </span>
                  <span style={{ fontSize: '0.68rem', color: color.sub }}>
                    {c.units_sold?.toLocaleString()} units
                  </span>
                </div>
              </div>
            )
          })()}

          {/* Right Column: Tops (top half) + Sub-row of remaining categories */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', height: '100%' }}>
            {/* Tops (Second Largest) */}
            {sorted[1] && (() => {
              const c = sorted[1]
              const color = colors[1]
              const isHovered = hoveredCat === c.category
              return (
                <div
                  key={c.category}
                  onMouseEnter={() => setHoveredCat(c.category)}
                  onMouseLeave={() => setHoveredCat(null)}
                  style={{
                    flex: '1.1',
                    background: color.bg,
                    color: color.text,
                    borderRadius: 'var(--radius-lg)',
                    padding: '0.9rem 1.1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'transform 0.18s ease, box-shadow 0.18s ease',
                    transform: isHovered ? 'scale(1.015)' : 'none',
                    boxShadow: isHovered ? '0 6px 16px rgba(6, 78, 53, 0.2)' : 'none',
                    border: '1px solid rgba(255, 255, 255, 0.12)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '0.95rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
                      {c.category}
                    </span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, opacity: 0.9 }}>
                      {c.pct_of_total}%
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
                      {c.revenue_formatted || `₹${c.revenue?.toLocaleString()}`}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: color.sub }}>
                      {c.units_sold?.toLocaleString()} units
                    </span>
                  </div>
                </div>
              )
            })()}

            {/* Bottom Sub-grid for Outerwear, Dresses, Knitwear */}
            <div style={{
              flex: '1',
              display: 'grid',
              gridTemplateColumns: `repeat(${Math.max(1, sorted.slice(2).length)}, 1fr)`,
              gap: '8px'
            }}>
              {sorted.slice(2).map((c, i) => {
                const color = colors[2 + i] || colors[colors.length - 1]
                const isHovered = hoveredCat === c.category
                return (
                  <div
                    key={c.category}
                    onMouseEnter={() => setHoveredCat(c.category)}
                    onMouseLeave={() => setHoveredCat(null)}
                    style={{
                      background: color.bg,
                      color: color.text,
                      borderRadius: 'var(--radius-md)',
                      padding: '0.65rem 0.75rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'transform 0.18s ease',
                      transform: isHovered ? 'scale(1.025)' : 'none',
                      boxShadow: isHovered ? '0 4px 12px rgba(0, 0, 0, 0.15)' : 'none',
                      minWidth: 0,
                      overflow: 'hidden'
                    }}
                    title={`${c.category}: ${c.revenue_formatted} (${c.pct_of_total}%) • ${c.units_sold} units`}
                  >
                    <span style={{
                      fontSize: '0.78rem',
                      fontWeight: 800,
                      fontFamily: 'var(--font-display)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {c.category}
                    </span>
                    <span style={{
                      fontSize: '0.85rem',
                      fontWeight: 800,
                      fontFamily: 'var(--font-display)',
                      fontVariantNumeric: 'tabular-nums',
                      lineHeight: 1.15
                    }}>
                      {c.revenue_formatted}
                    </span>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: color.sub }}>
                      {c.pct_of_total}%
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
