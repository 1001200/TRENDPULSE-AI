import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle, Loader, ArrowRight } from 'lucide-react'
import { datasetAPI } from '../api/client'
import './UploadPage.css'

export default function UploadPage() {
  const navigate = useNavigate()
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
    const f = e.dataTransfer?.files?.[0]
    if (f) setFile(f)
  }, [])

  const handleFileSelect = (e) => {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError('')
    setProgress(0)
    try {
      const res = await datasetAPI.upload(file, (e) => {
        if (e.total) setProgress(Math.round((e.loaded / e.total) * 100))
      })
      setResult(res.data)
      // Auto-redirect to dataset intelligence after 1.5s
      setTimeout(() => {
        navigate(`/dataset/${res.data.dataset_id}`)
      }, 1500)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="page-container">
      <div className="upload-hero animate-in">
        <div className="upload-hero-badge">
          <span className="bauhaus-dot" />
          <span>DATA ENGINE V4 • AUTONOMOUS INGESTION</span>
        </div>
        <h2 className="font-display">INGEST APPAREL SALES DATA</h2>
        <p className="upload-subtitle">
          DROP A RAW CSV OR EXCEL CATALOG — TRENDPULSE NORMALIZES SIZES, AUDITS MARGINS, AND SYNTHESIZES PREDICTIONS AUTOMATICALLY.
        </p>
      </div>

      {/* Bauhaus Dropzone */}
      <div
        className={`dropzone animate-in animate-in-delay-1 ${dragActive ? 'dropzone--active' : ''} ${file ? 'dropzone--has-file' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        {file ? (
          <div className="dropzone-file">
            <div className="dropzone-file-icon">
              <FileSpreadsheet size={36} strokeWidth={2.5} />
            </div>
            <div>
              <div className="dropzone-filename">{file.name}</div>
              <div className="dropzone-filesize">
                {(file.size / 1024).toFixed(1)} KB • READY FOR INGESTION
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="dropzone-circle-icon">
              <Upload size={36} strokeWidth={2.5} />
            </div>
            <div className="dropzone-text">
              <strong>CLICK TO BROWSE</strong> OR DRAG &amp; DROP CSV FILE
            </div>
            <div className="dropzone-hint">
              SUPPORTS SHOPIFY, WOOCOMMERCE &amp; EXCEL EXPORTS (UP TO 100MB)
            </div>
          </>
        )}
      </div>

      {/* Upload Button & Progress */}
      {file && !result && (
        <div className="upload-actions animate-in animate-in-delay-2">
          <button
            className="btn btn-red btn-lg"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader size={18} className="spin" strokeWidth={2.5} />
                <span>PROCESSING PIPELINE ({progress}%)…</span>
              </>
            ) : (
              <>
                <span>START AUTONOMOUS INGESTION</span>
                <ArrowRight size={18} strokeWidth={2.5} />
              </>
            )}
          </button>

          {uploading && (
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="upload-error animate-in">
          <AlertCircle size={20} strokeWidth={2.5} />
          <span>{error}</span>
        </div>
      )}

      {/* Success Banner */}
      {result && (
        <div className="upload-success animate-in">
          <CheckCircle size={24} strokeWidth={2.5} />
          <div>
            <div className="upload-success-title">CATALOG INGESTION COMPLETE!</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>
              Synthesizing 60-second executive diagnosis &amp; predictive models… Redirecting now.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
