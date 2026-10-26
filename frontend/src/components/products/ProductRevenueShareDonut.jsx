import React from 'react'
import DonutChart from '../common/DonutChart'

/**
 * ProductRevenueShareDonut — Donut chart showing product revenue share among top items and long tail
 * Matches Reference Image #7
 */
export default function ProductRevenueShareDonut({ bestSellersByRevenue = [], totalRevenueRaw }) {
  const products = bestSellersByRevenue || []
  const totalRev = totalRevenueRaw || products.reduce((acc, p) => acc + (p.revenue || 0), 0)

  // Top 4 individual items
  const topItems = products.slice(0, 4)
  const topRevSum = topItems.reduce((acc, p) => acc + (p.revenue || 0), 0)
  const othersRev = Math.max(0, totalRev - topRevSum)

  const donutData = topItems.map(p => {
    const pct = totalRev > 0 ? (p.revenue / totalRev) * 100 : 0
    return {
      label: p.product_name,
      value: p.revenue,
      formattedValue: p.revenue_formatted || `₹${p.revenue?.toLocaleString()}`,
      percentage: Math.round(pct * 10) / 10,
      sublabel: `${p.units_sold} sold`
    }
  })

  // Add "Others" long tail category if exists
  if (othersRev > 0) {
    const othersPct = totalRev > 0 ? (othersRev / totalRev) * 100 : 0
    donutData.push({
      label: 'Others',
      value: othersRev,
      formattedValue: `₹${Math.round(othersRev).toLocaleString()}`,
      percentage: Math.round(othersPct * 10) / 10,
      sublabel: 'Remaining catalog'
    })
  }

  // Format center label e.g. "₹17.7L"
  const formatCenterRevenue = (val) => {
    if (!val) return '₹0'
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
    if (val >= 1000) return `₹${Math.round(val / 1000)}K`
    return `₹${val.toLocaleString()}`
  }

  return (
    <DonutChart
      title="Product Revenue Share"
      subtitle="Top SKU revenue contribution vs catalog"
      data={donutData}
      centerPrimary={formatCenterRevenue(totalRev)}
      centerSecondary="Total Revenue"
      colors={['#064E35', '#0F6B4B', '#2D8A68', '#5AB892', '#CADCD2']}
    />
  )
}
