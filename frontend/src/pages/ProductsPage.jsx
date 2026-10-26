import React, { useState, useEffect } from 'react'
import {
  Layers,
  Package,
  TrendingUp,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  Filter,
  ShoppingBag,
  Award,
  Sparkles
} from 'lucide-react'
import { getInsights, getIngestionStats } from '../services/api'
import CategoryTreemapChart from '../components/products/CategoryTreemapChart'
import MonthlyCategoryBarChart from '../components/products/MonthlyCategoryBarChart'
import ProductRevenueShareDonut from '../components/products/ProductRevenueShareDonut'
import CategoryHorizontalBarChart from '../components/products/CategoryHorizontalBarChart'
import { Shirt } from 'lucide-react'

export default function ProductsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [productSortBy, setProductSortBy] = useState('units') // 'units' | 'revenue'

  const fetchData = async (p = period, cat = selectedCategory) => {
    setLoading(true)
    try {
      const statsRes = await getIngestionStats()
      if (statsRes.ok && statsRes.data.has_data) {
        const insightsRes = await getInsights({ period: p, category: cat })
        if (insightsRes.ok && insightsRes.data.has_data) {
          setData(insightsRes.data)
        }
      }
    } catch (err) {
      console.error('Failed to fetch products data:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData(period, selectedCategory)
  }, [period, selectedCategory])

  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod)
  }

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value)
  }

  // Active period display label mapping matching Sales Performance
  const periodLabelMap = {
    all: 'All Time',
    this_month: 'This Month',
    last_month: 'Last Month',
    '3m': 'Last 3 Months',
    '6m': 'Last 6 Months'
  }
  const activePeriodLabel = periodLabelMap[period] || 'All Time'

  // Loading skeleton matching Sales Performance
  if (loading && !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="skeleton" style={{ width: '220px', height: '28px', borderRadius: 'var(--radius-md)', marginBottom: '6px' }} />
            <div className="skeleton" style={{ width: '320px', height: '16px', borderRadius: 'var(--radius-sm)' }} />
          </div>
          <div className="skeleton" style={{ width: '380px', height: '36px', borderRadius: 'var(--radius-pill)' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(215px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: '125px', borderRadius: 'var(--radius-xl)' }} />
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          <div className="skeleton" style={{ height: '320px', borderRadius: 'var(--radius-xl)' }} />
          <div className="skeleton" style={{ height: '320px', borderRadius: 'var(--radius-xl)' }} />
        </div>
      </div>
    )
  }

  if (!data?.products) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-display)', margin: 0 }}>
            Products
          </h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Understand which clothing products drive your sales.
          </span>
        </div>
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No product data available. Please upload sales data or load sample data.
        </div>
      </div>
    )
  }

  const { products, filters_applied, sales } = data

  // Filter out any non-clothing categories safely (strictly clothing only)
  const safeCategories = (filters_applied?.available_categories || []).filter(
    c => !c.toLowerCase().includes('accessor') && !c.toLowerCase().includes('jewel')
  )
  const salesByCategory = (products?.sales_by_category || []).filter(
    c => !c.category.toLowerCase().includes('accessor') && !c.category.toLowerCase().includes('jewel')
  )

  // Best-selling lists
  const bestSellersByUnits = products.best_sellers_by_units || []
  const bestSellersByRevenue = products.best_sellers_by_revenue || []
  const activeBestSellers = productSortBy === 'units' ? bestSellersByUnits : bestSellersByRevenue

  // KPI Metrics
  const topCategory = salesByCategory.length > 0 ? salesByCategory[0] : null
  const bestSellerByUnits = bestSellersByUnits.length > 0 ? bestSellersByUnits[0] : null
  const bestSellerByRevenue = bestSellersByRevenue.length > 0 ? bestSellersByRevenue[0] : null

  // Maximum value for Best-Selling progress bar scaling
  const maxBestSellerMetric = activeBestSellers.length > 0
    ? (productSortBy === 'units' ? (activeBestSellers[0].units_sold || 1) : (activeBestSellers[0].revenue || 1))
    : 1

  // Volume vs Revenue Contrast
  const contrast = products.volume_vs_revenue_contrast
  const volLeader = contrast?.volume_leader
  const revLeader = contrast?.revenue_leader
  const hasContrastData = volLeader && revLeader && (volLeader.units > 0 || revLeader.revenue > 0)
  const isSameLeader = contrast?.is_same || (volLeader?.product_id && volLeader?.product_id === revLeader?.product_id)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* =========================================================================
          1. Header with Title, Period Badge, Subtitle & Filter Controls
          ========================================================================= */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.85rem'
      }}>
        {/* Title & Subtitle */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Products
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
            {selectedCategory !== 'All' && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 600,
                color: 'var(--forest-dark)',
                background: '#E0EDE6',
                padding: '2px 9px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(6, 78, 53, 0.18)'
              }}>
                {selectedCategory}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
            Understand which clothing products drive your sales.
          </span>
        </div>

        {/* Filters Group: Reporting Period & Clothing Category */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem',
          flexWrap: 'wrap'
        }}>
          {/* Polished Reporting-Period Segmented Control (Exact match to Sales Performance) */}
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

          {/* Clothing Category Filter Dropdown */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            background: '#FFFFFF',
            padding: '3px 10px',
            borderRadius: 'var(--radius-pill)',
            border: selectedCategory !== 'All' ? '1.5px solid var(--forest-green)' : '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-card)'
          }}>
            <Filter size={13} color="var(--forest-green)" />
            <select
              value={selectedCategory}
              onChange={handleCategoryChange}
              style={{
                border: 'none',
                background: 'transparent',
                fontSize: '0.72rem',
                fontWeight: 600,
                color: selectedCategory !== 'All' ? 'var(--forest-green)' : 'var(--text-primary)',
                cursor: 'pointer',
                outline: 'none',
                padding: '2px 0'
              }}
            >
              <option value="All">All Clothing Categories</option>
              {safeCategories.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* =========================================================================
          2. Four Redesigned Responsive KPI Cards (Consistent Dimensions, No Overlap)
          ========================================================================= */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(215px, 1fr))',
        gap: '1rem'
      }}>
        {/* Card 1: Top Category */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <Layers size={18} color="var(--forest-green)" />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              {topCategory ? `${topCategory.pct_of_total}% Share` : 'Top Category'}
            </span>
          </div>
          <div>
            <span className="kpi-label">Top Category</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.35rem',
                fontWeight: 800,
                color: 'var(--forest-green)',
                lineHeight: 1.15,
                display: 'block'
              }}>
                {topCategory?.category || 'None'}
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {topCategory
                  ? `${topCategory.revenue_formatted} • ${topCategory.units_sold} units sold`
                  : 'No category sales recorded'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 2: Best-Selling Product (Units Sold) */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <Package size={18} color="var(--forest-green)" />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              By Volume
            </span>
          </div>
          <div>
            <span className="kpi-label">Best-Selling Product</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '0.96rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  lineHeight: 1.25,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  minHeight: '2.4em'
                }}
                title={bestSellerByUnits?.product_name || 'N/A'}
              >
                {bestSellerByUnits?.product_name || 'None recorded'}
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {bestSellerByUnits
                  ? `${bestSellerByUnits.units_sold} units sold • ${bestSellerByUnits.revenue_formatted}`
                  : 'No unit sales in period'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: Top Revenue Product */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <TrendingUp size={18} color="var(--forest-green)" />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              By Revenue
            </span>
          </div>
          <div>
            <span className="kpi-label">Top Revenue Product</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '0.96rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  lineHeight: 1.25,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  minHeight: '2.4em'
                }}
                title={bestSellerByRevenue?.product_name || 'N/A'}
              >
                {bestSellerByRevenue?.product_name || 'None recorded'}
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {bestSellerByRevenue
                  ? `${bestSellerByRevenue.revenue_formatted} grossed • ${bestSellerByRevenue.units_sold} sold`
                  : 'No revenue sales in period'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 4: Sell-Through Rate */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <BarChart3 size={18} color="var(--forest-green)" />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              Stock Turn
            </span>
          </div>
          <div>
            <span className="kpi-label">Sell-Through Rate</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.35rem',
                fontWeight: 800,
                color: 'var(--forest-green)',
                lineHeight: 1.15,
                display: 'block'
              }}>
                {products.sell_through_rate}%
              </span>
              <span className="kpi-subtext" style={{ display: 'block', marginTop: '4px' }}>
                {products.sell_through_insight || 'Curated catalog inventory efficiency'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          3. Two Primary Visual Cards (Best-Selling Products & Sales by Category)
          ========================================================================= */}
      {/* =========================================================================
          3. Two-Column Analytics Grid Matching Reference Mockup
             Left: Top 5 Best-Selling Products + Monthly Category Performance
             Right: Category Revenue Distribution (Treemap) + Product Revenue Share (Donut)
          ========================================================================= */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
        gap: '1.25rem',
        alignItems: 'start'
      }}>
        {/* Left Column: Best-Selling Products + Monthly Category Bar Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Card 1: Top 5 Best-Selling Products */}
          <div className="card" style={{ padding: '1.4rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <h3 style={{
                    fontSize: '1.08rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font-display)',
                    color: 'var(--text-primary)',
                    margin: 0
                  }}>
                    Top 5 Best-Selling Products
                  </h3>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    color: 'var(--forest-green)',
                    background: 'var(--mint-soft)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-pill)',
                    border: '1px solid rgba(6, 78, 53, 0.1)'
                  }}>
                    Ranked
                  </span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                  Highest volume and revenue contributors
                </span>
              </div>

              {/* Segmented Control: By Units | By Revenue */}
              <div className="segmented-control">
                <button
                  type="button"
                  className={`segmented-control-btn ${productSortBy === 'units' ? 'active' : ''}`}
                  onClick={() => setProductSortBy('units')}
                >
                  By Units
                </button>
                <button
                  type="button"
                  className={`segmented-control-btn ${productSortBy === 'revenue' ? 'active' : ''}`}
                  onClick={() => setProductSortBy('revenue')}
                >
                  By Revenue
                </button>
              </div>
            </div>

            {/* Column Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              fontWeight: 700,
              marginBottom: '0.75rem',
              paddingBottom: '0.45rem',
              borderBottom: '1px solid rgba(18, 38, 28, 0.06)',
              letterSpacing: '0.04em'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <span style={{ width: '22px', textAlign: 'center' }}>#</span>
                <span>PRODUCT NAME</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                <span style={{ width: '70px', textAlign: 'right' }}>UNITS SOLD</span>
                <span style={{ width: '80px', textAlign: 'right' }}>REVENUE</span>
              </div>
            </div>

            {/* Ranked List (Top 5) */}
            {activeBestSellers.length === 0 ? (
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                No product sales recorded in this period.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                {activeBestSellers.slice(0, 5).map((p, idx) => {
                  const metricValue = productSortBy === 'units' ? p.units_sold : p.revenue
                  const barFillPct = Math.min(100, Math.max(14, ((metricValue / maxBestSellerMetric) * 100)))

                  return (
                    <div
                      key={p.product_id || idx}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.45rem',
                        padding: '0.4rem 0.2rem'
                      }}
                      title={`${p.product_name} • ${p.units_sold} sold • ${p.revenue_formatted}`}
                    >
                      {/* Top Row: Rank, Thumbnail, Title, Units & Revenue */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '0.75rem'
                      }}>
                        {/* Left: Rank + Fashion Thumbnail + Title */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flex: 1, minWidth: 0 }}>
                          <span style={{
                            fontSize: '0.74rem',
                            fontWeight: 800,
                            color: '#ffffff',
                            background: idx === 0 ? 'var(--forest-green)' : '#0F6B4B',
                            width: '22px',
                            height: '22px',
                            borderRadius: '50%',
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                            boxShadow: '0 2px 5px rgba(6, 78, 53, 0.2)'
                          }}>
                            {idx + 1}
                          </span>

                          <div style={{
                            width: '34px',
                            height: '34px',
                            borderRadius: 'var(--radius-md)',
                            background: 'var(--mint-soft)',
                            border: '1px solid rgba(6, 78, 53, 0.12)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0
                          }}>
                            <Shirt size={16} color="var(--forest-green)" strokeWidth={1.8} />
                          </div>

                          <div style={{ minWidth: 0, flex: 1 }}>
                            <span style={{
                              fontSize: '0.84rem',
                              fontWeight: 700,
                              color: 'var(--text-primary)',
                              lineHeight: 1.25,
                              display: 'block',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}>
                              {p.product_name}
                            </span>
                            <span style={{ fontSize: '0.69rem', color: 'var(--text-muted)' }}>
                              {p.category} {p.size ? `• Size ${p.size}` : ''}
                            </span>
                          </div>
                        </div>

                        {/* Right: Units Sold & Revenue */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexShrink: 0 }}>
                          <span style={{
                            width: '70px',
                            textAlign: 'right',
                            fontSize: '0.84rem',
                            fontWeight: 700,
                            color: 'var(--text-primary)',
                            fontFamily: 'var(--font-display)'
                          }}>
                            {p.units_sold?.toLocaleString()}
                          </span>
                          <span style={{
                            width: '80px',
                            textAlign: 'right',
                            fontSize: '0.86rem',
                            fontWeight: 800,
                            color: 'var(--forest-green)',
                            fontFamily: 'var(--font-display)'
                          }}>
                            {p.revenue_formatted}
                          </span>
                        </div>
                      </div>

                      {/* Horizontal Progress Bar */}
                      <div style={{
                        width: '100%',
                        height: '5px',
                        background: '#EAF3EE',
                        borderRadius: 'var(--radius-pill)',
                        overflow: 'hidden',
                        marginTop: '2px'
                      }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${barFillPct}%`,
                            background: idx === 0
                              ? 'linear-gradient(90deg, #064E35 0%, #158058 100%)'
                              : 'linear-gradient(90deg, #0F6B4B 0%, #3DAE84 100%)',
                            borderRadius: 'var(--radius-pill)',
                            transition: 'width 0.4s ease'
                          }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Monthly Category Performance (Vertical Grouped Bar Chart) */}
          <MonthlyCategoryBarChart monthlyTrends={data?.trends?.monthly_category_trends} />
        </div>

        {/* Right Column: Treemap + Product Donut */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Category Revenue Distribution (Proportional Squarified Treemap) */}
          <CategoryTreemapChart
            categories={salesByCategory}
            totalRevenueRaw={sales?.total_sales_raw}
          />

          {/* Product Revenue Share (Center-labeled Donut Chart) */}
          <ProductRevenueShareDonut
            bestSellersByRevenue={bestSellersByRevenue}
            totalRevenueRaw={sales?.total_sales_raw}
          />
        </div>
      </div>

      {/* =========================================================================
          4. Simplified Volume Leader vs Revenue Leader Comparison Cards
          ========================================================================= */}
      {hasContrastData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {/* Section Sub-header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Award size={16} color="var(--forest-green)" />
              <h3 style={{
                fontSize: '0.95rem',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Volume Leader vs Revenue Leader Comparison
              </h3>
            </div>
            {isSameLeader && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 9px',
                borderRadius: 'var(--radius-pill)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                border: '1px solid rgba(6, 78, 53, 0.12)'
              }}>
                <Sparkles size={11} /> Unified Leader in Both Metrics
              </span>
            )}
          </div>

          {/* Comparison Cards Side-by-Side */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1rem'
          }}>
            {/* Card A: Volume Leader */}
            <div className="card" style={{ padding: '1.25rem 1.4rem' }}>
              <div className="kpi-top-row">
                <div className="kpi-icon-bubble">
                  <Package size={18} color="var(--forest-green)" />
                </div>
                <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
                  Most Units Sold
                </span>
              </div>
              <div>
                <span className="kpi-label">Volume Leader</span>
                <span style={{
                  fontSize: '0.96rem',
                  fontWeight: 800,
                  color: 'var(--text-primary)',
                  display: 'block',
                  marginTop: '0.3rem',
                  lineHeight: 1.3,
                  wordBreak: 'break-word'
                }}>
                  {volLeader?.name || 'N/A'}
                </span>
                <div style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '0.5rem',
                  marginTop: '0.45rem'
                }}>
                  <span style={{
                    fontSize: '1.35rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font-display)',
                    color: 'var(--forest-green)',
                    lineHeight: 1
                  }}>
                    {volLeader?.units || 0} units
                  </span>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    sold @ {volLeader?.unit_price_formatted || '₹0'} each
                  </span>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  display: 'block',
                  marginTop: '0.35rem',
                  borderTop: '1px solid rgba(0, 0, 0, 0.04)',
                  paddingTop: '0.35rem'
                }}>
                  Total Sales Revenue: <strong>{volLeader?.revenue_formatted || '₹0'}</strong> {volLeader?.category ? `• ${volLeader.category}` : ''}
                </span>
              </div>
            </div>

            {/* Card B: Revenue Leader */}
            <div className="card" style={{ padding: '1.25rem 1.4rem' }}>
              <div className="kpi-top-row">
                <div className="kpi-icon-bubble">
                  <TrendingUp size={18} color="var(--forest-green)" />
                </div>
                <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
                  Highest Gross Revenue
                </span>
              </div>
              <div>
                <span className="kpi-label">Revenue Leader</span>
                <span style={{
                  fontSize: '0.96rem',
                  fontWeight: 800,
                  color: 'var(--text-primary)',
                  display: 'block',
                  marginTop: '0.3rem',
                  lineHeight: 1.3,
                  wordBreak: 'break-word'
                }}>
                  {revLeader?.name || 'N/A'}
                </span>
                <div style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '0.5rem',
                  marginTop: '0.45rem'
                }}>
                  <span style={{
                    fontSize: '1.35rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font-display)',
                    color: 'var(--forest-green)',
                    lineHeight: 1
                  }}>
                    {revLeader?.revenue_formatted || '₹0'}
                  </span>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    gross revenue ({revLeader?.units || 0} units)
                  </span>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  display: 'block',
                  marginTop: '0.35rem',
                  borderTop: '1px solid rgba(0, 0, 0, 0.04)',
                  paddingTop: '0.35rem'
                }}>
                  Catalog Unit Price: <strong>{revLeader?.unit_price_formatted || '₹0'}</strong> {revLeader?.category ? `• ${revLeader.category}` : ''}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* =========================================================================
          5. Supporting Cards: Fastest-Selling Products & Slow-Moving Products
          ========================================================================= */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '1.25rem'
      }}>
        {/* Supporting Card 1: Fastest-Selling Products */}
        <div className="card" style={{ padding: '1.35rem 1.45rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={16} color="var(--forest-green)" />
              <h3 style={{
                fontSize: '0.95rem',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Fastest-Selling Products
              </h3>
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              Turnaround Time
            </span>
          </div>

          {products.fastest_selling?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {products.fastest_selling.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.75rem',
                    paddingBottom: '0.55rem',
                    borderBottom: idx < products.fastest_selling.length - 1 ? '1px solid rgba(0, 0, 0, 0.04)' : 'none'
                  }}
                >
                  {/* Left: Product Name */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span
                      style={{
                        fontSize: '0.82rem',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        display: 'block',
                        lineHeight: 1.25,
                        wordBreak: 'break-word'
                      }}
                      title={item.product_name}
                    >
                      {item.product_name}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {item.category} • {item.revenue_formatted}
                    </span>
                  </div>

                  {/* Right: Visually Separated Duration Pill */}
                  <div style={{ flexShrink: 0, textAlign: 'right' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: 'var(--forest-dark)',
                      background: 'var(--mint-soft)',
                      padding: '3px 9px',
                      borderRadius: 'var(--radius-pill)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      border: '1px solid rgba(6, 78, 53, 0.12)'
                    }}>
                      <Clock size={11} color="var(--forest-green)" />
                      Sold in {item.display_time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
              Turnaround velocity requires drop timestamps. Available when drop times are tracked.
            </div>
          )}
        </div>

        {/* Supporting Card 2: Slow-Moving Products */}
        <div className="card" style={{ padding: '1.35rem 1.45rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={16} color="#B45309" />
              <h3 style={{
                fontSize: '0.95rem',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Slow-Moving Products
              </h3>
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              Available in Catalog
            </span>
          </div>

          {products.slow_moving?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {products.slow_moving.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.75rem',
                    paddingBottom: '0.55rem',
                    borderBottom: idx < products.slow_moving.length - 1 ? '1px solid rgba(0, 0, 0, 0.04)' : 'none'
                  }}
                >
                  {/* Left: Product Name */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span
                      style={{
                        fontSize: '0.82rem',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        display: 'block',
                        lineHeight: 1.25,
                        wordBreak: 'break-word'
                      }}
                      title={item.product_name}
                    >
                      {item.product_name}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {item.category} • Listed at {item.price_formatted}
                    </span>
                  </div>

                  {/* Right: Restrained Days Listed Badge */}
                  <div style={{ flexShrink: 0, textAlign: 'right' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: '#92400E',
                      background: '#FEF3C7',
                      padding: '3px 9px',
                      borderRadius: 'var(--radius-pill)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      border: '1px solid rgba(180, 83, 9, 0.15)'
                    }}>
                      <AlertCircle size={11} color="#B45309" />
                      Listed {item.days_listed} days
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              color: 'var(--forest-green)',
              fontSize: '0.82rem',
              padding: '2rem 1rem'
            }}>
              <CheckCircle2 size={16} />
              <span>All catalog products in this selection have registered sales.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
