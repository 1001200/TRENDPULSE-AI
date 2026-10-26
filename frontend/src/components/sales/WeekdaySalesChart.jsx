import React, { useState } from 'react'
import { Calendar, TrendingUp } from 'lucide-react'

export default function WeekdaySalesChart({ salesByDay = [], insightText }) {
  const [hoveredDay, setHoveredDay] = useState(null)

  // Ensure standard Monday - Sunday order
  const standardDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  
  // Map incoming data or provide zeros if missing
  const dayMap = {}
  salesByDay.forEach(d => {
    dayMap[d.day] = d
  })

  const daysData = standardDays.map(dayName => {
    return dayMap[dayName] || {
      day: dayName,
      total_revenue: 0,
      total_revenue_formatted: '₹0',
      avg_revenue: 0,
      avg_revenue_formatted: '₹0',
      orders: 0,
      units: 0
    }
  })

  const maxRevenue = Math.max(...daysData.map(d => d.total_revenue), 1)
  const peakDayObj = daysData.reduce((prev, curr) => (curr.total_revenue > prev.total_revenue ? curr : prev), daysData[0])

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', position: 'relative' }}>
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem'
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
              Sales by Day of Week
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
            Weekday revenue distribution (Monday through Sunday)
          </span>
        </div>
      </div>

      {/* Horizontal Bar Chart List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {daysData.map((item) => {
          const isPeak = item.day === peakDayObj.day && item.total_revenue > 0
          const hasSales = item.total_revenue > 0
          const barWidthPct = hasSales ? Math.max((item.total_revenue / maxRevenue) * 100, 4) : 0
          const isHovered = hoveredDay === item.day

          return (
            <div
              key={item.day}
              onMouseEnter={() => setHoveredDay(item.day)}
              onMouseLeave={() => setHoveredDay(null)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                padding: '4px 6px',
                borderRadius: 'var(--radius-md)',
                background: isHovered ? '#FAFBF9' : 'transparent',
                transition: 'background 0.15s ease'
              }}
            >
              {/* Day Label */}
              <div style={{ width: '85px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{
                  fontSize: '0.78rem',
                  fontWeight: isPeak ? 700 : 600,
                  color: isPeak ? 'var(--forest-green)' : hasSales ? 'var(--text-primary)' : 'var(--text-muted)'
                }}>
                  {item.day}
                </span>
                {(item.day === 'Saturday' || item.day === 'Sunday') && (
                  <span style={{
                    width: '5px',
                    height: '5px',
                    borderRadius: '50%',
                    background: isPeak ? 'var(--forest-green)' : 'var(--mint-light)',
                    display: 'inline-block'
                  }} title="Weekend drop" />
                )}
              </div>

              {/* Bar Track & Fill */}
              <div style={{
                flex: 1,
                height: '18px',
                background: '#F3F4F3',
                borderRadius: 'var(--radius-pill)',
                overflow: 'hidden',
                position: 'relative'
              }}>
                {hasSales && (
                  <div
                    style={{
                      height: '100%',
                      width: `${barWidthPct}%`,
                      borderRadius: 'var(--radius-pill)',
                      background: isPeak
                        ? 'linear-gradient(90deg, var(--forest-green), #0A6B4A)'
                        : 'linear-gradient(90deg, #115E43, #2E7D5C)',
                      boxShadow: isPeak ? '0 2px 6px rgba(6, 78, 53, 0.25)' : 'none',
                      transition: 'width 0.4s ease'
                    }}
                  />
                )}
              </div>

              {/* Value and Orders Badge */}
              <div style={{
                width: '135px',
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '0.5rem'
              }}>
                <span style={{
                  fontSize: '0.82rem',
                  fontWeight: hasSales ? 700 : 500,
                  fontFamily: 'var(--font-display)',
                  color: isPeak ? 'var(--forest-green)' : hasSales ? 'var(--text-primary)' : 'var(--text-muted)'
                }}>
                  {item.total_revenue_formatted}
                </span>

                <span style={{
                  fontSize: '0.66rem',
                  fontWeight: 600,
                  color: hasSales ? 'var(--forest-green)' : 'var(--text-muted)',
                  background: hasSales ? 'var(--mint-soft)' : '#F1F2F0',
                  padding: '2px 7px',
                  borderRadius: 'var(--radius-pill)',
                  whiteSpace: 'nowrap'
                }}>
                  {item.orders} {item.orders === 1 ? 'order' : 'orders'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
