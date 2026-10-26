import React, { useState } from 'react'
import {
  CheckCircle2, AlertTriangle, AlertCircle, ArrowRight,
  Database, Eye, EyeOff, Sparkles, Check, X, ShieldAlert
} from 'lucide-react'

export default function DataPreviewTable({
  rows = [],
  summary = {},
  onToggleExcludeRow,
  onConfirmImport,
  isImporting = false
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterMode, setFilterMode] = useState('all') // all, ready, flagged, excluded

  const readyCount = rows.filter(r => !r._excluded && r._validation_status !== 'error').length
  const excludedCount = rows.filter(r => r._excluded).length

  // Filter rows
  const filteredRows = rows.filter((r) => {
    if (filterMode === 'ready' && (r._excluded || r._validation_status === 'error')) return false
    if (filterMode === 'flagged' && r._validation_status === 'ready' && !r._excluded) return false
    if (filterMode === 'excluded' && !r._excluded) return false

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      const pName = (r.product_name || '').toLowerCase()
      const cat = (r.category || '').toLowerCase()
      const ord = (r.order_id || '').toLowerCase()
      const cust = (r.customer || '').toLowerCase()
      return pName.includes(term) || cat.includes(term) || ord.includes(term) || cust.includes(term)
    }
    return true
  })

  return (
    <div style={{
      background: '#FFFFFF',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
      padding: '1.25rem',
      boxShadow: 'var(--shadow-card)',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem'
    }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Data Preview & Validation Table
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Inspect normalized records before final database commit. Unresolved duplicates and errors are excluded by default.
          </p>
        </div>

        {/* Prominent Confirm Import Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn-forest"
            onClick={onConfirmImport}
            disabled={isImporting || readyCount === 0}
            style={{ padding: '0.65rem 1.5rem', fontSize: '0.88rem' }}
          >
            <Database size={16} />
            <span>
              {isImporting
                ? 'Importing records...'
                : `Confirm Import (${readyCount} Valid Records)`}
            </span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        padding: '0.5rem 0',
        borderBottom: '1px solid rgba(0, 0, 0, 0.05)'
      }}>
        {/* Search */}
        <div style={{ maxWidth: '280px', flex: 1 }}>
          <input
            type="text"
            className="form-input"
            placeholder="Search items, orders, buyers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem' }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <button
            type="button"
            className={`btn btn-sm ${filterMode === 'all' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setFilterMode('all')}
            style={{ fontWeight: filterMode === 'all' ? 700 : 500 }}
          >
            All ({rows.length})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${filterMode === 'ready' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setFilterMode('ready')}
            style={{ color: '#065F46', fontWeight: filterMode === 'ready' ? 700 : 500 }}
          >
            Ready ({readyCount})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${filterMode === 'flagged' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setFilterMode('flagged')}
            style={{ color: '#B45309', fontWeight: filterMode === 'flagged' ? 700 : 500 }}
          >
            Flagged ({rows.filter(r => r._validation_status !== 'ready' && !r._excluded).length})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${filterMode === 'excluded' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setFilterMode('excluded')}
            style={{ color: '#6B7280', fontWeight: filterMode === 'excluded' ? 700 : 500 }}
          >
            Excluded ({excludedCount})
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div style={{ overflowX: 'auto', maxHeight: '440px', border: '1px solid rgba(0, 0, 0, 0.06)', borderRadius: 'var(--radius-md)' }}>
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ width: '70px' }}>Status</th>
              <th>Row</th>
              <th>Product Name</th>
              <th>Category</th>
              <th>Size</th>
              <th>Retail Price</th>
              <th>Wholesale COGS</th>
              <th>Qty</th>
              <th>Sale Date</th>
              <th>Channel</th>
              <th>Buyer</th>
              <th style={{ textAlign: 'right' }}>Include</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 ? (
              <tr>
                <td colSpan={12} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No matching records found.
                </td>
              </tr>
            ) : (
              filteredRows.map((r) => {
                const isExcluded = r._excluded
                const status = r._validation_status

                return (
                  <tr
                    key={r._row_id}
                    style={{
                      opacity: isExcluded ? 0.5 : 1,
                      background: isExcluded ? '#FAFAFA' : status === 'error' ? '#FFF8F8' : status === 'warning' ? '#FFFDF8' : 'transparent'
                    }}
                  >
                    {/* Status Badge */}
                    <td>
                      {isExcluded ? (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          color: '#6B7280',
                          background: '#E5E7EB',
                          padding: '0.15rem 0.45rem',
                          borderRadius: 'var(--radius-pill)'
                        }}>
                          Excluded
                        </span>
                      ) : status === 'ready' ? (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          color: '#065F46',
                          background: '#DDF2E3',
                          padding: '0.15rem 0.45rem',
                          borderRadius: 'var(--radius-pill)'
                        }}>
                          <CheckCircle2 size={11} /> Ready
                        </span>
                      ) : status === 'warning' ? (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          color: '#92400E',
                          background: '#FEF3C7',
                          padding: '0.15rem 0.45rem',
                          borderRadius: 'var(--radius-pill)'
                        }}>
                          <AlertTriangle size={11} /> Warning
                        </span>
                      ) : (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          color: 'var(--badge-red-text)',
                          background: 'var(--badge-red-bg)',
                          padding: '0.15rem 0.45rem',
                          borderRadius: 'var(--radius-pill)'
                        }}>
                          <AlertCircle size={11} /> Error
                        </span>
                      )}
                    </td>

                    {/* Row Index */}
                    <td style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      #{r._source_row_idx}
                    </td>

                    {/* Product Name */}
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)', textDecoration: isExcluded ? 'line-through' : 'none' }}>
                      {r.product_name || '—'}
                    </td>

                    {/* Category */}
                    <td>
                      <span className="format-pill">{r.category || 'Tops'}</span>
                    </td>

                    {/* Size */}
                    <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {r.size || 'Free Size'}
                    </td>

                    {/* Retail Price */}
                    <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      ₹{Number(r.retail_price || 0).toLocaleString()}
                    </td>

                    {/* Cost Price */}
                    <td style={{ color: 'var(--text-secondary)' }}>
                      ₹{Number(r.cost_price || 0).toLocaleString()}
                    </td>

                    {/* Quantity */}
                    <td>{r.quantity || 1}</td>

                    {/* Sale Date */}
                    <td style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      {r.sale_date || '—'}
                    </td>

                    {/* Channel */}
                    <td>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {r.channel || 'Instagram DM'}
                      </span>
                    </td>

                    {/* Customer */}
                    <td style={{ fontSize: '0.74rem', color: '#245B43', fontWeight: 600 }}>
                      {r.customer || '@buyer'}
                    </td>

                    {/* Toggle Exclude Button */}
                    <td style={{ textAlign: 'right' }}>
                      <button
                        type="button"
                        className={`btn btn-sm ${isExcluded ? 'btn-secondary' : 'btn-ghost'}`}
                        onClick={() => onToggleExcludeRow?.(r._row_id, !isExcluded)}
                        title={isExcluded ? 'Include this record' : 'Exclude this record from import'}
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                      >
                        {isExcluded ? (
                          <span style={{ color: '#245B43', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                            <Check size={12} /> Include
                          </span>
                        ) : (
                          <span style={{ color: '#9CA3AF', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                            <X size={12} /> Exclude
                          </span>
                        )}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Info Notice */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        fontSize: '0.76rem',
        color: 'var(--text-secondary)',
        paddingTop: '0.5rem'
      }}>
        <div>
          Showing <strong>{filteredRows.length}</strong> of <strong>{rows.length}</strong> records.
          {excludedCount > 0 && (
            <span style={{ color: '#B45309', marginLeft: '0.4rem' }}>
              ({excludedCount} records excluded and will not be imported).
            </span>
          )}
        </div>
        <div style={{ color: '#245B43', fontWeight: 600 }}>
          Atomic database transaction will safeguard against partial data corruption.
        </div>
      </div>
    </div>
  )
}
