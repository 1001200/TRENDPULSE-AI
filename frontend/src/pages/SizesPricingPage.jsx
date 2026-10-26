import React, { useState, useEffect } from 'react'
import {
  Ruler,
  DollarSign,
  Layers,
  Sparkles,
  TrendingUp,
  Tag
} from 'lucide-react'
import { getInsights, getIngestionStats } from '../services/api'
import SizeHorizontalBarChart from '../components/sizes/SizeHorizontalBarChart'
import SizeDonutChart from '../components/sizes/SizeDonutChart'
import PriceBracketBarChart from '../components/sizes/PriceBracketBarChart'
import CategorySizeBreakdown from '../components/sizes/CategorySizeBreakdown'
import CategorySweetSpots from '../components/sizes/CategorySweetSpots'

export default function SizesPricingPage() {
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
      console.error('Failed to fetch sizes and pricing data:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData(period)
  }, [period])

  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod)
  }

  // Active period display label mapping
  const periodLabelMap = {
    all: 'All Time',
    this_month: 'This Month',
    last_month: 'Last Month',
    '3m': 'Last 3 Months',
    '6m': 'Last 6 Months'
  }
  const activePeriodLabel = periodLabelMap[period] || 'All Time'

  // Loading skeleton matching Sales Performance & Products
  if (loading && !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="skeleton" style={{ width: '220px', height: '28px', borderRadius: 'var(--radius-md)', marginBottom: '6px' }} />
            <div className="skeleton" style={{ width: '340px', height: '16px', borderRadius: 'var(--radius-sm)' }} />
          </div>
          <div className="skeleton" style={{ width: '380px', height: '36px', borderRadius: 'var(--radius-pill)' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {[1, 2].map(i => (
            <div key={i} className="skeleton" style={{ height: '115px', borderRadius: 'var(--radius-xl)' }} />
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          <div className="skeleton" style={{ height: '330px', borderRadius: 'var(--radius-xl)' }} />
          <div className="skeleton" style={{ height: '330px', borderRadius: 'var(--radius-xl)' }} />
        </div>
      </div>
    )
  }

  if (!data?.clothing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-display)', margin: 0 }}>
            Sizes & Pricing
          </h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Understand which sizes sell best and which prices drive revenue.
          </span>
        </div>
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No size or pricing data available. Please upload sales records or load sample data.
        </div>
      </div>
    )
  }

  const { clothing } = data
  const dominantSize = clothing.dominant_size
  const dominantPrice = clothing.dominant_price_bracket

  // Calculations for safe totals
  const totalGarmentUnits = clothing.sales_by_size?.reduce((acc, s) => acc + (s.units_sold || 0), 0) || 0
  const totalGarmentRevenue = clothing.sales_by_size?.reduce((acc, s) => acc + (s.revenue || 0), 0) || 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* 1. Header with Title, Active Period Badge & Polished Segmented Control */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.85rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sizes & Pricing
            </h2>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              color: 'var(--forest-green)',
              background: 'var(--mint-soft)',
              padding: '2px 9px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid rgba(6, 78, 53, 0.12)'
            }}>
              {activePeriodLabel}
            </span>
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Understand which sizes sell best and which prices drive revenue.
          </span>
        </div>

        {/* Polished Reporting-Period Segmented Control */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-segment)',
          padding: '3px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid rgba(18, 38, 28, 0.05)',
          flexWrap: 'wrap'
        }}>
          {[
            { id: 'all', label: 'All Time' },
            { id: 'this_month', label: 'This Month' },
            { id: 'last_month', label: 'Last Month' },
            { id: '3m', label: 'Last 3 Months' },
            { id: '6m', label: 'Last 6 Months' },
          ].map(item => {
            const isSelected = period === item.id
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handlePeriodChange(item.id)}
                style={{
                  padding: '4px 12px',
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
                {item.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* 2. Redesigned KPI Cards: Top-Selling Size & Top Price Range */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1rem'
      }}>
        {/* KPI Card 1: Top-Selling Size */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <Ruler size={18} color="var(--forest-green)" />
            </div>
            {dominantSize?.size && (
              <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
                {dominantSize.pct_of_sales}% Volume Share
              </span>
            )}
          </div>
          <div>
            <span className="kpi-label">Top-Selling Size</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span style={{
                fontSize: '1.45rem',
                fontWeight: 800,
                color: 'var(--forest-green)',
                fontFamily: 'var(--font-display)',
                lineHeight: 1.15,
                display: 'block'
              }}>
                Size {dominantSize?.size || 'N/A'}
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {dominantSize?.units_sold || 0} units sold • {dominantSize?.revenue_formatted || '₹0'} revenue generated
              </span>
            </div>
          </div>
        </div>

        {/* KPI Card 2: Top Price Range */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <DollarSign size={18} color="var(--forest-green)" />
            </div>
            {dominantPrice?.pct_of_sales !== undefined && (
              <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
                {dominantPrice.pct_of_sales}% Rev Share
              </span>
            )}
          </div>
          <div>
            <span className="kpi-label">Top Price Range</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span style={{
                fontSize: '1.45rem',
                fontWeight: 800,
                color: 'var(--forest-green)',
                fontFamily: 'var(--font-display)',
                lineHeight: 1.15,
                display: 'block'
              }}>
                {dominantPrice?.range || '₹1,000 – ₹1,499'}
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {dominantPrice?.revenue_formatted || '₹0'} revenue • {dominantPrice?.units || 0} units sold ({dominantPrice?.pct_of_units || 0}% volume)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Primary Visualizations Grid: Size Donut Chart & Vertical Price Bracket Chart */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        gap: '1.25rem'
      }}>
        <SizeDonutChart
          salesBySize={clothing.sales_by_size}
          totalUnits={totalGarmentUnits}
        />

        <PriceBracketBarChart
          salesByPriceRange={clothing.sales_by_price_range}
          dominantPriceBracket={dominantPrice}
          totalRevenue={totalGarmentRevenue}
          totalUnits={totalGarmentUnits}
        />
      </div>

      {/* 4. Category × Size Breakdown */}
      <CategorySizeBreakdown
        categoryXSize={clothing.category_x_size}
        catSizeInsight={clothing.cat_size_insight}
      />

      {/* 5. Category Price Sweet Spots */}
      <CategorySweetSpots
        categoryXPrice={clothing.category_x_price}
      />
    </div>
  )
}
