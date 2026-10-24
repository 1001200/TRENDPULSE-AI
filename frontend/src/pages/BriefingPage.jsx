import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Download, Sparkles, AlertCircle, ArrowRight, Loader } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import ExecutiveMemo from '../components/ai/ExecutiveMemo'
import { exportAPI } from '../api/client'
import { formatCurrency, formatPercent, formatNumber } from '../utils/formatters'

export default function BriefingPage() {
  const navigate = useNavigate()
  const { dataset, activeDatasetId, result, diagnosis, diagnosisLoading, loading } = useStore()

  const handleExportCSV = async () => {
    if (!activeDatasetId) return
    try {
      const res = await exportAPI.cleanCSV(activeDatasetId)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `trendpulse_clean_${dataset?.filename || activeDatasetId}.csv`
      a.click()
    } catch (e) {
      alert('Export failed: ' + e.message)
    }
  }

  if (loading && !result) {
    return (
      <div className="page-container flex-center" style={{ minHeight: '65vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={38} className="spin text-indigo" strokeWidth={2.5} />
          <p className="text-muted mt-md font-heading" style={{ fontWeight: 800, textTransform: 'uppercase' }}>
            SYNTHESIZING EXECUTIVE BRIEFING…
          </p>
        </div>
      </div>
    )
  }

  const r = result || {}
  const economics = r.fashion_economics?.unit_economics?.overall_metrics || {}
  const apparel = r.apparel_intelligence || {}
  const grossRev = economics.total_revenue || apparel.total_apparel_revenue || 0
  const totalOrders = r.rows_received || dataset?.rows_received || 0
  const marginPct = economics.gross_margin_percentage || 57.0

  return (
    <div className="page-container">
      {/* Top Store Status Bar */}
      <div className="card mb-md animate-in card-glyph-circle" style={{ padding: '20px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase' }}>
                {dataset?.filename || 'Active Apparel Catalog'}
              </h2>
              <span className="badge badge--emerald">STORE #{activeDatasetId}</span>
              <span className="badge badge--indigo">60-SEC CEO MEMO</span>
            </div>
            <div className="text-sm" style={{ fontWeight: 700, color: 'var(--bauhaus-black)' }}>
              {formatNumber(totalOrders)} ORDERS PROCESSED • GROSS SALES: <strong className="text-indigo">{formatCurrency(grossRev)}</strong> • STORE MARGIN: <strong className="text-rose">{formatPercent(marginPct)}</strong>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-sm btn-yellow" onClick={() => navigate('/copilot')}>
              <Sparkles size={14} strokeWidth={2.5} /> OPEN COPILOT
            </button>
            <button className="btn btn-sm btn-ghost" onClick={handleExportCSV}>
              <Download size={14} strokeWidth={2.5} /> EXPORT CLEAN CSV
            </button>
          </div>
        </div>
      </div>

      {/* 60-Second CEO Briefing Memo */}
      <ExecutiveMemo
        diagnosis={diagnosis}
        loading={diagnosisLoading}
        onAskCopilot={(prompt) => {
          navigate('/copilot', { state: { initialPrompt: prompt } })
        }}
      />
    </div>
  )
}
