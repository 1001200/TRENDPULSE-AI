import React from 'react'
import DonutChart from '../common/DonutChart'

/**
 * SalesByCategoryChart — Donut chart showing revenue share by clothing category
 * Matches Reference Image #3
 */
export default function SalesByCategoryChart({ categories = [], totalSalesRaw, totalUnitsSold }) {
  const catList = categories || []
  const totalRev = totalSalesRaw || catList.reduce((acc, c) => acc + (c.revenue || 0), 0)

  // Format center total revenue e.g. "₹17.7L" or "₹1.8Cr"
  const formatCenterRevenue = (val) => {
    if (!val) return '₹0'
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
    if (val >= 1000) return `₹${Math.round(val / 1000)}K`
    return `₹${val.toLocaleString()}`
  }

  const donutData = catList.map(c => ({
    label: c.category,
    value: c.revenue || 0,
    formattedValue: c.revenue_formatted || `₹${c.revenue?.toLocaleString()}`,
    percentage: c.pct_of_total || (totalRev > 0 ? Math.round((c.revenue / totalRev) * 1000) / 10 : 0),
    count: c.units_sold
  }))

  return (
    <DonutChart
      title="Sales by Clothing Category"
      subtitle="Revenue share across categories"
      data={donutData}
      centerPrimary={formatCenterRevenue(totalRev)}
      centerSecondary="Total Revenue"
      colors={['#064E35', '#0F6B4B', '#2D8A68', '#5AB892', '#A3DAC3']}
    />
  )
}
