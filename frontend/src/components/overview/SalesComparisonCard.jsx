import React, { useState } from 'react'
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Calendar, ArrowRight } from 'lucide-react'

export default function SalesComparisonCard({ comparisonData }) {
  const [comparisonMode, setComparisonMode] = useState('month') // 'month' | 'week'

  const currentComparison = comparisonMode === 'month' 
    ? comparisonData?.month 
    : comparisonData?.week

  if (!currentComparison) {
    return (
      <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
          Sales Comparison
        </h3>
        <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Insufficient sales history to compute comparison periods.
        </p>
      </div>
    )
  }

  const {
    current_label,
    prior_label,
    current_revenue,
    current_revenue_formatted,
    prior_revenue,
    prior_revenue_formatted,
    diff_revenue,
    diff_revenue_formatted,
    pct_change,
    is_positive,
    current_orders,
    prior_orders,
    current_units,
    prior_units
  } = currentComparison

  // Determine bar widths for visual comparison
  const maxRev = Math.max(current_revenue, prior_revenue, 1)
  const currentBarWidth = Math.round((current_revenue / maxRev) * 100)
  const priorBarWidth = Math.round((prior_revenue / maxRev) * 100)

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      {/* Header with Comparison Toggle */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
            Sales Comparison
          </h3>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Period-over-period business performance
          </span>
        </div>

        {/* View Toggle */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-segment)',
          padding: '3px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid rgba(18, 38, 28, 0.05)'
        }}>
          <button
            onClick={() => setComparisonMode('month')}
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.69rem',
              fontWeight: comparisonMode === 'month' ? 700 : 500,
              color: comparisonMode === 'month' ? '#ffffff' : 'var(--text-secondary)',
              background: comparisonMode === 'month' ? 'var(--forest-green)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              boxShadow: comparisonMode === 'month' ? '0 2px 6px rgba(6, 78, 53, 0.2)' : 'none'
            }}
          >
            Monthly
          </button>
          <button
            onClick={() => setComparisonMode('week')}
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.69rem',
              fontWeight: comparisonMode === 'week' ? 700 : 500,
              color: comparisonMode === 'week' ? '#ffffff' : 'var(--text-secondary)',
              background: comparisonMode === 'week' ? 'var(--forest-green)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              boxShadow: comparisonMode === 'week' ? '0 2px 6px rgba(6, 78, 53, 0.2)' : 'none'
            }}
          >
            Weekly
          </button>
        </div>
      </div>

      {/* Delta Callout Box */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.65rem 0.9rem',
        borderRadius: 'var(--radius-md)',
        background: is_positive ? 'var(--badge-green-bg)' : 'var(--badge-red-bg)',
        border: `1px solid ${is_positive ? 'rgba(5, 138, 62, 0.15)' : 'rgba(217, 45, 32, 0.15)'}`,
        marginBottom: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: is_positive ? 'var(--badge-green-text)' : 'var(--badge-red-text)'
          }}>
            {is_positive ? <ArrowUpRight size={16} strokeWidth={2.5} /> : <ArrowDownRight size={16} strokeWidth={2.5} />}
          </div>
          <div>
            <span style={{ fontSize: '0.68rem', color: is_positive ? 'var(--badge-green-text)' : 'var(--badge-red-text)', fontWeight: 700, display: 'block', textTransform: 'uppercase', letterSpacing: '0.02em' }}>
              {is_positive ? 'Revenue Increase' : 'Revenue Decrease'}
            </span>
            <span style={{ fontSize: '0.95rem', fontWeight: 800, color: is_positive ? 'var(--badge-green-text)' : 'var(--badge-red-text)' }}>
              {diff_revenue_formatted}
            </span>
          </div>
        </div>

        {pct_change !== null && (
          <span style={{
            fontSize: '0.88rem',
            fontWeight: 800,
            padding: '3px 8px',
            borderRadius: 'var(--radius-pill)',
            background: '#ffffff',
            color: is_positive ? 'var(--badge-green-text)' : 'var(--badge-red-text)',
            boxShadow: '0 2px 4px rgba(0,0,0,0.04)'
          }}>
            {is_positive ? `+${pct_change}%` : `${pct_change}%`}
          </span>
        )}
      </div>

      {/* Two Metric Comparison Blocks */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {/* 1. Current Period */}
        <div style={{
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-md)',
          background: '#FAFBF9',
          border: '1px solid rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {current_label} (Current)
            </span>
            <span style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--forest-green)', fontFamily: 'var(--font-display)' }}>
              {current_revenue_formatted}
            </span>
          </div>

          {/* Progress comparison track */}
          <div style={{
            width: '100%',
            height: '7px',
            background: '#EBF4F0',
            borderRadius: 'var(--radius-pill)',
            overflow: 'hidden',
            marginBottom: '0.35rem'
          }}>
            <div style={{
              height: '100%',
              width: `${currentBarWidth}%`,
              background: 'var(--forest-green)',
              borderRadius: 'var(--radius-pill)',
              transition: 'width 0.4s ease'
            }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.67rem', color: 'var(--text-muted)' }}>
            <span>Orders: {current_orders}</span>
            <span>Units Sold: {current_units}</span>
          </div>
        </div>

        {/* 2. Prior Period */}
        <div style={{
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-md)',
          background: '#FAFBF9',
          border: '1px solid rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {prior_label} (Previous)
            </span>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'var(--font-display)' }}>
              {prior_revenue_formatted}
            </span>
          </div>

          {/* Progress comparison track */}
          <div style={{
            width: '100%',
            height: '7px',
            background: '#EBF4F0',
            borderRadius: 'var(--radius-pill)',
            overflow: 'hidden',
            marginBottom: '0.35rem'
          }}>
            <div style={{
              height: '100%',
              width: `${priorBarWidth}%`,
              background: '#8A948E',
              borderRadius: 'var(--radius-pill)',
              transition: 'width 0.4s ease'
            }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.67rem', color: 'var(--text-muted)' }}>
            <span>Orders: {prior_orders}</span>
            <span>Units Sold: {prior_units}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
