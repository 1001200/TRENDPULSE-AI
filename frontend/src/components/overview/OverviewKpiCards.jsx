import React from 'react'
import { BarChart3, BarChart2, Package, Tag, TrendingUp, TrendingDown } from 'lucide-react'

export default function OverviewKpiCards({ sales, period = 'all', monthLabel }) {
  // Extract values with defensive fallbacks
  const totalSalesFormatted = sales?.total_sales_formatted || '₹0'
  const totalOrders = sales?.total_orders ?? 0
  const totalUnitsSold = sales?.units_sold ?? 0
  const aovFormatted = sales?.aov_formatted || '₹0'

  const overallGrowth = sales?.growth_pct ?? null
  const overallPositive = sales?.growth_is_positive ?? (overallGrowth !== null && overallGrowth >= 0)

  // Subtexts based on reporting period
  let salesSubtext = 'All-Time Cumulative Revenue'
  let ordersSubtext = 'All-Time Completed Orders'
  let aovSubtext = 'Avg Spend / Order'
  let unitsSubtext = 'Clothing Items Sold'
  let periodBadge = 'All-Time'

  if (period === '7d' || period === 'last_7_days') {
    salesSubtext = 'Last 7 Days Revenue'
    ordersSubtext = 'Orders in Last 7 Days'
    aovSubtext = 'Avg Spend / Order (7d)'
    unitsSubtext = 'Garments (Last 7 Days)'
    periodBadge = '7 Days'
  } else if (period === '30d' || period === 'last_30_days') {
    salesSubtext = 'Last 30 Days Revenue'
    ordersSubtext = 'Orders in Last 30 Days'
    aovSubtext = 'Avg Spend / Order (30d)'
    unitsSubtext = 'Garments (Last 30 Days)'
    periodBadge = '30 Days'
  } else if (period === 'monthly' || period === 'this_month' || (typeof period === 'string' && (period.startsWith('month') || period.includes('-')))) {
    const mName = monthLabel || sales?.this_month?.month_name || 'This Month'
    salesSubtext = `${mName} Revenue`
    ordersSubtext = `Orders in ${mName}`
    aovSubtext = `Avg Spend / Order (${mName})`
    unitsSubtext = `Garments in ${mName}`
    periodBadge = 'Monthly'
  }

  return (
    <div className="kpi-grid">
      {/* Card 1: Solid Deep Forest Green Hero Card — Total Sales */}
      <div className="kpi-card-ref hero-green">
        <div className="kpi-top-row">
          <div className="kpi-icon-bubble">
            <BarChart3 size={18} strokeWidth={2.4} />
          </div>
          {overallGrowth !== null && overallGrowth !== 0 ? (
            <span className="pill-badge forest" title="Revenue trajectory across selected period">
              {overallPositive ? `+${overallGrowth}%` : `${overallGrowth}%`}
            </span>
          ) : (
            <span className="pill-badge forest">
              {periodBadge}
            </span>
          )}
        </div>
        <div>
          <span className="kpi-label">Total Sales</span>
          <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
            <span className="kpi-value">{totalSalesFormatted}</span>
            <span className="kpi-subtext">{salesSubtext}</span>
          </div>
        </div>
      </div>

      {/* Card 2: White Card — Total Orders */}
      <div className="kpi-card-ref white">
        <div className="kpi-top-row">
          <div className="kpi-icon-bubble">
            <BarChart2 size={18} strokeWidth={2.2} />
          </div>
          <span className="pill-badge green">
            Completed
          </span>
        </div>
        <div>
          <span className="kpi-label">Total Orders</span>
          <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
            <span className="kpi-value">{totalOrders.toLocaleString()}</span>
            <span className="kpi-subtext">{ordersSubtext}</span>
          </div>
        </div>
      </div>

      {/* Card 3: White Card — Total Units Sold */}
      <div className="kpi-card-ref white">
        <div className="kpi-top-row">
          <div className="kpi-icon-bubble">
            <Package size={18} strokeWidth={2.2} />
          </div>
          <span className="pill-badge green">
            Garments
          </span>
        </div>
        <div>
          <span className="kpi-label">Total Units Sold</span>
          <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
            <span className="kpi-value">{totalUnitsSold.toLocaleString()}</span>
            <span className="kpi-subtext">{unitsSubtext}</span>
          </div>
        </div>
      </div>

      {/* Card 4: White Card — Average Order Value */}
      <div className="kpi-card-ref white">
        <div className="kpi-top-row">
          <div className="kpi-icon-bubble">
            <Tag size={18} strokeWidth={2.2} />
          </div>
          <span className="pill-badge green">
            AOV
          </span>
        </div>
        <div>
          <span className="kpi-label">Average Order Value</span>
          <div className="kpi-value-row" style={{ marginTop: '0.35rem' }}>
            <span className="kpi-value">{aovFormatted}</span>
            <span className="kpi-subtext">{aovSubtext}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
