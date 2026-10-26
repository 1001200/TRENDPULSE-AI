import React from 'react'
import DonutChart from '../common/DonutChart'

/**
 * SizeDonutChart — Donut chart showing the share of apparel units sold by size (S, M, L, XL, etc.)
 * Provides clear part-to-whole view of customer size demand
 */
export default function SizeDonutChart({ salesBySize = [], totalUnits = 0 }) {
  const sizeList = salesBySize || []
  const calcTotalUnits = totalUnits || sizeList.reduce((acc, s) => acc + (s.units_sold || 0), 0)

  // Map into DonutChart data structure
  const donutData = sizeList.map(s => {
    const pct = calcTotalUnits > 0 ? (s.units_sold / calcTotalUnits) * 100 : (s.pct_of_sales || 0)
    return {
      label: `Size ${s.size}`,
      value: s.units_sold,
      formattedValue: `${s.units_sold?.toLocaleString()} units`,
      percentage: Math.round(pct * 10) / 10,
      sublabel: s.revenue_formatted || `₹${s.revenue?.toLocaleString()}`
    }
  })

  // Format center total
  const centerValue = calcTotalUnits >= 1000
    ? `${calcTotalUnits.toLocaleString()}`
    : `${calcTotalUnits}`

  return (
    <DonutChart
      title="Size Share of Demand"
      subtitle="Unit volume distribution across apparel sizes"
      data={donutData}
      centerPrimary={centerValue}
      centerSecondary="Garments Sold"
      colors={['#064E35', '#0F6B4B', '#2D8A68', '#5AB892', '#CADCD2', '#E2ECE7']}
    />
  )
}
