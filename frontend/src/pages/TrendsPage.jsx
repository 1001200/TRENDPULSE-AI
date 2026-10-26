import React, { useState, useEffect } from 'react'
import PageHeader from '../components/common/PageHeader'
import {
  Flame,
  TrendingUp,
  Tag,
  DollarSign,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Info,
  Calendar,
  AlertTriangle,
  Lightbulb,
  Sparkles,
  ShoppingBag,
  Clock,
  CheckCircle2,
  Package,
  HelpCircle
} from 'lucide-react'
import { getInsights, getIngestionStats } from '../services/api'
import SalesForecastChart from '../components/trends/SalesForecastChart'
import HistoricalSalesLineChart from '../components/trends/HistoricalSalesLineChart'

export default function TrendsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('all')
  const [activeTab, setActiveTab] = useState('overview') // 'overview' | 'category' | 'size' | 'price'

  const fetchData = async (p = period) => {
    setLoading(true)
    try {
      const statsRes = await getIngestionStats()
      if (statsRes.ok && statsRes.data.has_data) {
        const insightsRes = await getInsights({ period: p })
        if (insightsRes.ok && insightsRes.data.has_data) {
          setData(insightsRes.data)
        } else {
          setData(insightsRes.data || null)
        }
      } else {
        const insightsRes = await getInsights({ period: p })
        if (insightsRes.ok && insightsRes.data?.has_data) {
          setData(insightsRes.data)
        } else {
          setData(null)
        }
      }
    } catch (err) {
      console.error('Failed to fetch trends data:', err)
      setData(null)
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
          title="Trends"
          subtitle="Discover patterns in your historical clothing sales and explore what may happen next."
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: '90px', borderRadius: 'var(--radius-xl)' }} />
          ))}
        </div>
      </div>
    )
  }

  if (!loading && (!data || !data.has_data)) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <PageHeader
          title="Trends"
          subtitle="Discover patterns in your historical clothing sales and explore what may happen next."
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
            <Flame size={28} color="var(--forest-green)" />
          </div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            No trend patterns detected yet
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Trends and predictions are computed mathematically from your sales history.
            Upload your sales records or load sample data to unlock historical trends and machine learning forecasts.
          </p>
        </div>
      </div>
    )
  }

  const trends = data?.trends?.trends || []
  const trendsData = data?.trends || {}
  const predictions = data?.predictions || {}
  const salesForecast = predictions?.sales_forecast || null
  const inventoryRisk = predictions?.inventory_risk || null
  const recommendations = data?.recommendations || predictions?.recommendations || []
  const repeatInsights = predictions?.repeat_purchase_insights || null
  const categoryOpportunities = predictions?.category_opportunities || []

  const getDomainIcon = (domain) => {
    switch (domain) {
      case 'Category Share':
      case 'Category Shift':
        return Layers
      case 'Garment Sizing':
        return Tag
      case 'Price Range':
        return DollarSign
      case 'Monthly Momentum':
        return TrendingUp
      default:
        return Flame
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '2.5rem' }}>
      {/* 1. Page Header with Title, Subtitle & Period Selector */}
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
            Trends
          </h1>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.15rem', display: 'block' }}>
            Discover patterns in your historical clothing sales and explore what may happen next.
          </span>
        </div>

        {/* Segmented Period Filter Bar */}
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

      {/* 2. Seller Data Exclusivity Banner */}
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
        <span style={{ fontSize: '0.82rem', color: 'var(--forest-dark)', lineHeight: 1.4 }}>
          <strong>Seller Data Exclusivity:</strong> All trends below represent mathematical patterns derived exclusively from your uploaded sales records.
        </span>
      </div>

      {/* ===================================================================== */}
      {/* SECTION 1: HISTORICAL BUSINESS TRENDS */}
      {/* ===================================================================== */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Historical Business Trends
            </h2>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Observed changes across your past clothing sales, categories, and sizing.
            </span>
          </div>
          <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
            Historical Observations
          </span>
        </div>

        {/* Historical Monthly Sales Line Chart */}
        <HistoricalSalesLineChart
          salesByMonth={trendsData.sales_by_month}
          strongestMonth={trendsData.strongest_month}
        />

        {/* Existing Historical Insight Cards with Corrected Calculations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {trends.map((t, idx) => {
            const Icon = getDomainIcon(t.domain)
            return (
              <div
                key={idx}
                className="card"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1.1rem 1.35rem',
                  gap: '1rem'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{
                    width: '42px', height: '42px', borderRadius: '12px',
                    background: 'var(--mint-soft)', color: 'var(--forest-green)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.2rem' }}>
                      <span style={{
                        fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase',
                        color: 'var(--forest-green)', letterSpacing: '0.05em'
                      }}>
                        {t.trend_type}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>•</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {t.domain}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0, lineHeight: 1.4 }}>
                      {t.statement}
                    </p>
                  </div>
                </div>

                <div className={`pill-badge ${t.direction === 'up' ? 'green' : t.direction === 'down' ? 'red' : 'forest'}`} style={{ flexShrink: 0 }}>
                  {t.direction === 'up' ? (
                    <ArrowUpRight size={13} />
                  ) : t.direction === 'down' ? (
                    <ArrowDownRight size={13} />
                  ) : (
                    <Minus size={13} />
                  )}
                  <span>{t.delta}</span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Category, Size & Price Distribution Evolution Over Time */}
        {trendsData.monthly_category_trends?.length > 1 && (
          <div className="card" style={{ padding: '1.35rem 1.45rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
                  Category & Size Evolution Over Time
                </h3>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Tracking share shifts across recorded drop months.
                </span>
              </div>

              {/* View Switcher Pills */}
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <button
                  onClick={() => setActiveTab('category')}
                  className={`filter-pill ${activeTab === 'category' || activeTab === 'overview' ? 'active' : ''}`}
                  style={{ fontSize: '0.7rem', padding: '3px 10px' }}
                >
                  Category Revenue Share
                </button>
                <button
                  onClick={() => setActiveTab('size')}
                  className={`filter-pill ${activeTab === 'size' ? 'active' : ''}`}
                  style={{ fontSize: '0.7rem', padding: '3px 10px' }}
                >
                  Size Proportions
                </button>
                <button
                  onClick={() => setActiveTab('price')}
                  className={`filter-pill ${activeTab === 'price' ? 'active' : ''}`}
                  style={{ fontSize: '0.7rem', padding: '3px 10px' }}
                >
                  Price Brackets
                </button>
              </div>
            </div>

            {/* TAB: Category Revenue Share Evolution */}
            {(activeTab === 'category' || activeTab === 'overview') && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-light)', color: 'var(--text-muted)', textAlign: 'left' }}>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Month</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Outerwear</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Bottoms (Momentum)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Tops (Volume Anchor)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Total Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendsData.monthly_category_trends.map((m, idx) => {
                      const getCat = (cName) => (m.categories || []).find(c => c.category === cName) || { revenue_formatted: '₹0', revenue_share: 0, units: 0 }
                      const out = getCat('Outerwear')
                      const btm = getCat('Bottoms')
                      const tops = getCat('Tops')
                      return (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {m.month}
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem' }}>
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{out.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{out.revenue_share}% ({out.units} units)</span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', background: btm.revenue_share > 30 ? 'var(--mint-soft)' : 'transparent' }}>
                            <div style={{ fontWeight: 700, color: 'var(--forest-green)' }}>{btm.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--forest-dark)', fontWeight: 600 }}>
                              {btm.revenue_share}% ({btm.units} units)
                            </span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem' }}>
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{tops.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{tops.revenue_share}% ({tops.units} units)</span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            ₹{m.total_revenue?.toLocaleString()} ({m.total_units} units)
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* TAB: Size Distribution Evolution */}
            {activeTab === 'size' && trendsData.monthly_size_trends && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-light)', color: 'var(--text-muted)', textAlign: 'left' }}>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Month</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Size L (Top Size)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Size M</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Size S</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Size XL</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Total Units</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendsData.monthly_size_trends.map((m, idx) => {
                      const getSz = (sName) => (m.sizes || []).find(s => s.size === sName) || { units: 0, unit_share: 0 }
                      const l = getSz('L')
                      const med = getSz('M')
                      const s = getSz('S')
                      const xl = getSz('XL')
                      return (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {m.month}
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--forest-green)', background: 'var(--mint-soft)' }}>
                            {l.units} units ({l.unit_share}%)
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {med.units} units ({med.unit_share}%)
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {s.units} units ({s.unit_share}%)
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {xl.units} units ({xl.unit_share}%)
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700 }}>
                            {m.total_units} garments
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* TAB: Price Bracket Evolution */}
            {activeTab === 'price' && trendsData.monthly_price_trends && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-light)', color: 'var(--text-muted)', textAlign: 'left' }}>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Month</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Under ₹800 (Budget)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>₹800 – ₹1,499 (Sweet Spot)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>₹1,500+ (Premium)</th>
                      <th style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>Month Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendsData.monthly_price_trends.map((m, idx) => {
                      const getBrk = (bName) => (m.brackets || []).find(b => b.bracket === bName) || { revenue_formatted: '₹0', revenue_share: 0, units: 0 }
                      const b1 = getBrk('Under ₹800')
                      const b2 = getBrk('₹800 – ₹1,499')
                      const b3 = getBrk('₹1,500+')
                      return (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {m.month}
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem' }}>
                            <div>{b1.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{b1.revenue_share}% ({b1.units} units)</span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', background: 'var(--mint-soft)', fontWeight: 700, color: 'var(--forest-green)' }}>
                            <div>{b2.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--forest-dark)' }}>{b2.revenue_share}% ({b2.units} units)</span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem' }}>
                            <div>{b3.revenue_formatted}</div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{b3.revenue_share}% ({b3.units} units)</span>
                          </td>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700 }}>
                            ₹{m.total_revenue?.toLocaleString()}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ===================================================================== */}
      {/* SECTION 2: PREDICTIONS & RECOMMENDATIONS (NEW ML COMPONENT) */}
      {/* ===================================================================== */}
      <div style={{
        marginTop: '0.5rem',
        padding: '1.4rem',
        borderRadius: 'var(--radius-2xl)',
        background: '#FAFBF9',
        border: '1px solid rgba(6, 78, 53, 0.12)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '10px',
              background: 'var(--forest-green)', color: '#ffffff',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Sparkles size={17} />
            </div>
            <div>
              <h2 style={{
                fontSize: '1.2rem',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Predictions & Recommendations
              </h2>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Evaluated time-series forecasting, slow-moving inventory risk, and repeat-purchase dynamics.
              </span>
            </div>
          </div>
          <span style={{
            fontSize: '0.7rem',
            fontWeight: 700,
            background: 'var(--mint-soft)',
            color: 'var(--forest-green)',
            padding: '3px 10px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid rgba(6, 78, 53, 0.15)'
          }}>
            ML Decision Support
          </span>
        </div>

        {/* Prediction 1: Sales Forecasting Chart */}
        <SalesForecastChart forecastData={salesForecast} />

        {/* Prediction 2: Slow-Moving Inventory Risk Assessment */}
        {inventoryRisk && inventoryRisk.has_slow_moving_items && (inventoryRisk.risk_items || []).length > 0 && (
          <div className="card" style={{ padding: '1.4rem 1.5rem', borderLeft: '4px solid #F59E0B' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertTriangle size={18} color="#D97706" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', margin: 0 }}>
                    Slow-Selling Product Risk Assessment
                  </h3>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  Unsold items listed longer than comparable sold items in the same category.
                </span>
              </div>
              <span className="pill-badge" style={{ background: '#FEF3C7', color: '#92400E', fontWeight: 700 }}>
                {inventoryRisk.items_count} Available Items Flagged
              </span>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.4 }}>
              Completed Outerwear sales average <strong>1.5 days</strong> to sell out. The {inventoryRisk.items_count} currently available items below have remained in inventory significantly longer, tying up sourcing capital.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '0.85rem'
            }}>
              {(inventoryRisk.risk_items || []).map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.85rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-canvas)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)' }}>{item.product_id}</span>
                      <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#B45309', background: '#FDE68A', padding: '1px 6px', borderRadius: '4px' }}>
                        {item.days_on_hand} days on hand
                      </span>
                    </div>
                    <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                      {item.product_name}
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {item.category} • Size {item.size} • Listed {item.date_stocked}
                    </span>
                  </div>

                  <div style={{ marginTop: '0.75rem', paddingTop: '0.65rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--forest-green)' }}>
                      {item.retail_price_formatted}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      Benchmark: {item.category_avg_days_to_sale} days
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Prediction 3 & 4: Opportunities Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1rem'
        }}>
          {/* Category Opportunity */}
          {categoryOpportunities.length > 0 && (
            <div className="card" style={{ padding: '1.25rem 1.4rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.65rem' }}>
                <Layers size={18} color="var(--forest-green)" />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
                  Category Sourcing Opportunity
                </h4>
              </div>
              <p style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                {categoryOpportunities[0].finding}
              </p>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginBottom: '0.65rem', lineHeight: 1.4 }}>
                <strong>Evidence:</strong> {categoryOpportunities[0].evidence}
              </p>
              <div style={{ padding: '0.65rem 0.75rem', borderRadius: 'var(--radius-sm)', background: 'var(--mint-soft)', fontSize: '0.74rem', color: 'var(--forest-dark)' }}>
                <strong>Recommendation:</strong> {categoryOpportunities[0].suggested_action}
              </div>
            </div>
          )}

          {/* Repeat Purchase Behavioral Pattern */}
          {repeatInsights && repeatInsights.has_data && (
            <div className="card" style={{ padding: '1.25rem 1.4rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.65rem' }}>
                <ShoppingBag size={18} color="var(--forest-green)" />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
                  Repeat-Purchase Dynamics
                </h4>
              </div>
              <p style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                {repeatInsights.finding}
              </p>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginBottom: '0.65rem', lineHeight: 1.4 }}>
                <strong>Cycle interval:</strong> Repeat buyers make follow-up orders every ~{repeatInsights.avg_days_between_purchases} days.
              </p>
              <div style={{ padding: '0.65rem 0.75rem', borderRadius: 'var(--radius-sm)', background: 'var(--mint-soft)', fontSize: '0.74rem', color: 'var(--forest-dark)' }}>
                <strong>Recommendation:</strong> {repeatInsights.actionable_insight}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ===================================================================== */}
      {/* SECTION 3: RECOMMENDED ACTIONS */}
      {/* ===================================================================== */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h2 style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Recommended Actions
            </h2>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Structured, low-risk business decisions based on historical patterns and model forecasts.
            </span>
          </div>
          <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
            {recommendations.length} Actionable Recommendations
          </span>
        </div>

        {/* Grid of Structured 6-Field Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '1.15rem'
        }}>
          {recommendations.map((rec, idx) => (
            <div
              key={rec.id || idx}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '1.35rem 1.45rem',
                borderTop: '3px solid var(--forest-green)'
              }}
            >
              <div>
                {/* Header: Category Type + Confidence Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    color: 'var(--forest-green)',
                    letterSpacing: '0.05em'
                  }}>
                    {rec.category_type}
                  </span>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: rec.confidence === 'High' ? 'var(--forest-green)' : '#92400E',
                    background: rec.confidence === 'High' ? 'var(--mint-soft)' : '#FEF3C7',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-pill)'
                  }}>
                    {rec.confidence} Confidence
                  </span>
                </div>

                {/* 1. Title */}
                <h3 style={{
                  fontSize: '1.02rem',
                  fontWeight: 800,
                  fontFamily: 'var(--font-display)',
                  color: 'var(--text-primary)',
                  marginBottom: '0.65rem',
                  lineHeight: 1.3
                }}>
                  {rec.title}
                </h3>

                {/* 2. Reason */}
                <div style={{ marginBottom: '0.55rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Reason
                  </span>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', margin: 0, lineHeight: 1.4 }}>
                    {rec.reason}
                  </p>
                </div>

                {/* 3. Evidence */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Evidence
                  </span>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                    {rec.evidence}
                  </p>
                </div>
              </div>

              <div>
                {/* 4. Suggested Action */}
                <div style={{
                  padding: '0.75rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--mint-soft)',
                  border: '1px solid rgba(6, 78, 53, 0.1)',
                  marginBottom: '0.65rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.2rem' }}>
                    <Lightbulb size={13} color="var(--forest-green)" />
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--forest-green)' }}>
                      Suggested Next Step
                    </span>
                  </div>
                  <p style={{ fontSize: '0.76rem', color: 'var(--forest-dark)', margin: 0, lineHeight: 1.4 }}>
                    {rec.suggested_action}
                  </p>
                </div>

                {/* 5. Evaluation Metric */}
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <CheckCircle2 size={12} color="var(--forest-green)" style={{ flexShrink: 0 }} />
                  <span>
                    <strong>Evaluation metric:</strong> {rec.evaluation_metric}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
