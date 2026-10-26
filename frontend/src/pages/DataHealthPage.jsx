import React, { useState, useEffect } from 'react'
import QualityGauge from '../components/health/QualityGauge'
import {
  Shield, Database, FileSpreadsheet,
  Clock, Layers
} from 'lucide-react'
import { getIngestionHistory, getIngestionStats } from '../services/api'

export default function DataHealthPage() {
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedBatch, setSelectedBatch] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      const [histRes, statsRes] = await Promise.all([
        getIngestionHistory(),
        getIngestionStats()
      ])
      if (histRes.ok) setHistory(histRes.data)
      if (statsRes.ok) setStats(statsRes.data)
      setLoading(false)
    }
    fetchData()
  }, [])

  const latestLog = history[0] || null

  if (loading) {
    return (
      <div className="skeleton" style={{ height: '240px', borderRadius: 'var(--radius-xl)' }} />
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Overview Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '1.25rem', alignItems: 'start' }}>
        {/* Quality Gauge */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1.75rem 2.25rem' }}>
          <QualityGauge score={latestLog?.quality_score || 94} />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.75rem', textAlign: 'center' }}>
            {latestLog ? `Last upload: ${latestLog.source_name}` : 'Sample Dataset Quality'}
          </p>
        </div>

        {/* Database Stats */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Database size={16} color="var(--forest-green)" />
            <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>Processed Records</span>
          </div>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.75rem' }}>
              {[
                { label: 'Products', value: stats.products, icon: Layers },
                { label: 'Sales', value: stats.sales, icon: FileSpreadsheet },
                { label: 'Content', value: stats.content_items, icon: FileSpreadsheet },
                { label: 'Inquiries', value: stats.inquiries, icon: FileSpreadsheet },
              ].map((s, i) => (
                <div key={i} style={{ padding: '0.75rem', background: '#F8F9F7', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.label}</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--forest-green)' }}>{s.value}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Ingestion History */}
      {history.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Clock size={16} color="var(--forest-green)" />
            <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>Audit Trail & History</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Uploaded</th>
                  <th>Rows</th>
                  <th>Valid</th>
                  <th>Quality</th>
                </tr>
              </thead>
              <tbody>
                {history.map((log, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{log.source_name}</td>
                    <td>{new Date(log.uploaded_at).toLocaleDateString()}</td>
                    <td>{log.total_rows}</td>
                    <td style={{ color: 'var(--forest-green)', fontWeight: 600 }}>{log.valid_rows}</td>
                    <td>
                      <span className="pill-badge green">
                        {log.quality_score}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
