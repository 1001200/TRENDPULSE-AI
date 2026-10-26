import React from 'react'
import {
  FileSpreadsheet, FileText, Image as ImageIcon, File,
  CheckCircle2, AlertTriangle, AlertCircle, Trash2,
  RefreshCw, Sparkles, Tag
} from 'lucide-react'

export default function UploadedFilesList({
  files = [],
  analysisResults = [],
  onRemoveFile,
  disabled = false
}) {
  if (files.length === 0 && analysisResults.length === 0) return null

  // Combine files with their analysis metadata if available
  const displayItems = files.map((file, idx) => {
    const analysis = analysisResults.find(a => a.filename === file.name) || {}
    return {
      id: file.name + '-' + idx,
      name: file.name,
      size: file.size,
      rawFile: file,
      format: (file.name.split('.').pop() || 'file').toUpperCase(),
      status: analysis.status || 'ready_to_upload',
      recordType: analysis.detected_record_type,
      confidence: analysis.record_type_confidence,
      recordsCount: analysis.records_count,
      error: analysis.error,
      warning: analysis.warning,
      isDuplicateUpload: analysis.is_duplicate_upload
    }
  })

  const getFileIcon = (filename) => {
    const ext = filename.toLowerCase().split('.').pop()
    if (['csv', 'xlsx', 'xls'].includes(ext)) {
      return <FileSpreadsheet size={20} color="#245B43" />
    }
    if (['pdf', 'docx', 'txt'].includes(ext)) {
      return <FileText size={20} color="#0D9488" />
    }
    if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) {
      return <ImageIcon size={20} color="#6366F1" />
    }
    return <File size={20} color="var(--text-secondary)" />
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB'
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const getRecordTypeLabel = (type) => {
    switch (type) {
      case 'sales_orders':
        return 'Sales & Orders'
      case 'products_inventory':
        return 'Products & Inventory'
      case 'customer_inquiries':
        return 'Customer Inquiries'
      case 'social_content':
        return 'Social & Engagement'
      case 'mixed_business':
        return 'Mixed Retail Data'
      default:
        return 'Business Records'
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Selected Files ({displayItems.length})
        </h3>
        <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          Auto-detecting formats and schemas
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {displayItems.map((item, idx) => (
          <div
            key={item.id}
            className="file-card-item"
            style={{
              borderColor: item.status === 'failed'
                ? 'rgba(217, 45, 32, 0.3)'
                : item.isDuplicateUpload
                  ? 'rgba(217, 119, 6, 0.3)'
                  : 'rgba(0, 0, 0, 0.07)'
            }}
          >
            {/* Left: Icon & File Info */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flex: 1, minWidth: 0 }}>
              <div style={{
                width: 38,
                height: 38,
                borderRadius: 'var(--radius-md)',
                background: '#F5F7F5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {getFileIcon(item.name)}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', minWidth: 0, flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: '0.86rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: '320px'
                  }}>
                    {item.name}
                  </span>
                  <span className="format-pill">{item.format}</span>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    {formatFileSize(item.size)}
                  </span>
                </div>

                {/* Status / Detection Badges */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                  {item.recordType && (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#065F46',
                      background: '#DDF2E3',
                      padding: '0.15rem 0.5rem',
                      borderRadius: 'var(--radius-pill)'
                    }}>
                      <Sparkles size={11} />
                      {getRecordTypeLabel(item.recordType)}
                      {item.confidence ? ` (${item.confidence}%)` : ''}
                    </span>
                  )}

                  {item.recordsCount !== undefined && item.recordsCount > 0 && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                      &bull; {item.recordsCount} {item.recordsCount === 1 ? 'row' : 'rows'} detected
                    </span>
                  )}

                  {item.isDuplicateUpload && (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#92400E',
                      background: '#FEF3C7',
                      padding: '0.15rem 0.45rem',
                      borderRadius: 'var(--radius-pill)'
                    }}>
                      <AlertTriangle size={11} />
                      Possible duplicate upload
                    </span>
                  )}
                </div>

                {/* Error / Warning Details */}
                {item.error && (
                  <div style={{
                    fontSize: '0.74rem',
                    color: 'var(--badge-red-text)',
                    marginTop: '0.2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}>
                    <AlertCircle size={13} />
                    <span>{item.error}</span>
                  </div>
                )}
                {item.warning && !item.error && (
                  <div style={{
                    fontSize: '0.74rem',
                    color: '#B45309',
                    marginTop: '0.2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}>
                    <AlertTriangle size={13} />
                    <span>{item.warning}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: '1rem' }}>
              {onRemoveFile && !disabled && (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => onRemoveFile(idx)}
                  title="Remove file"
                  style={{ padding: '0.4rem', color: '#9CA3AF' }}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
