import React from 'react'
import { IndianRupee, TrendingUp, AlertOctagon, Sparkles, ShieldAlert, Loader } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import { formatCurrency, formatPercent, formatNumber, shortenProduct } from '../utils/formatters'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const ChartTooltipStyle = {
  contentStyle: {
    background: '#FFFFFF',
    border: '3px solid #121212',
    borderRadius: 0,
    fontSize: '0.84rem',
    fontWeight: 800,
    fontFamily: "'Outfit', sans-serif",
    color: '#121212',
    boxShadow: '4px 4px 0px 0px #121212',
    padding: '8px 14px',
  },
  itemStyle: {
    color: '#121212',
    fontWeight: 800,
  }
}

export default function EconomicsPage() {
  const { result, loading } = useStore()

  if (loading && !result) {
    return (
      <div className="page-container flex-center" style={{ minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={38} className="spin text-indigo" strokeWidth={2.5} />
          <p className="text-muted mt-md font-heading" style={{ fontWeight: 800, textTransform: 'uppercase' }}>
            AUDITING UNIT ECONOMICS &amp; DISCOUNT BLEED…
          </p>
        </div>
      </div>
    )
  }

  const r = result || {}
  const economics = r.fashion_economics?.unit_economics || {}
  const econMetrics = economics.overall_metrics || {}
  const quadrants = economics.profitability_quadrants || {}
  const revDecomp = r.revenue_decomposition || {}
  const pvm = revDecomp.summary || revDecomp.decomposition || {}

  const grossRev = econMetrics.total_revenue || r.apparel_intelligence?.total_apparel_revenue || 0
  const grossProfit = econMetrics.total_gross_profit || 0
  const marginPct = econMetrics.gross_margin_percentage || 57.0
  const bleed = econMetrics.total_discount_bleed || 0

  const stars = quadrants.star_performers || []
  const gems = quadrants.hidden_gems || []
  const destroyers = quadrants.value_destroyers || []

  const rawWeekly = r.time_aggregation?.weekly || []
  const timeSeries = rawWeekly.map(w => ({
    date: w.period?.split('/')[0] || w.period,
    revenue: w.total_revenue || w.revenue || 0,
  }))

  return (
    <div className="page-container">
      {/* Header */}
      <div className="card mb-md animate-in card-glyph-triangle" style={{ padding: '20px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase' }}>
                UNIT ECONOMICS &amp; PROFIT AUDIT
              </h2>
              <span className="badge badge--emerald">MARGIN PROTECTION</span>
              <span className="badge badge--rose">DISCOUNT LEAK AUDIT</span>
            </div>
            <div className="text-xs" style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              PROTECT GROSS MARGINS • PREVENT PROMO CODE EROSION • IDENTIFY VALUE DESTROYERS
            </div>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="kpi-grid animate-in">
        <div className="kpi-card kpi-card--blue">
          <div className="kpi-label">GROSS REVENUE</div>
          <div className="kpi-value">{formatCurrency(grossRev)}</div>
          <div className="kpi-sub">STORE VOLUME</div>
        </div>

        <div className="kpi-card kpi-card--yellow">
          <div className="kpi-label">GROSS PROFIT</div>
          <div className="kpi-value">{formatCurrency(grossProfit)}</div>
          <div className="kpi-sub">NET STORE EARNINGS</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">STORE MARGIN</div>
          <div className="kpi-value text-indigo">{formatPercent(marginPct)}</div>
          <div className="kpi-sub">BENCHMARK: 55-60%</div>
        </div>

        <div className="kpi-card kpi-card--red">
          <div className="kpi-label">DISCOUNT CODE BLEED</div>
          <div className="kpi-value">-₹{Number(bleed).toLocaleString('en-IN')}</div>
          <div className="kpi-sub">LOST REVENUE TO CODES</div>
        </div>
      </div>

      {/* 4-Quadrant Product Profitability Matrix */}
      <div className="card mb-md animate-in animate-in-delay-1 card-glyph-square">
        <div className="card-title">4-QUADRANT PRODUCT PROFITABILITY MATRIX</div>
        <p className="text-xs text-muted" style={{ textTransform: 'uppercase', fontWeight: 700, marginBottom: 16 }}>
          AUTOMATICALLY SEGREGATES CATALOG INTO HIGH-MARGIN HEROES AND CASH DESTROYERS
        </p>
        <div className="quad-grid">
          {/* Stars */}
          <div className="quad-section quad-section--star">
            <div className="quad-label text-indigo">💎 STAR PERFORMERS ({stars.length})</div>
            {stars.slice(0, 6).map((s, i) => (
              <div key={i} className="quad-item">
                <span className="truncate">{shortenProduct(s.sku, 32)}</span>
                <span className="text-indigo" style={{ fontWeight: 900 }}>{formatPercent(s.gross_margin_percentage)}</span>
              </div>
            ))}
          </div>

          {/* Hidden Gems */}
          <div className="quad-section quad-section--cow">
            <div className="quad-label text-amber">💰 HIDDEN GEMS / HIGH MARGIN ({gems.length})</div>
            {gems.slice(0, 6).map((s, i) => (
              <div key={i} className="quad-item">
                <span className="truncate">{shortenProduct(s.sku, 32)}</span>
                <span className="text-amber" style={{ fontWeight: 900 }}>{formatPercent(s.gross_margin_percentage)}</span>
              </div>
            ))}
          </div>

          {/* Value Destroyers */}
          <div className="quad-section quad-section--under">
            <div className="quad-label text-rose">⚠️ MARGIN DESTROYERS ({destroyers.length})</div>
            {destroyers.length === 0 ? (
              <p className="text-xs text-muted">No high margin destroyers detected.</p>
            ) : (
              destroyers.slice(0, 6).map((s, i) => (
                <div key={i} className="quad-item">
                  <span className="truncate">{shortenProduct(s.sku, 32)}</span>
                  <span className="text-rose" style={{ fontWeight: 900 }}>{formatPercent(s.gross_margin_percentage)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Revenue Trajectory Over Time */}
      {timeSeries.length > 0 && (
        <div className="card animate-in animate-in-delay-2 card-glyph-circle">
          <div className="card-title">WEEKLY REVENUE TRAJECTORY</div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={timeSeries}>
              <CartesianGrid stroke="#121212" strokeDasharray="0" opacity={0.15} />
              <XAxis dataKey="date" tick={{ fill: '#121212', fontSize: 11, fontWeight: 700 }} />
              <YAxis tick={{ fill: '#121212', fontSize: 11, fontWeight: 700 }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
              <Tooltip {...ChartTooltipStyle} formatter={(v) => [formatCurrency(v), 'Revenue']} />
              <Area type="monotone" dataKey="revenue" stroke="#1040C0" strokeWidth={3} fill="#DBEAFE" fillOpacity={0.8} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
