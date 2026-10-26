import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileDropZone from '../components/upload/FileDropZone'
import UploadedFilesList from '../components/upload/UploadedFilesList'
import QualityReviewSection from '../components/upload/QualityReviewSection'
import DataPreviewTable from '../components/upload/DataPreviewTable'
import UploadHistorySection from '../components/upload/UploadHistorySection'
import {
  UploadCloud, Database, CheckCircle2, ArrowRight,
  AlertCircle, Sparkles, RefreshCw, ShieldCheck, Check,
  ShoppingBag, DollarSign, Package, MessageSquare
} from 'lucide-react'
import {
  analyzeFiles,
  updateStaging,
  confirmImport,
  loadSampleData
} from '../services/api'

export default function UploadPage() {
  const navigate = useNavigate()

  // Workflow states: 'IDLE' | 'ANALYZING' | 'REVIEW' | 'IMPORTING' | 'SUCCESS'
  const [workflowState, setWorkflowState] = useState('IDLE')

  // Selected files pending upload or analyzed
  const [selectedFiles, setSelectedFiles] = useState([])

  // Staged session data from backend
  const [sessionId, setSessionId] = useState(null)
  const [fileAnalysisResults, setFileAnalysisResults] = useState([])
  const [summary, setSummary] = useState(null)
  const [issues, setIssues] = useState([])
  const [previewRows, setPreviewRows] = useState([])

  // Final import confirmation data
  const [importResult, setImportResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  // Demo sample loader state
  const [loadingSample, setLoadingSample] = useState(false)

  // Handle files selected from FileDropZone
  const handleFilesSelected = (newFiles) => {
    setErrorMessage(null)
    const combined = [...selectedFiles, ...newFiles]
    setSelectedFiles(combined)
  }

  // Remove a pending file before analyzing
  const handleRemoveFile = (index) => {
    const updated = selectedFiles.filter((_, idx) => idx !== index)
    setSelectedFiles(updated)
    if (updated.length === 0) {
      setWorkflowState('IDLE')
      setSessionId(null)
      setSummary(null)
      setIssues([])
      setPreviewRows([])
    }
  }

  // Trigger file analysis & issue detection
  const handleStartAnalysis = async () => {
    if (selectedFiles.length === 0) return

    setWorkflowState('ANALYZING')
    setErrorMessage(null)

    const res = await analyzeFiles(selectedFiles)

    if (res.ok && res.data.success) {
      setSessionId(res.data.session_id)
      setFileAnalysisResults(res.data.files || [])
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
      setWorkflowState('REVIEW')
    } else {
      setWorkflowState('IDLE')
      setErrorMessage(res.error || 'Failed to analyze uploaded files. Please check file formats.')
    }
  }

  // Apply issue resolution (Accept correction)
  const handleAcceptIssue = async (issueId) => {
    if (!sessionId) return
    const res = await updateStaging({
      session_id: sessionId,
      accept_issue_ids: [issueId]
    })
    if (res.ok && res.data.success) {
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
    }
  }

  // Exclude row associated with an issue
  const handleExcludeIssue = async (issueId) => {
    if (!sessionId) return
    const res = await updateStaging({
      session_id: sessionId,
      exclude_issue_ids: [issueId]
    })
    if (res.ok && res.data.success) {
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
    }
  }

  // Edit a cell value directly
  const handleEditCell = async (rowId, column, value) => {
    if (!sessionId) return
    const res = await updateStaging({
      session_id: sessionId,
      cell_edits: [{ row_id: rowId, column, value }]
    })
    if (res.ok && res.data.success) {
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
    }
  }

  // Toggle inclusion / exclusion of a row in the preview table
  const handleToggleExcludeRow = async (rowId, shouldExclude) => {
    if (!sessionId) return
    const payload = {
      session_id: sessionId,
      ...(shouldExclude ? { exclude_row_ids: [rowId] } : { include_row_ids: [rowId] })
    }
    const res = await updateStaging(payload)
    if (res.ok && res.data.success) {
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
    }
  }

  // Execute bulk action on issues
  const handleBulkAction = async (action) => {
    if (!sessionId) return
    const res = await updateStaging({
      session_id: sessionId,
      bulk_action: action
    })
    if (res.ok && res.data.success) {
      setSummary(res.data.summary)
      setIssues(res.data.issues || [])
      setPreviewRows(res.data.preview_rows || [])
    }
  }

  // Final Commit Import
  const handleConfirmImport = async () => {
    if (!sessionId) return
    setWorkflowState('IMPORTING')
    setErrorMessage(null)

    const res = await confirmImport({ session_id: sessionId })

    if (res.ok && res.data.success) {
      setImportResult(res.data)
      setWorkflowState('SUCCESS')
    } else {
      setWorkflowState('REVIEW')
      setErrorMessage(res.error || 'Database import failed. Please review your records and try again.')
    }
  }

  // Load demo sample thrift records
  const handleLoadSample = async () => {
    setLoadingSample(true)
    setErrorMessage(null)
    setImportResult(null)

    const res = await loadSampleData()
    setLoadingSample(false)

    if (res.ok) {
      setImportResult({
        message: res.data.message,
        imported_count: res.data.summary?.total_rows || 48,
        quality_score: res.data.summary?.quality_score || 94.2,
        entities_saved: res.data.summary?.saved_entities || {
          products: 48,
          sales: 42,
          inventory: 48,
          inquiries: 12
        }
      })
      setWorkflowState('SUCCESS')
    } else {
      setErrorMessage(res.error || 'Failed to load sample data.')
    }
  }

  // Reset workflow to upload more files
  const handleResetWorkflow = () => {
    setWorkflowState('IDLE')
    setSelectedFiles([])
    setSessionId(null)
    setFileAnalysisResults([])
    setSummary(null)
    setIssues([])
    setPreviewRows([])
    setImportResult(null)
    setErrorMessage(null)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 1. Contextual Header Greeting */}
      <div style={{
        background: '#FFFFFF',
        borderRadius: 'var(--radius-xl)',
        padding: '1.25rem 1.5rem',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-card)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{
            fontSize: '0.72rem',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: '#245B43',
            marginBottom: '0.2rem'
          }}>
            Data Management & Ingestion
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Let's get your business data ready.
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Securely import multi-format files. TrendPulse validates quality, cleans formatting, and prevents duplicate records.
          </p>
        </div>

        {/* Load Sample Demo Button */}
        <div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleLoadSample}
            disabled={loadingSample || workflowState === 'ANALYZING' || workflowState === 'IMPORTING'}
            style={{ fontSize: '0.82rem' }}
          >
            <Database size={15} color="#245B43" />
            <span>{loadingSample ? 'Loading demo records...' : 'Load Demo Thrift Data'}</span>
          </button>
        </div>
      </div>

      {/* 2. Error Banner if any */}
      {errorMessage && (
        <div style={{
          background: 'var(--badge-red-bg)',
          borderColor: 'rgba(217, 45, 32, 0.25)',
          borderRadius: 'var(--radius-lg)',
          padding: '0.9rem 1.25rem',
          border: '1px solid',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem',
          color: 'var(--badge-red-text)',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 3. Main Upload Area (Visible when IDLE or analyzing) */}
      {(workflowState === 'IDLE' || workflowState === 'ANALYZING') && (
        <>
          <div className="card">
            <FileDropZone
              onFilesSelected={handleFilesSelected}
              disabled={workflowState === 'ANALYZING'}
              isProcessing={workflowState === 'ANALYZING'}
            />
          </div>

          {/* Selected Files List and Action Trigger */}
          {selectedFiles.length > 0 && (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <UploadedFilesList
                files={selectedFiles}
                onRemoveFile={handleRemoveFile}
                disabled={workflowState === 'ANALYZING'}
              />

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '1rem',
                borderTop: '1px solid rgba(0, 0, 0, 0.05)',
                flexWrap: 'wrap',
                gap: '0.75rem'
              }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'} ready for extraction and quality inspection.
                </span>

                <button
                  type="button"
                  className="btn-forest"
                  onClick={handleStartAnalysis}
                  disabled={workflowState === 'ANALYZING'}
                >
                  {workflowState === 'ANALYZING' ? (
                    <>
                      <RefreshCw size={16} className="spin-animation" />
                      <span>Extracting & Inspecting Records...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      <span>Inspect & Prepare Records</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* 4. Processing Status Banner */}
      {(workflowState === 'ANALYZING' || workflowState === 'IMPORTING') && (
        <div className="card" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          background: '#F0F9F4',
          borderColor: 'rgba(36, 91, 67, 0.2)'
        }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: '#DDF2E3',
            color: '#245B43',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <RefreshCw size={22} className="spin-animation" />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1B4533' }}>
              {workflowState === 'ANALYZING'
                ? 'Processing & Detecting Business Records...'
                : 'Committing Validated Records to Database...'}
            </div>
            <div style={{ fontSize: '0.76rem', color: '#245B43', marginTop: '0.15rem' }}>
              {workflowState === 'ANALYZING'
                ? 'Extracting multi-format data → Checking duplicates → Normalizing sizes and prices → Auditing quality'
                : 'Writing atomic transaction & audit ledger. Existing business records remain protected.'}
            </div>
          </div>
        </div>
      )}

      {/* 5. Review & Preview Stage */}
      {workflowState === 'REVIEW' && summary && (
        <>
          {/* File summary bar */}
          <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <ShieldCheck size={20} color="#245B43" />
              <div>
                <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Extraction Complete: {summary.total_rows} records detected across {fileAnalysisResults.length} {fileAnalysisResults.length === 1 ? 'file' : 'files'}
                </span>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', display: 'block' }}>
                  Review issues below, accept suggested corrections, or exclude records before confirming import.
                </span>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleResetWorkflow}
            >
              Upload Different Files
            </button>
          </div>

          {/* Quality Review Section */}
          <QualityReviewSection
            summary={summary}
            issues={issues}
            onAcceptIssue={handleAcceptIssue}
            onExcludeIssue={handleExcludeIssue}
            onEditCell={handleEditCell}
            onBulkAction={handleBulkAction}
            disabled={workflowState === 'IMPORTING'}
          />

          {/* Data Preview Table & Final Confirm Import */}
          <DataPreviewTable
            rows={previewRows}
            summary={summary}
            onToggleExcludeRow={handleToggleExcludeRow}
            onConfirmImport={handleConfirmImport}
            isImporting={workflowState === 'IMPORTING'}
          />
        </>
      )}

      {/* 6. Success State Card */}
      {workflowState === 'SUCCESS' && importResult && (
        <div style={{
          background: 'linear-gradient(135deg, #EBF8F0 0%, #DDF2E3 100%)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid rgba(36, 91, 67, 0.25)',
          padding: '2rem 1.75rem',
          boxShadow: 'var(--shadow-card)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: 50,
              height: 50,
              borderRadius: '50%',
              background: '#245B43',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Check size={26} />
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#1B4533', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Import Completed Successfully
              </div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#073B28', letterSpacing: '-0.01em' }}>
                {importResult.message || `Imported ${importResult.imported_count} records into TrendPulse.`}
              </h2>
            </div>
          </div>

          {/* Breakdown of Entities Saved */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '0.75rem'
          }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.75)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#245B43', marginBottom: '0.2rem' }}>
                <ShoppingBag size={15} />
                <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>Products Added</span>
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#073B28' }}>
                {importResult.entities_saved?.products ?? importResult.imported_count}
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.75)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#245B43', marginBottom: '0.2rem' }}>
                <DollarSign size={15} />
                <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>Sales Orders</span>
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#073B28' }}>
                {importResult.entities_saved?.sales ?? importResult.imported_count}
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.75)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#245B43', marginBottom: '0.2rem' }}>
                <Package size={15} />
                <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>Inventory Items</span>
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#073B28' }}>
                {importResult.entities_saved?.inventory ?? importResult.imported_count}
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.75)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#245B43', marginBottom: '0.2rem' }}>
                <ShieldCheck size={15} />
                <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>Quality Health</span>
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#073B28' }}>
                {importResult.quality_score ?? 96.5}%
              </div>
            </div>
          </div>

          {/* Navigation Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn-forest"
              onClick={() => navigate('/')}
            >
              <span>Explore Sales Dashboard</span>
              <ArrowRight size={15} />
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/products')}
            >
              <span>View Product Inventory</span>
            </button>

            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleResetWorkflow}
            >
              <span>Import Another File</span>
            </button>
          </div>
        </div>
      )}

      {/* 7. Past Upload History Drawer */}
      <UploadHistorySection />
    </div>
  )
}
