import React, { useState } from 'react'
import {
  CheckCircle2, AlertTriangle, AlertCircle, Sparkles,
  Check, X, Edit3, ArrowRight, ShieldCheck, Filter,
  Layers, Info, Trash2
} from 'lucide-react'

export default function QualityReviewSection({
  summary = {},
  issues = [],
  onAcceptIssue,
  onExcludeIssue,
  onEditCell,
  onBulkAction,
  disabled = false
}) {
  const [activeTab, setActiveTab] = useState('all') // all, duplicates, missing, invalid, formatting
  const [editingIssueId, setEditingIssueId] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [confirmModal, setConfirmModal] = useState(null) // { action, label, count }

  // Filter issues by active tab
  const filteredIssues = issues.filter((iss) => {
    if (activeTab === 'all') return true
    if (activeTab === 'duplicates') {
      return iss.issue_type === 'duplicate_confirmed' || iss.issue_type === 'duplicate_potential'
    }
    if (activeTab === 'missing') {
      return iss.issue_type === 'missing_value'
    }
    if (activeTab === 'invalid') {
      return iss.issue_type === 'invalid_value'
    }
    if (activeTab === 'formatting') {
      return iss.issue_type === 'formatting_cleaned'
    }
    return true
  })

  const countByType = {
    duplicates: issues.filter(i => i.issue_type.includes('duplicate')).length,
    missing: issues.filter(i => i.issue_type === 'missing_value').length,
    invalid: issues.filter(i => i.issue_type === 'invalid_value').length,
    formatting: issues.filter(i => i.issue_type === 'formatting_cleaned').length,
  }

  const handleStartEdit = (iss) => {
    setEditingIssueId(iss.id)
    setEditValue(iss.suggested_value !== 'NULL' ? iss.suggested_value : '')
  }

  const handleSaveEdit = (iss) => {
    onEditCell?.(iss.row_id, iss.column, editValue)
    onAcceptIssue?.(iss.id)
    setEditingIssueId(null)
  }

  const handleTriggerBulk = (action, label, count) => {
    if (action === 'exclude_confirmed_duplicates') {
      setConfirmModal({ action, label, count })
    } else {
      onBulkAction?.(action)
    }
  }

  const executeConfirmedBulk = () => {
    if (confirmModal) {
      onBulkAction?.(confirmModal.action)
      setConfirmModal(null)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* 1. Summary Metrics Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '0.75rem'
      }}>
        {/* Total Records */}
        <div style={{
          background: '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {summary.total_rows || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Total Records
          </div>
        </div>

        {/* Ready For Import */}
        <div style={{
          background: '#DDF2E3',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(36, 91, 67, 0.2)',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#245B43' }}>
            {summary.valid_rows || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#1B4533', fontWeight: 700 }}>
            Ready to Import
          </div>
        </div>

        {/* Confirmed Duplicates */}
        <div style={{
          background: summary.confirmed_duplicates > 0 ? '#FFEFEF' : '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid ' + (summary.confirmed_duplicates > 0 ? 'rgba(217, 45, 32, 0.25)' : 'var(--border-subtle)'),
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{
            fontSize: '1.35rem',
            fontWeight: 800,
            color: summary.confirmed_duplicates > 0 ? 'var(--badge-red-text)' : 'var(--text-primary)'
          }}>
            {summary.confirmed_duplicates || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Confirmed Dupes
          </div>
        </div>

        {/* Potential Duplicates */}
        <div style={{
          background: summary.potential_duplicates > 0 ? '#FEF8EB' : '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid ' + (summary.potential_duplicates > 0 ? 'rgba(217, 119, 6, 0.25)' : 'var(--border-subtle)'),
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{
            fontSize: '1.35rem',
            fontWeight: 800,
            color: summary.potential_duplicates > 0 ? '#B45309' : 'var(--text-primary)'
          }}>
            {summary.potential_duplicates || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Potential Dupes
          </div>
        </div>

        {/* Missing Values */}
        <div style={{
          background: '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {summary.missing_values || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Missing Values
          </div>
        </div>

        {/* Formatting Cleaned */}
        <div style={{
          background: '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {summary.formatting_cleaned || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Safe Auto-Cleans
          </div>
        </div>

        {/* Data Quality Score */}
        <div style={{
          background: '#F0FDF4',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(22, 163, 74, 0.25)',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#15803D' }}>
            {summary.quality_score || 100}%
          </div>
          <div style={{ fontSize: '0.72rem', color: '#166534', fontWeight: 700 }}>
            Quality Health Score
          </div>
        </div>
      </div>

      {/* 2. Review Header & Filter Tabs */}
      <div style={{
        background: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        padding: '1.25rem',
        boxShadow: 'var(--shadow-card)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1rem',
          paddingBottom: '0.85rem',
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)'
        }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Data Quality Inspection & Review
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
              TrendPulse identified these data quality items. Review suggestions before importing.
            </p>
          </div>

          {/* Bulk Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            {summary.formatting_cleaned > 0 && (
              <button
                type="button"
                className="btn-mint-outline"
                onClick={() => handleTriggerBulk('accept_all_safe', 'Accept All Safe Formatting', summary.formatting_cleaned)}
                disabled={disabled}
              >
                <Check size={14} />
                <span>Accept Safe Formatting ({summary.formatting_cleaned})</span>
              </button>
            )}

            {summary.confirmed_duplicates > 0 && (
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={() => handleTriggerBulk('exclude_confirmed_duplicates', 'Exclude Confirmed Duplicates', summary.confirmed_duplicates)}
                disabled={disabled}
              >
                <Trash2 size={13} />
                <span>Exclude Confirmed Dupes ({summary.confirmed_duplicates})</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          overflowX: 'auto',
          paddingBottom: '0.5rem',
          marginBottom: '1rem'
        }}>
          <button
            type="button"
            className={`review-filter-tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All Issues ({issues.length})
          </button>
          <button
            type="button"
            className={`review-filter-tab ${activeTab === 'duplicates' ? 'active' : ''}`}
            onClick={() => setActiveTab('duplicates')}
          >
            Duplicates ({countByType.duplicates})
          </button>
          <button
            type="button"
            className={`review-filter-tab ${activeTab === 'missing' ? 'active' : ''}`}
            onClick={() => setActiveTab('missing')}
          >
            Missing Values ({countByType.missing})
          </button>
          <button
            type="button"
            className={`review-filter-tab ${activeTab === 'invalid' ? 'active' : ''}`}
            onClick={() => setActiveTab('invalid')}
          >
            Invalid Values ({countByType.invalid})
          </button>
          <button
            type="button"
            className={`review-filter-tab ${activeTab === 'formatting' ? 'active' : ''}`}
            onClick={() => setActiveTab('formatting')}
          >
            Formatting ({countByType.formatting})
          </button>
        </div>

        {/* Issue Cards List */}
        {filteredIssues.length === 0 ? (
          <div style={{
            padding: '2rem 1rem',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.84rem'
          }}>
            <ShieldCheck size={28} color="#245B43" style={{ margin: '0 auto 0.5rem auto' }} />
            <div>No unresolved issues in this category. Records satisfy validation requirements.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', overflowY: 'auto', paddingRight: '4px' }}>
            {filteredIssues.map((iss) => (
              <div
                key={iss.id}
                className={`issue-card severity-${iss.severity.toLowerCase()}`}
                style={{
                  opacity: iss.status === 'excluded' ? 0.6 : 1,
                  background: iss.status === 'accepted' ? '#FAFCFA' : '#FFFFFF'
                }}
              >
                {/* Top Row: Tag, Row & Column, Status */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '0.15rem 0.5rem',
                      borderRadius: 'var(--radius-pill)',
                      background: iss.severity === 'ERROR' ? 'var(--badge-red-bg)' : iss.severity === 'WARNING' ? '#FEF3C7' : '#DDF2E3',
                      color: iss.severity === 'ERROR' ? 'var(--badge-red-text)' : iss.severity === 'WARNING' ? '#92400E' : '#245B43'
                    }}>
                      {iss.severity} &bull; {iss.column}
                    </span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                      Row {iss.row_id.replace('row_', '')} ({iss.file_name})
                    </span>
                  </div>

                  {/* Status Indicator */}
                  <div>
                    {iss.status === 'accepted' && (
                      <span style={{ fontSize: '0.72rem', color: '#15803D', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                        <Check size={13} /> Accepted
                      </span>
                    )}
                    {iss.status === 'excluded' && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                        <X size={13} /> Excluded from import
                      </span>
                    )}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.15rem' }}>
                    {iss.title}
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                    {iss.description}
                  </div>
                </div>

                {/* Comparison Box: Original -> Suggested or Inline Editor */}
                {editingIssueId === iss.id ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                    <input
                      type="text"
                      className="form-input"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      placeholder="Enter corrected value"
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.78rem', flex: 1 }}
                      autoFocus
                    />
                    <button
                      type="button"
                      className="btn-forest"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.74rem' }}
                      onClick={() => handleSaveEdit(iss)}
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setEditingIssueId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="val-compare-box">
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Original:</span>
                    <span className="val-original">{iss.original_value || 'NULL'}</span>
                    <ArrowRight size={13} className="val-arrow" />
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Suggested:</span>
                    <span className="val-suggested">{iss.suggested_value || 'NULL'}</span>
                  </div>
                )}

                {/* Action Buttons for this Issue */}
                {iss.status !== 'excluded' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginTop: '0.25rem' }}>
                    {iss.status !== 'accepted' && (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => onAcceptIssue?.(iss.id)}
                        disabled={disabled}
                      >
                        <Check size={13} color="#245B43" />
                        <span>Accept Suggestion</span>
                      </button>
                    )}

                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleStartEdit(iss)}
                      disabled={disabled}
                    >
                      <Edit3 size={13} />
                      <span>Edit Value</span>
                    </button>

                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      onClick={() => onExcludeIssue?.(iss.id)}
                      disabled={disabled}
                    >
                      <X size={13} />
                      <span>Exclude Row</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation Modal for destructive actions */}
      {confirmModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.45)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{
            background: '#FFFFFF',
            borderRadius: 'var(--radius-xl)',
            padding: '1.5rem',
            maxWidth: '440px',
            width: '90%',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)'
          }}>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Confirm Exclusion
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              Are you sure you want to exclude {confirmModal.count} confirmed duplicate records from this import? These records will not be added to your database.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmModal(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={executeConfirmedBulk}
              >
                Yes, Exclude Records
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
