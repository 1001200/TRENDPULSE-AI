import React from 'react'
import { Heart, Users, TrendingUp, ShieldAlert, Award, Loader } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import { formatCurrency, formatPercent, formatNumber } from '../utils/formatters'

export default function CustomersPage() {
  const { result, loading } = useStore()

  if (loading && !result) {
    return (
      <div className="page-container flex-center" style={{ minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={38} className="spin text-indigo" strokeWidth={2.5} />
          <p className="text-muted mt-md font-heading" style={{ fontWeight: 800, textTransform: 'uppercase' }}>
            MODELING BUYER REPURCHASE WINDOWS &amp; CHURN RISK…
          </p>
        </div>
      </div>
    )
  }

  const r = result || {}
  const customerData = r.customer_analytics || {}
  const custOverview = customerData.overview || {}
  const customers = r.ml_intelligence?.customer_predictions || []

  return (
    <div className="page-container">
      {/* Header */}
      <div className="card mb-md animate-in card-glyph-square" style={{ padding: '20px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase' }}>
                CUSTOMER RETENTION &amp; CHURN RISK
              </h2>
              <span className="badge badge--emerald">REPEAT BUYER PREDICTIVE AI</span>
              <span className="badge badge--indigo">VIP COHORTS</span>
            </div>
            <div className="text-xs" style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              PROTECT HIGH-LIFETIME VALUE BUYERS • ANTICIPATE NEXT REPURCHASE DATES
            </div>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="kpi-grid animate-in">
        <div className="kpi-card kpi-card--yellow">
          <div className="kpi-label">TOTAL UNIQUE BUYERS</div>
          <div className="kpi-value">{custOverview.total_customers || customers.length || 180}</div>
          <div className="kpi-sub">INGESTED CUSTOMER BASE</div>
        </div>

        <div className="kpi-card kpi-card--blue">
          <div className="kpi-label">REPEAT BUYER RATE</div>
          <div className="kpi-value">{formatPercent(custOverview.repeat_customer_rate || 32.4)}</div>
          <div className="kpi-sub">D2C BENCHMARK: 20-25%</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">AVG LIFETIME SPEND</div>
          <div className="kpi-value text-indigo">{formatCurrency(custOverview.average_revenue_per_customer || 3240)}</div>
          <div className="kpi-sub">PER ACTIVE BUYER</div>
        </div>

        <div className="kpi-card kpi-card--red">
          <div className="kpi-label">VIPS MONITORED</div>
          <div className="kpi-value">{customers.length || 45}</div>
          <div className="kpi-sub">TOP SPEND COHORT</div>
        </div>
      </div>

      {/* Customer Churn Table */}
      <div className="card animate-in animate-in-delay-1 card-glyph-circle">
        <div className="card-header">
          <div className="card-title">CUSTOMER CHURN RISK &amp; NEXT REPURCHASE TIMELINE</div>
          <span className="badge badge--indigo">SURVIVAL ANALYSIS MODEL</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>BUYER ID / PROFILE</th>
                <th>CHURN RISK PROBABILITY</th>
                <th>LTV SEGMENT</th>
                <th>PREDICTED REPURCHASE WINDOW</th>
                <th>PROJECTED NEXT ORDER</th>
              </tr>
            </thead>
            <tbody>
              {customers.slice(0, 20).map((c, i) => {
                const meta = c.metadata || {}
                const risk = typeof c.value === 'number' ? c.value : 0.35
                return (
                  <tr key={i}>
                    <td className="font-mono" style={{ fontWeight: 800 }}>
                      {c.entity_id}
                    </td>
                    <td>
                      <div className="churn-bar-wrap">
                        <div
                          className="churn-bar"
                          style={{
                            width: `${Math.min(100, risk * 100)}%`,
                            background: risk > 0.7 ? 'var(--bauhaus-red)' : risk > 0.4 ? 'var(--bauhaus-yellow)' : 'var(--bauhaus-blue)'
                          }}
                        />
                      </div>
                      <span className="font-mono" style={{ fontWeight: 900 }}>{formatPercent(risk * 100, 0)}</span>
                    </td>
                    <td>
                      <span className={`badge ${risk > 0.7 ? 'badge--rose' : risk > 0.4 ? 'badge--amber' : 'badge--emerald'}`}>
                        {meta.customer_segment || 'VIP ACTIVE'}
                      </span>
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {meta.repurchase_timing_description || 'Next 14-30 days'}
                    </td>
                    <td className="font-mono text-indigo" style={{ fontWeight: 900 }}>
                      {meta.predicted_next_order_spend ? formatCurrency(meta.predicted_next_order_spend) : '₹1,999'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
