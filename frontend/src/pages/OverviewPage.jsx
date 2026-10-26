import React, { useState, useEffect } from 'react'
import { TrendingUp, Database } from 'lucide-react'
import { getInsights, loadSampleData, getIngestionStats } from '../services/api'
import OverviewKpiCards from '../components/overview/OverviewKpiCards'
import SalesOverviewChart from '../components/overview/SalesOverviewChart'
import SalesByCategoryChart from '../components/overview/SalesByCategoryChart'
import SalesComparisonCard from '../components/overview/SalesComparisonCard'
import TopSellingCategoriesCard from '../components/overview/TopSellingCategoriesCard'

export default function OverviewPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [hasData, setHasData] = useState(false)
  const [loadingSample, setLoadingSample] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState('all') // '7d' | '30d' | 'monthly' | 'all'
  const [selectedMonthKey, setSelectedMonthKey] = useState('')
  const [selectedMonthLabel, setSelectedMonthLabel] = useState('')

  const fetchData = async (periodToFetch = selectedPeriod, customMonthKey = selectedMonthKey) => {
    setLoading(true)
    try {
      const statsRes = await getIngestionStats()
      if (statsRes.ok && statsRes.data.has_data) {
        setHasData(true)
        const queryPeriod = (periodToFetch === 'monthly' && customMonthKey) ? customMonthKey : periodToFetch
        const insightsRes = await getInsights({ period: queryPeriod })
        if (insightsRes.ok && insightsRes.data.has_data) {
          setData(insightsRes.data)
          // Set default month key if monthly was chosen and key not set
          const months = insightsRes.data.sales?.sales_by_month || []
          if (months.length > 0 && !customMonthKey) {
            const latestMonth = months[months.length - 1]
            setSelectedMonthKey(latestMonth.sort_key || latestMonth.month)
            setSelectedMonthLabel(latestMonth.month)
          }
        }
      } else {
        setHasData(false)
      }
    } catch (err) {
      console.error('Failed to fetch overview data:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData('all')
  }, [])

  const handlePeriodChange = (newPeriod) => {
    setSelectedPeriod(newPeriod)
    if (newPeriod === 'monthly') {
      const months = data?.sales?.sales_by_month || []
      const latestMonth = months.length > 0 ? months[months.length - 1] : null
      const mKey = latestMonth?.sort_key || latestMonth?.month || ''
      setSelectedMonthKey(mKey)
      setSelectedMonthLabel(latestMonth?.month || 'This Month')
      fetchData(newPeriod, mKey)
    } else {
      fetchData(newPeriod)
    }
  }

  const handleMonthChange = (monthKey) => {
    setSelectedMonthKey(monthKey)
    const months = data?.sales?.sales_by_month || []
    const match = months.find(m => (m.sort_key === monthKey || m.month === monthKey))
    if (match) {
      setSelectedMonthLabel(match.month)
    }
    fetchData('monthly', monthKey)
  }

  const handleLoadSample = async () => {
    setLoadingSample(true)
    const res = await loadSampleData()
    if (res.ok) {
      await fetchData(selectedPeriod)
    }
    setLoadingSample(false)
  }

  // Determine active period label for header badge
  let activePeriodLabel = 'All Time'
  if (selectedPeriod === '7d') activePeriodLabel = 'Last 7 Days'
  else if (selectedPeriod === '30d') activePeriodLabel = 'Last 30 Days'
  else if (selectedPeriod === 'monthly') activePeriodLabel = selectedMonthLabel || 'Monthly'

  // Available months sorted newest first for dropdown
  const availableMonths = [...(data?.sales?.sales_by_month || [])].reverse()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Overview Top Header with Title and Reporting Period Selector */}
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
              Overview
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
            Real-time sales performance and clothing retail metrics
          </span>
        </div>

        {/* Reporting Period Selector (Matching Sales Overview Chart date pills style) */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          flexWrap: 'wrap'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-segment)',
            padding: '3px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid rgba(18, 38, 28, 0.05)'
          }}>
            {[
              { id: '7d', label: 'Last 7 Days' },
              { id: '30d', label: 'Last 30 Days' },
              { id: 'monthly', label: 'Monthly' },
              { id: 'all', label: 'All Time' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => handlePeriodChange(item.id)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 'var(--radius-pill)',
                  fontSize: '0.72rem',
                  fontWeight: selectedPeriod === item.id ? 700 : 500,
                  color: selectedPeriod === item.id ? '#ffffff' : 'var(--text-secondary)',
                  background: selectedPeriod === item.id ? 'var(--forest-green)' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  boxShadow: selectedPeriod === item.id ? '0 2px 6px rgba(6, 78, 53, 0.2)' : 'none'
                }}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Month selector dropdown if Monthly is active and data has historical months */}
          {selectedPeriod === 'monthly' && availableMonths.length > 0 && (
            <select
              value={selectedMonthKey}
              onChange={(e) => handleMonthChange(e.target.value)}
              className="select-pill"
              title="Review specific calendar month"
            >
              {availableMonths.map(m => (
                <option key={m.sort_key || m.month} value={m.sort_key || m.month}>
                  {m.month}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Quick Banner if no data is present in database */}
      {!hasData && !loading && (
        <div style={{
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
          background: '#ffffff',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--mint-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--forest-green)' }}>
              <TrendingUp size={16} />
            </div>
            <div>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>No Sales Data Loaded</span>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Load sample clothing resale data or upload your sales records to view analytics.</span>
            </div>
          </div>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleLoadSample}
            disabled={loadingSample}
          >
            <Database size={13} />
            <span>{loadingSample ? 'Loading Data...' : 'Load Sample Data'}</span>
          </button>
        </div>
      )}

      {/* MAIN TWO-COLUMN DASHBOARD GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.75fr 1.15fr',
        gap: '1.25rem',
        alignItems: 'start',
        opacity: loading ? 0.75 : 1,
        transition: 'opacity 0.2s ease'
      }}>

        {/* ================= LEFT COLUMN ================= */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* 1. 2x2 KPI CARDS (Total Sales, Total Orders, Average Order Value, Total Units Sold) */}
          <OverviewKpiCards 
            sales={data?.sales} 
            period={selectedPeriod === 'monthly' && selectedMonthKey ? selectedMonthKey : selectedPeriod}
            monthLabel={selectedMonthLabel}
          />

          {/* 2. SALES OVERVIEW LINE + BAR COMBO GRAPH */}
          <SalesOverviewChart 
            timelineData={data?.sales?.timeline} 
            loading={loading}
            externalPeriod={selectedPeriod}
          />

          {/* 3. SALES COMPARISON CARD (This Month vs Last Month, This Week vs Last Week) */}
          <SalesComparisonCard 
            comparisonData={data?.sales?.sales_comparison}
          />
        </div>

        {/* ================= RIGHT COLUMN ================= */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* 1. SALES BY CLOTHING CATEGORY DONUT CHART */}
          <SalesByCategoryChart 
            categories={data?.products?.sales_by_category}
            totalSalesRaw={data?.sales?.total_sales_raw}
            totalUnitsSold={data?.sales?.units_sold}
          />

          {/* 2. TOP SELLING CATEGORIES CLEAN PROGRESS BARS */}
          <TopSellingCategoriesCard 
            categories={data?.products?.sales_by_category}
            totalSalesRaw={data?.sales?.total_sales_raw}
            totalUnitsSold={data?.sales?.units_sold}
          />
        </div>

      </div>
    </div>
  )
}
