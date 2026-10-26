import React, { useState, useEffect } from 'react'
import {
  History, CheckCircle2, ChevronDown, ChevronUp,
  FileSpreadsheet, AlertTriangle, ShieldCheck
} from 'lucide-react'
import { getIngestionHistory } from '../../services/api'

export default function UploadHistorySection() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const fetchHistory = async () => {
    setLoading(true)
    const res = await getIngestionHistory()
    setLoading(false)
    if (res.ok && Array.isArray(res.data)) {
      setHistory(res.data)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  if (history.length === 0 && !loading) return null

  return (
    <div style={{
      background: '#FFFFFF',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
      padding: '1.15rem 1.25rem',
      boxShadow: 'var(--shadow-card)'
    }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none'
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <History size={18} color="#245B43" />
          <h4 style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Previous Import History ({history.length})
          </h4>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
          <span style={{ fontSize: '0.74rem' }}>{expanded ? 'Hide history' : 'View past uploads'}</span>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {history.map((log) => {
            const dateStr = log.uploaded_at
              ? new Date(log.uploaded_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })
              : 'Past upload'

            return (
              <div
                key={log.batch_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 0.95rem',
                  background: '#F9FAF9',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(0, 0, 0, 0.04)',
                  flexWrap: 'wrap',
                  gap: '0.5rem'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <FileSpreadsheet size={18} color="#245B43" />
                  <div>
                    <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {log.source_name || 'Direct File Upload'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      Batch: {log.batch_id} &bull; {dateStr}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                    <strong>{log.valid_rows}</strong> valid / {log.total_rows} total rows
                  </span>

                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: '#065F46',
                    background: '#DDF2E3',
                    padding: '0.2rem 0.55rem',
                    borderRadius: 'var(--radius-pill)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}>
                    <ShieldCheck size={12} />
                    {log.quality_score}% Quality
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
