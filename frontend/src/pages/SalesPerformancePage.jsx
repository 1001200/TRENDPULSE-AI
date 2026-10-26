import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  DollarSign,
  ShoppingBag,
  Package,
  BarChart3,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ListFilter
} from 'lucide-react'
import { getInsights, getIngestionStats } from '../services/api'
import MonthlySalesChart from '../components/sales/MonthlySalesChart'
import WeekdaySalesChart from '../components/sales/WeekdaySalesChart'

export default function SalesPerformancePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('all')

  // Table pagination state
  const [tablePage, setTablePage] = useState(1)
  const [showAllRows, setShowAllRows] = useState(false)
  const rowsPerPage = 10

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
      console.error('Failed to fetch sales performance data:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData(period)
    setTablePage(1)
  }, [period])

  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod)
  }

  // Active period display label
  const periodLabelMap = {
    all: 'All Time',
    this_month: 'This Month',
    last_month: 'Last Month',
    '3m': 'Last 3 Months',
    '6m': 'Last 6 Months'
  }
  const activePeriodLabel = periodLabelMap[period] || 'All Time'

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="skeleton" style={{ width: '220px', height: '28px', borderRadius: 'var(--radius-md)', marginBottom: '6px' }} />
            <div className="skeleton" style={{ width: '320px', height: '16px', borderRadius: 'var(--radius-sm)' }} />
          </div>
          <div className="skeleton" style={{ width: '360px', height: '36px', borderRadius: 'var(--radius-pill)' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: '125px', borderRadius: 'var(--radius-xl)' }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: '300px', borderRadius: 'var(--radius-xl)' }} />
      </div>
    )
  }

  if (!data?.sales) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-display)', margin: 0 }}>
              Sales Performance
            </h2>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Track revenue, orders, and sales over time.
            </span>
          </div>
        </div>
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No sales data available. Please upload sales data or load sample data.
        </div>
      </div>
    )
  }

  const { sales } = data

  // Prepare Daily Sales Breakdown rows (newest first)
  const allDailyRows = sales.daily_sales ? [...sales.daily_sales].reverse() : []
  const totalDailyRecords = allDailyRows.length
  const totalPages = Math.max(1, Math.ceil(totalDailyRecords / rowsPerPage))
  const displayedDailyRows = showAllRows
    ? allDailyRows
    : allDailyRows.slice((tablePage - 1) * rowsPerPage, tablePage * rowsPerPage)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* 1. Header with Title, Period Badge & Polished Segmented Control */}
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
              Sales Performance
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
            Track revenue, orders, and sales over time.
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

      {/* 2. Redesigned 4-Metric Responsive KPI Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(215px, 1fr))',
        gap: '1rem'
      }}>
        {/* Metric 1: Total Sales (Forest Green Hero Card) */}
        <div className="kpi-card-ref hero-green">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <DollarSign size={18} strokeWidth={2.5} />
            </div>
            {sales.growth_pct !== undefined && sales.growth_pct !== 0 ? (
              <span className="pill-badge forest" title="Revenue trajectory vs prior period">
                {sales.growth_is_positive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {sales.growth_is_positive ? `+${Math.abs(sales.growth_pct)}%` : `-${Math.abs(sales.growth_pct)}%`}
              </span>
            ) : (
              <span className="pill-badge forest">
                {activePeriodLabel}
              </span>
            )}
          </div>
          <div>
            <span className="kpi-label">Total Sales</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{sales.total_sales_formatted || '₹0'}</span>
              <span className="kpi-subtext">
                {period === 'all' ? 'All-time cumulative revenue' : `Revenue in ${activePeriodLabel}`}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 2: Total Orders */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <ShoppingBag size={18} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              Completed
            </span>
          </div>
          <div>
            <span className="kpi-label">Total Orders</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{(sales.total_orders ?? 0).toLocaleString()}</span>
              <span className="kpi-subtext">
                {period === 'all' ? 'All-time verified orders' : `Orders in ${activePeriodLabel}`}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 3: Units Sold */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <Package size={18} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              Garments
            </span>
          </div>
          <div>
            <span className="kpi-label">Units Sold</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{(sales.units_sold ?? 0).toLocaleString()}</span>
              <span className="kpi-subtext">Clothing items sold</span>
            </div>
          </div>
        </div>

        {/* Metric 4: Average Order Value */}
        <div className="kpi-card-ref white">
          <div className="kpi-top-row">
            <div className="kpi-icon-bubble">
              <BarChart3 size={18} />
            </div>
            <span className="pill-badge green" style={{ background: 'var(--mint-soft)', color: 'var(--forest-green)' }}>
              AOV
            </span>
          </div>
          <div>
            <span className="kpi-label">Average Order Value</span>
            <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
              <span className="kpi-value">{sales.aov_formatted || '₹0'}</span>
              <span className="kpi-subtext">Per completed checkout</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Charts Section: Monthly Sales Trajectory Line Graph & Weekday Sales Bar Chart */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        gap: '1.25rem',
        alignItems: 'start'
      }}>
        {/* Monthly Sales Trajectory SVG Line Graph */}
        <MonthlySalesChart
          salesByMonth={sales.sales_by_month}
          insightText={sales.month_insight}
          period={period}
        />

        {/* Sales by Day of Week Horizontal Bar Chart */}
        <WeekdaySalesChart
          salesByDay={sales.sales_by_day}
          insightText={sales.day_insight}
        />
      </div>

      {/* 4. Compact Sales Spikes & Drops Section */}
      <div className="card" style={{ padding: '1.35rem 1.5rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.9rem',
          flexWrap: 'wrap',
          gap: '0.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sales Spikes & Drops
            </h3>
            {sales.spikes_and_drops?.length > 0 && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: 'var(--forest-green)',
                background: 'var(--mint-soft)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(6, 78, 53, 0.12)'
              }}>
                {sales.spikes_and_drops.length} {sales.spikes_and_drops.length === 1 ? 'event' : 'events'}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Statistically significant daily deviations for {activePeriodLabel}
          </span>
        </div>

        {sales.spikes_and_drops && sales.spikes_and_drops.length > 0 ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '0.85rem'
          }}>
            {sales.spikes_and_drops.map((event, idx) => {
              const isSpike = event.type === 'SPIKE'
              return (
                <div
                  key={idx}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-lg)',
                    background: isSpike ? 'rgba(6, 78, 53, 0.04)' : 'rgba(229, 72, 77, 0.04)',
                    border: isSpike ? '1px solid rgba(6, 78, 53, 0.15)' : '1px solid rgba(229, 72, 77, 0.15)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem'
                  }}
                >
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '10px',
                    background: isSpike ? 'var(--mint-soft)' : '#FDE8E8',
                    color: isSpike ? 'var(--forest-green)' : '#D32F2F',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {isSpike ? <ArrowUpRight size={16} strokeWidth={2.5} /> : <ArrowDownRight size={16} strokeWidth={2.5} />}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.2rem' }}>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 800,
                        letterSpacing: '0.04em',
                        textTransform: 'uppercase',
                        color: isSpike ? 'var(--forest-green)' : '#D32F2F'
                      }}>
                        {isSpike ? `+${event.pct_change}% Spike` : `${event.pct_change}% Drop`}
                      </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>• {event.date}</span>
                    </div>
                    <span style={{
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      display: 'block',
                      lineHeight: 1.35,
                      marginBottom: '0.25rem'
                    }}>
                      {event.headline}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Recorded <strong style={{ color: 'var(--text-primary)' }}>{event.sales_formatted}</strong> vs {event.baseline_formatted} baseline.
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div style={{
            padding: '1.25rem',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.78rem',
            background: '#FAFBF9',
            borderRadius: 'var(--radius-md)'
          }}>
            No significant sales spikes or drops detected within this reporting period.
          </div>
        )}
      </div>

      {/* 5. Daily Sales Breakdown Table */}
      {sales.daily_sales && sales.daily_sales.length > 0 && (
        <div className="card" style={{ padding: '1.35rem 1.5rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1rem',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: 800,
                  fontFamily: 'var(--font-display)',
                  color: 'var(--text-primary)',
                  margin: 0
                }}>
                  Daily Sales Breakdown
                </h3>
                <span style={{
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  color: 'var(--forest-green)',
                  background: 'var(--mint-soft)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-pill)',
                  border: '1px solid rgba(6, 78, 53, 0.12)'
                }}>
                  {totalDailyRecords} {totalDailyRecords === 1 ? 'record' : 'records'}
                </span>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                Itemized transaction history matching {activePeriodLabel}
              </span>
            </div>

            {/* View All / Toggle Controls */}
            {totalDailyRecords > rowsPerPage && (
              <button
                onClick={() => setShowAllRows(!showAllRows)}
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  color: 'var(--forest-green)',
                  background: 'var(--mint-soft)',
                  border: '1px solid rgba(6, 78, 53, 0.15)',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-pill)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {showAllRows ? `Show ${rowsPerPage} per page` : `View All (${totalDailyRecords})`}
              </button>
            )}
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--mint-soft)' }}>
                  <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '0.74rem', fontWeight: 700, color: 'var(--forest-green)', borderTopLeftRadius: 'var(--radius-md)', borderBottomLeftRadius: 'var(--radius-md)' }}>Date</th>
                  <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '0.74rem', fontWeight: 700, color: 'var(--forest-green)' }}>Day</th>
                  <th style={{ padding: '8px 14px', textAlign: 'center', fontSize: '0.74rem', fontWeight: 700, color: 'var(--forest-green)' }}>Orders</th>
                  <th style={{ padding: '8px 14px', textAlign: 'center', fontSize: '0.74rem', fontWeight: 700, color: 'var(--forest-green)' }}>Units</th>
                  <th style={{ padding: '8px 14px', textAlign: 'right', fontSize: '0.74rem', fontWeight: 700, color: 'var(--forest-green)', borderTopRightRadius: 'var(--radius-md)', borderBottomRightRadius: 'var(--radius-md)' }}>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {displayedDailyRows.map((d, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid #F0F2EF',
                      transition: 'background 0.1s ease'
                    }}
                  >
                    <td style={{ padding: '10px 14px', fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                      {d.display_date || d.date}
                    </td>
                    <td style={{ padding: '10px 14px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {d.day_name}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {d.orders}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {d.units}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 700, fontSize: '0.82rem', fontFamily: 'var(--font-display)', color: 'var(--forest-green)' }}>
                      {d.revenue_formatted}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination bar if pagination is active */}
          {!showAllRows && totalPages > 1 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '1rem',
              paddingTop: '0.75rem',
              borderTop: '1px solid #F0F2EF'
            }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Showing {(tablePage - 1) * rowsPerPage + 1} - {Math.min(tablePage * rowsPerPage, totalDailyRecords)} of {totalDailyRecords} records
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <button
                  disabled={tablePage === 1}
                  onClick={() => setTablePage(p => Math.max(1, p - 1))}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    padding: '4px 10px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    borderRadius: 'var(--radius-pill)',
                    border: '1px solid var(--border-subtle)',
                    background: tablePage === 1 ? '#F9FAF8' : '#ffffff',
                    color: tablePage === 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: tablePage === 1 ? 'not-allowed' : 'pointer'
                  }}
                >
                  <ChevronLeft size={14} /> Previous
                </button>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--forest-green)', padding: '0 4px' }}>
                  {tablePage} / {totalPages}
                </span>
                <button
                  disabled={tablePage === totalPages}
                  onClick={() => setTablePage(p => Math.min(totalPages, p + 1))}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    padding: '4px 10px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    borderRadius: 'var(--radius-pill)',
                    border: '1px solid var(--border-subtle)',
                    background: tablePage === totalPages ? '#F9FAF8' : '#ffffff',
                    color: tablePage === totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: tablePage === totalPages ? 'not-allowed' : 'pointer'
                  }}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
