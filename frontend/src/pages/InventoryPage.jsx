import React from 'react'
import { Shirt, AlertTriangle, Package, CheckCircle2, TrendingUp, Loader } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import { formatCurrency, formatPercent, formatNumber, shortenProduct } from '../utils/formatters'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
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

const COLORS = ['#D02020', '#1040C0', '#F0C020', '#121212', '#7A7A7A', '#B81818', '#0E35A0']

export default function InventoryPage() {
  const { result, dataset, loading } = useStore()

  if (loading && !result) {
    return (
      <div className="page-container flex-center" style={{ minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={38} className="spin text-indigo" strokeWidth={2.5} />
          <p className="text-muted mt-md font-heading" style={{ fontWeight: 800, textTransform: 'uppercase' }}>
            AUDITING SIZE CURVES &amp; STOCKOUT RISKS…
          </p>
        </div>
      </div>
    )
  }

  const r = result || {}
  const apparel = r.apparel_intelligence || {}
  const sizeCurve = apparel.size_intelligence?.overall_size_curve || []
  const colorways = apparel.color_intelligence?.color_family_distribution || []
  const fits = Array.isArray(apparel.fit_intelligence) ? apparel.fit_intelligence : []
  const brokenSizesRaw = apparel.broken_size_runs || []
  const brokenSizes = Array.isArray(brokenSizesRaw) ? brokenSizesRaw : (brokenSizesRaw.broken_runs || [])

  const forecasts = r.ml_intelligence?.demand_forecast || []
  const forecastChartData = forecasts.slice(0, 10).map(f => ({
    name: shortenProduct(f.entity_id, 20),
    units: Math.round(f.value || 0),
  }))

  return (
    <div className="page-container">
      {/* Header */}
      <div className="card mb-md animate-in card-glyph-square" style={{ padding: '20px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase' }}>
                INVENTORY &amp; SIZE-RUN INTELLIGENCE
              </h2>
              <span className="badge badge--rose">STOCKOUT PREVENTION</span>
              <span className="badge badge--indigo">SIZE CURVES</span>
            </div>
            <div className="text-xs" style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              ELIMINATE BROKEN SIZE CURVES • RESTOCK EXACT RATIOS WITHOUT ACCUMULATING DEADSTOCK
            </div>
          </div>
        </div>
      </div>

      {/* Broken Size Run Alerts */}
      {brokenSizes.length > 0 && (
        <div className="card mb-md animate-in" style={{ borderLeft: '10px solid var(--bauhaus-red)', background: 'var(--bauhaus-red-lt)' }}>
          <div className="card-title text-rose" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <AlertTriangle size={20} />
            <span>CRITICAL BROKEN SIZE RUN ALERT ({brokenSizes.length} High-Demand Stockouts)</span>
          </div>
          <p className="text-sm" style={{ fontWeight: 700, color: 'var(--bauhaus-black)', marginTop: 6, marginBottom: 12 }}>
            Your highest-converting customer sizes (e.g. M &amp; L) are completely out of stock while edge sizes sit unsold. Customers are landing on your store and bouncing.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {brokenSizes.slice(0, 3).map((b, i) => (
              <div key={i} className="badge badge--rose" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                {b.product || 'Core SKU'}: MISSING SIZES [{(b.missing_sizes || ['M', 'L']).join(', ')}]
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Size Curve Distribution */}
      <div className="card mb-md animate-in animate-in-delay-1 card-glyph-circle">
        <div className="card-title">STORE-WIDE SIZE RUN CURVE (HISTORICAL DEMAND DISTRIBUTION)</div>
        <p className="text-xs text-muted" style={{ textTransform: 'uppercase', fontWeight: 700, marginBottom: 16 }}>
          USE THIS EXACT RATIO WHEN PLACING FACTORY PURCHASE ORDERS RATHER THAN ORDERING EQUAL QUANTITIES
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={sizeCurve}>
            <CartesianGrid stroke="#121212" strokeDasharray="0" opacity={0.15} />
            <XAxis dataKey="size" tick={{ fill: '#121212', fontSize: 12, fontWeight: 800 }} />
            <YAxis tick={{ fill: '#121212', fontSize: 11, fontWeight: 700 }} />
            <Tooltip {...ChartTooltipStyle} formatter={(v) => [`${v} Units Sold`, 'Historical Volume']} />
            <Bar dataKey="units_sold" fill="#D02020" stroke="#121212" strokeWidth={2} radius={[0, 0, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Grid: Colorways & Fits */}
      <div className="grid-2 mb-md animate-in animate-in-delay-2">
        <div className="card">
          <div className="card-title">COLORWAY REVENUE DISTRIBUTION</div>
          <div style={{ marginTop: 12 }}>
            {colorways.slice(0, 7).map((c, i) => (
              <div key={i} className="palette-row">
                <span className="palette-dot" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="palette-name">{c.color_family}</span>
                <span className="palette-pct">{formatPercent(c.revenue_share)}</span>
                <span className="palette-rev">{formatCurrency(c.revenue)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">FIT &amp; SILHOUETTE RANKING</div>
          <div style={{ marginTop: 12 }}>
            {fits.slice(0, 7).map((f, i) => (
              <div key={i} className="palette-row">
                <span className="badge badge--indigo">#{i + 1}</span>
                <span className="palette-name">{f.fit_type}</span>
                <span className="palette-pct">{f.units_sold} units</span>
                <span className="palette-rev">{formatPercent(f.revenue_share)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top 10 Demand Forecasts */}
      {forecastChartData.length > 0 && (
        <div className="card animate-in animate-in-delay-3 card-glyph-triangle">
          <div className="card-title">30-DAY PREDICTIVE DEMAND FORECASTS (TOP 10 HERO SKUS)</div>
          <p className="text-xs text-muted" style={{ textTransform: 'uppercase', fontWeight: 700, marginBottom: 16 }}>
            PROJECTED UNITS REQUIRED OVER THE NEXT MONTH TO PREVENT REVENUE ATTRITION
          </p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={forecastChartData}>
              <CartesianGrid stroke="#121212" strokeDasharray="0" opacity={0.15} />
              <XAxis dataKey="name" tick={{ fill: '#121212', fontSize: 10, fontWeight: 700 }} angle={-15} textAnchor="end" height={60} />
              <YAxis tick={{ fill: '#121212', fontSize: 11, fontWeight: 700 }} />
              <Tooltip {...ChartTooltipStyle} formatter={(v) => [`${v} Units`, 'Forecasted Demand']} />
              <Bar dataKey="units" fill="#F0C020" stroke="#121212" strokeWidth={2} radius={[0, 0, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
