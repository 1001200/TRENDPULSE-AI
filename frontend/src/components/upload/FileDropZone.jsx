import React, { useState, useRef } from 'react'
import {
  UploadCloud, FileSpreadsheet, FileText, Image as ImageIcon,
  CheckCircle2, FolderOpen, AlertCircle
} from 'lucide-react'

const ACCEPTED_FORMATS_STRING = '.csv,.xlsx,.xls,.pdf,.docx,.txt,.png,.jpg,.jpeg,.webp'
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024 // 25 MB

export default function FileDropZone({
  onFilesSelected,
  disabled = false,
  isProcessing = false
}) {
  const [dragActive, setDragActive] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const inputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (disabled || isProcessing) return
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const validateAndPassFiles = (fileList) => {
    setErrorMessage(null)
    const files = Array.from(fileList || [])
    if (files.length === 0) return

    // Validate size
    const oversized = files.filter(f => f.size > MAX_FILE_SIZE_BYTES)
    if (oversized.length > 0) {
      setErrorMessage(`The file "${oversized[0].name}" exceeds the maximum permitted limit of 25MB.`)
      return
    }

    onFilesSelected?.(files)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (disabled || isProcessing) return
    setDragActive(false)
    if (e.dataTransfer?.files?.length) {
      validateAndPassFiles(e.dataTransfer.files)
    }
  }

  const handleChange = (e) => {
    if (e.target.files?.length) {
      validateAndPassFiles(e.target.files)
      // reset input so same file can be reselected if needed
      e.target.value = ''
    }
  }

  const handleBrowseClick = (e) => {
    e.stopPropagation()
    if (!disabled && !isProcessing) {
      inputRef.current?.click()
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div
        className={`upload-dropzone-container ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        style={{ opacity: disabled || isProcessing ? 0.7 : 1, cursor: disabled || isProcessing ? 'not-allowed' : 'pointer' }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_FORMATS_STRING}
          multiple
          onChange={handleChange}
          style={{ display: 'none' }}
        />

        {/* Cloud Upload Icon */}
        <div className="upload-cloud-icon-wrapper">
          <UploadCloud size={32} />
        </div>

        {/* Main Heading & Subtitle */}
        <h2 style={{
          fontSize: '1.25rem',
          fontWeight: 800,
          color: 'var(--text-primary)',
          marginBottom: '0.45rem',
          letterSpacing: '-0.01em'
        }}>
          Upload Your Business Data
        </h2>

        <p style={{
          fontSize: '0.84rem',
          color: 'var(--text-secondary)',
          maxWidth: '560px',
          margin: '0 auto 1.35rem auto',
          lineHeight: 1.55
        }}>
          Upload your business files in supported formats. TrendPulse will identify useful information, check data quality, and help you prepare your records for import.
        </p>

        {/* Prominent Browse Files Button */}
        <div style={{ marginBottom: '1.5rem' }}>
          <button
            type="button"
            className="btn-forest"
            onClick={handleBrowseClick}
            disabled={disabled || isProcessing}
          >
            <FolderOpen size={17} />
            <span>Browse Files</span>
          </button>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
            or drag and drop files anywhere here
          </div>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'var(--badge-red-bg)',
            color: 'var(--badge-red-text)',
            padding: '0.45rem 1rem',
            borderRadius: 'var(--radius-pill)',
            fontSize: '0.78rem',
            fontWeight: 600,
            marginBottom: '1rem'
          }}>
            <AlertCircle size={15} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Supported Format Tags Grouped */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.65rem',
          paddingTop: '1rem',
          borderTop: '1px solid rgba(0, 0, 0, 0.05)',
          maxWidth: '680px',
          margin: '0 auto'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
            fontSize: '0.74rem'
          }}>
            {/* Structured */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="format-category-tag">Structured</span>
              <span className="format-pill"><FileSpreadsheet size={13} color="#245B43" /> CSV</span>
              <span className="format-pill"><FileSpreadsheet size={13} color="#245B43" /> XLS</span>
              <span className="format-pill"><FileSpreadsheet size={13} color="#245B43" /> XLSX</span>
            </div>

            {/* Documents */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="format-category-tag">Documents</span>
              <span className="format-pill"><FileText size={13} color="#245B43" /> PDF</span>
              <span className="format-pill"><FileText size={13} color="#245B43" /> DOCX</span>
              <span className="format-pill"><FileText size={13} color="#245B43" /> TXT</span>
            </div>

            {/* Images */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="format-category-tag">Images</span>
              <span className="format-pill"><ImageIcon size={13} color="#245B43" /> PNG</span>
              <span className="format-pill"><ImageIcon size={13} color="#245B43" /> JPG</span>
              <span className="format-pill"><ImageIcon size={13} color="#245B43" /> WebP</span>
            </div>
          </div>

          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Multiple-file selection supported &bull; Maximum file size: <strong>25 MB</strong> &bull; Automatic column & record detection
          </div>
        </div>
      </div>
    </div>
  )
}
