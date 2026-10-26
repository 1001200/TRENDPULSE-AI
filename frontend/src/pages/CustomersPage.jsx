import React, { useState, useEffect } from 'react'
import PageHeader from '../components/common/PageHeader'
import {
  Users,
  Repeat,
  CreditCard,
  ShoppingBag,
  TrendingUp,
  Info,
  Calendar,
  UserCheck,
  UserPlus,
  ArrowUpRight
} from 'lucide-react'
import { getInsights, getIngestionStats } from '../services/api'
import DonutChart from '../components/common/DonutChart'

export default function CustomersPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('all')

  const fetchData = async (p = period) => {
    setLoading(true)
    try {
      const statsRes = await getIngestionStats()
      if (statsRes.ok && statsRes.data.has_data) {
        const insightsRes = await getInsights({ period: p })
        if (insightsRes.ok && insightsRes.data.has_data) {
          setData(insightsRes.data)
        }
      }
    } catch (err) {
      console.error('Failed to fetch customers data:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData(period)
  }, [period])

  const periodOptions = [
    { id: 'all', label: 'All Time' },
    { id: 'this_month', label: 'This Month' },
    { id: 'last_month', label: 'Last Month' },
    { id: '3m', label: 'Last 3 Months' },
    { id: '6m', label: 'Last 6 Months' },
  ]

  const activePeriodObj = periodOptions.find(p => p.id === period) || periodOptions[0]

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <PageHeader
          title="Customers"
          subtitle="Understand repeat purchases, customer spending, and buying patterns."
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(215px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: '130px', borderRadius: 'var(--radius-xl)' }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: '320px', borderRadius: 'var(--radius-xl)' }} />
      </div>
    )
  }

  const customers = data?.customers

  if (!customers || !customers.available) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <PageHeader
          title="Customers"
          subtitle="Understand repeat purchases, customer spending, and buying patterns."
        />
        <div className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
          <div style={{
            margin: '0 auto 1.25rem',
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'var(--mint-soft)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Users size={28} color="var(--forest-green)" />
          </div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            No customer handle or buyer data identified
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Customer analytics require customer handles, phone numbers, or account IDs in your uploaded spreadsheet.
            Upload your order records with a Buyer Handle column to unlock repeat buyer analytics.
          </p>
        </div>
      </div>
    )
  }

  const returningCount = customers.returning_customers || 0
  const newCount = customers.new_customers || 0
  const uniqueCount = Math.max(1, customers.unique_customers || 1)
  const returningPct = customers.returning_pct !== undefined
    ? customers.returning_pct
    : Math.round((returningCount / uniqueCount) * 100)
  const newPct = customers.new_pct !== undefined
    ? customers.new_pct
    : Math.max(0, 100 - returningPct)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* 1. Page Header with Clean Subtitle & Period Selector */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.85rem'
      }}>
        <div>
          <h1 style={{
            fontSize: '1.4rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Customers
          </h1>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.15rem', display: 'block' }}>
            Understand repeat purchases, customer spending, and buying patterns.
          </span>
        </div>

        {/* Polished Segmented Period Filter Bar */}
        <div style={{
          display: 'inline-flex',
          background: 'var(--bg-segment)',
          padding: '3px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid rgba(18, 38, 28, 0.05)'
        }}>
          {periodOptions.map(p => {
            const isSelected = period === p.id
            return (
              <button
                key={p.id}
                onClick={() => setPeriod(p.id)}
                style={{
                  padding: '5px 13px',
                  borderRadius: 'var(--radius-pill)',
                  fontSize: '0.72rem',
                  fontWeight: isSelected ? 700 : 500,
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  background: isSelected ? 'var(--forest-green)' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  boxShadow: isSelected ? '0 2px 6px rgba(6, 78, 53, 0.2)' : 'none'
                }}
              >
                {p.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* 2. Redesigned 4-Card Responsive KPI Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(215px, 1fr))',
        gap: '1rem'
      }}>
        {/* KPI 1: Unique Buyers */}
        <div className="kpi-card-ref white" style={{ padding: '1.25rem 1.4rem' }}>
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              <Users size={18} strokeWidth={2.2} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              {period === 'all' ? 'All Time' : activePeriodObj.label}
            </span>
          </div>
          <div>
            <span className="kpi-label">Unique Buyers</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{customers.unique_customers}</span>
              <span className="kpi-subtext" style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {period === 'all'
                  ? 'Distinct buyers in recorded history'
                  : `Active in period (${customers.all_time_unique_customers || customers.unique_customers} historical total)`
                }
              </span>
            </div>
          </div>
        </div>

        {/* KPI 2: Repeat Purchase Rate */}
        <div className="kpi-card-ref white" style={{ padding: '1.25rem 1.4rem' }}>
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              <Repeat size={18} strokeWidth={2.2} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              2+ Orders
            </span>
          </div>
          <div>
            <span className="kpi-label">Repeat Purchase Rate</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value" style={{ color: 'var(--forest-green)' }}>
                {customers.repeat_purchase_rate}%
              </span>
              <span className="kpi-subtext" style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {customers.returning_customers} of {customers.unique_customers} buyers placed 2+ orders
              </span>
            </div>
          </div>
        </div>

        {/* KPI 3: Average Customer Spend */}
        <div className="kpi-card-ref white" style={{ padding: '1.25rem 1.4rem' }}>
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              <CreditCard size={18} strokeWidth={2.2} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              Spend Avg
            </span>
          </div>
          <div>
            <span className="kpi-label">
              {period === 'all' ? 'Lifetime Avg Customer Spend' : 'Period Avg Customer Spend'}
            </span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{customers.avg_customer_spend_formatted}</span>
              <span className="kpi-subtext" style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {period === 'all'
                  ? 'Average total spend per buyer across all history'
                  : `In ${activePeriodObj.label} (${customers.avg_customer_spend_lifetime_formatted || customers.avg_customer_spend_formatted} lifetime avg)`
                }
              </span>
            </div>
          </div>
        </div>

        {/* KPI 4: Items Per Order */}
        <div className="kpi-card-ref white" style={{ padding: '1.25rem 1.4rem' }}>
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              <ShoppingBag size={18} strokeWidth={2.2} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              Basket Size
            </span>
          </div>
          <div>
            <span className="kpi-label">Items Per Order</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{customers.avg_items_per_order}</span>
              <span className="kpi-subtext" style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Qualifying clothing units per checkout
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Data-Backed Customer Insight (Replaces unsupported heuristic) */}
      {customers.key_insight && (
        <div style={{
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
          background: 'var(--mint-soft)',
          border: '1px solid rgba(6, 78, 53, 0.15)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <Info size={18} color="var(--forest-green)" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '0.84rem', color: 'var(--forest-dark)', lineHeight: 1.4 }}>
            <strong>Observed Customer Insight:</strong> {customers.key_insight}
          </span>
        </div>
      )}

      {/* 4. Buyer Composition & Top Repeat Buyers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        gap: '1.25rem',
        alignItems: 'start'
      }}>
        {/* Left: Buyer Composition Donut Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <DonutChart
            title="Buyer Composition"
            subtitle="New vs returning customer share"
            data={[
              {
                label: 'New Buyers',
                value: newCount,
                formattedValue: `${newCount.toLocaleString()} buyers`,
                percentage: newPct,
                sublabel: 'First recorded order'
              },
              {
                label: 'Returning Buyers',
                value: returningCount,
                formattedValue: `${returningCount.toLocaleString()} buyers`,
                percentage: returningPct,
                sublabel: '2+ qualifying orders'
              }
            ]}
            centerPrimary={`${uniqueCount.toLocaleString()}`}
            centerSecondary="Total Buyers"
            colors={['#064E35', '#CADCD2']}
          />

          {/* Basis of Calculation Note */}
          <div style={{
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            lineHeight: 1.4,
            padding: '0.65rem 0.85rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            background: '#ffffff'
          }}>
            <strong>Scope definition:</strong> Returning buyers made 2 or more qualifying purchases within the recorded period. New buyers have a single recorded purchase. Based on available recorded sales history.
          </div>
        </div>

        {/* Right: Top Repeat Buyers Ranked Table */}
        <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
                Top Repeat Buyers
              </h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Ranked by verified order frequency
              </span>
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              {customers.top_buyers?.length || 0} Identified
            </span>
          </div>

          {customers.top_buyers?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
              {customers.top_buyers.map((b, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    background: idx < 3 ? 'var(--mint-soft)' : 'var(--bg-canvas)',
                    border: '1px solid var(--border-subtle)',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  {/* Left: Rank, Avatar & Handle */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: idx < 3 ? 'var(--forest-green)' : 'var(--text-muted)',
                      width: '16px'
                    }}>
                      #{idx + 1}
                    </span>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: idx < 3 ? 'var(--forest-green)' : '#CADCD2',
                      color: idx < 3 ? '#ffffff' : 'var(--forest-dark)',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      {b.handle.replace('@', '').substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div style={{
                        fontSize: '0.84rem',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-sans)',
                        letterSpacing: '-0.01em'
                      }}>
                        {b.handle}
                      </div>
                      <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
                        First order: {b.first_order_date || 'Historical record'}
                      </span>
                    </div>
                  </div>

                  {/* Right: Order Count & Spend */}
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', justifyContent: 'flex-end' }}>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--forest-green)',
                        background: 'rgba(6, 78, 53, 0.1)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-pill)'
                      }}>
                        {b.orders_count} orders
                      </span>
                    </div>
                    <div style={{
                      fontSize: '0.82rem',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      marginTop: '0.15rem'
                    }}>
                      {b.total_spend_formatted}
                      {period !== 'all' && b.lifetime_spend_formatted && (
                        <span style={{ fontSize: '0.68rem', fontWeight: 500, color: 'var(--text-muted)', display: 'block' }}>
                          ({b.lifetime_spend_formatted} lifetime)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              No repeat buyers identified in this period.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
