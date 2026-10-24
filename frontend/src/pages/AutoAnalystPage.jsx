import React, { useState, useEffect, useRef } from 'react'
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  BarChart3,
  Brain,
  ShieldCheck,
  Download,
  RefreshCw,
  Layers,
  ArrowRight,
  Search,
  Activity,
  Zap,
  Info,
  Sliders,
  ChevronRight,
  Printer,
  Send,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { analystAPI } from '../api/client'

// Cluster Palette
const CLUSTER_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#06b6d4']

export default function AutoAnalystPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [activeTab, setActiveTab] = useState('executive') // executive | visual | ml | health
  const [dragActive, setDragActive] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [copilotQuery, setCopilotQuery] = useState('')
  const [copilotAnswer, setCopilotAnswer] = useState(null)
  const fileInputRef = useRef(null)

  const handleAskCopilot = (questionText) => {
    const q = (questionText || copilotQuery).toLowerCase().trim()
    if (!q || !data) return

    if (q.includes('outlier') || q.includes('anomaly') || q.includes('risk')) {
      const anom = data.patterns?.anomalies
      if (anom?.enabled && anom?.top_outliers?.length > 0) {
        const top = anom.top_outliers[0]
        setCopilotAnswer(`Found ${anom.outlier_count} anomalies (${anom.outlier_rate_pct}% rate). Top flag is Row #${top.row_index}: ${top.reason}.`)
      } else {
        setCopilotAnswer('No significant multi-variate anomalies were detected. Data follows expected distribution.')
      }
    } else if (q.includes('cluster') || q.includes('segment') || q.includes('cohort') || q.includes('persona')) {
      const cl = data.patterns?.clusters
      if (cl?.enabled && cl?.profiles?.length > 0) {
        const pList = cl.profiles.map(p => `${p.name} (${p.percentage}%)`).join('; ')
        setCopilotAnswer(`Population is segmented into ${cl.k} behavioral personas: ${pList}.`)
      } else {
        setCopilotAnswer('Clustering inactive for this dataset structure.')
      }
    } else if (q.includes('driver') || q.includes('correlation') || q.includes('relation')) {
      const corrs = data.patterns?.correlations
      if (corrs && corrs.length > 0) {
        setCopilotAnswer(`The primary statistical coupling is between '${corrs[0].column_a}' and '${corrs[0].column_b}' with Pearson r = ${corrs[0].r_value} (${corrs[0].direction} coupling).`)
      } else {
        setCopilotAnswer('No high-magnitude linear correlations identified between numeric variables.')
      }
    } else if (q.includes('quality') || q.includes('clean') || q.includes('health') || q.includes('missing')) {
      const qm = data.quality?.quality_metrics
      setCopilotAnswer(`Dataset health score is ${data.quality?.health_score}%. Imputed ${qm?.total_missing_imputed || 0} missing cells and removed ${qm?.duplicates_removed || 0} duplicate rows.`)
    } else {
      setCopilotAnswer(`Dataset '${data.metadata?.filename}' contains ${data.metadata?.rows_cleaned} clean records across ${data.metadata?.columns_count} columns. ${data.narrative?.executive_summary}`)
    }
  }

  const steps = [
    'Inferring semantic data types (Zero-Shot Discovery)...',
    'Executing smart cleaning & audit trail logging...',
    'Mining correlations, clusters & isolation forest anomalies...',
    'Synthesizing visual grammar & executive briefing...',
  ]

  const runAnalysis = async (filePromise) => {
    setLoading(true)
    setError(null)
    setProcessingStep(0)

    const stepInterval = setInterval(() => {
      setProcessingStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev))
    }, 450)

    try {
      const res = await filePromise
      setData(res.data)
      setActiveTab('executive')
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      clearInterval(stepInterval)
      setLoading(false)
    }
  }

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      runAnalysis(analystAPI.analyzeFile(file))
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      runAnalysis(analystAPI.analyzeFile(file))
    }
  }

  const loadSample = (sampleId) => {
    runAnalysis(analystAPI.analyzeSample(sampleId))
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-[2px] shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Brain className="w-5 h-5 text-indigo-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-lg tracking-tight text-white">AutoAnalyst</h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  End-to-End Engine
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Problem Statement 3
                </span>
              </div>
              <p className="text-xs text-slate-400">Zero-Shot Autonomous Insight & Adaptive Dashboard Engine</p>
            </div>
          </div>

          {data && (
            <div className="flex items-center gap-3">
              <a
                href={analystAPI.downloadCleanedUrl(data.analysis_id)}
                download
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/40 text-xs font-medium transition-all shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                Download Cleaned CSV
              </a>
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-sm shadow-indigo-600/20"
              >
                <Printer className="w-3.5 h-3.5" />
                Print Briefing
              </button>
              <button
                onClick={() => setData(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Upload New
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* If no data loaded yet, show the Ingestion Hero */}
        {!data && !loading && (
          <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                Autonomous Raw Spreadsheet-to-Insight Platform
              </div>
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400">
                From Raw Data to Executive Insight in Seconds.
              </h2>
              <p className="text-slate-400 text-sm md:text-base max-w-2xl mx-auto leading-relaxed">
                Drop any spreadsheet from any domain — Sales, Healthcare, Marketing, or HR. AutoAnalyst auto-detects column types, cleans anomalies, trains unsupervised ML models, and builds an adaptive dashboard with zero manual configuration.
              </p>
            </div>

            {/* Drag and Drop Zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setDragActive(true)
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 relative overflow-hidden group ${
                dragActive
                  ? 'border-indigo-500 bg-indigo-950/30 ring-4 ring-indigo-500/20 scale-[1.01]'
                  : 'border-slate-800 bg-slate-900/40 hover:border-indigo-500/50 hover:bg-slate-900/80'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
              />
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300 shadow-inner">
                <UploadCloud className="w-8 h-8 text-indigo-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-1">
                Drop your raw CSV or Excel file here, or <span className="text-indigo-400 underline">browse</span>
              </h3>
              <p className="text-xs text-slate-500">Supports .csv, .xlsx, .xls • Any column schema or domain</p>
            </div>

            {/* 1-Click Practice Datasets */}
            <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <h4 className="text-sm font-semibold text-white">Evaluate with Pre-loaded Sample Domains</h4>
                </div>
                <span className="text-[11px] text-slate-500">Instant Zero-Shot Testing</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <button
                  onClick={() => loadSample('healthcare')}
                  className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 hover:bg-indigo-950/20 transition-all text-left group"
                >
                  <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Activity className="w-4 h-4 text-rose-400" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white group-hover:text-indigo-300">Healthcare Clinic</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">350 patient records, BP, stay days, diagnoses & costs</div>
                  </div>
                </button>

                <button
                  onClick={() => loadSample('marketing')}
                  className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 hover:bg-indigo-950/20 transition-all text-left group"
                >
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white group-hover:text-indigo-300">Marketing Campaigns</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">280 ad sets, spend, CTR, conversions & revenue</div>
                  </div>
                </button>

                <button
                  onClick={() => loadSample('sales')}
                  className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 hover:bg-indigo-950/20 transition-all text-left group"
                >
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white group-hover:text-indigo-300">Retail & E-Commerce</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Orders, quantities, pricing, categories & discounts</div>
                  </div>
                </button>
              </div>
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}

        {/* Loading Stepper State */}
        {loading && (
          <div className="max-w-xl mx-auto py-16 text-center space-y-6">
            <div className="relative w-20 h-20 mx-auto">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping" />
              <div className="w-20 h-20 rounded-full border-4 border-t-indigo-500 border-indigo-500/20 animate-spin flex items-center justify-center bg-slate-900 shadow-xl shadow-indigo-500/20">
                <Brain className="w-8 h-8 text-indigo-400" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-white">Autonomous Intelligence Pipeline Running</h3>
              <p className="text-sm text-indigo-400 font-medium animate-pulse">{steps[processingStep]}</p>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
              <div
                className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-2 transition-all duration-300 ease-out"
                style={{ width: `${((processingStep + 1) / steps.length) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Main Intelligence Results */}
        {data && !loading && (
          <div className="space-y-6">
            {/* Meta Bar */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{data.metadata?.filename}</h3>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <span>{data.metadata?.rows_cleaned?.toLocaleString()} Cleaned Records</span>
                    <span>•</span>
                    <span>{data.metadata?.columns_count} Columns</span>
                    <span>•</span>
                    <span>Processed in {data.metadata?.processing_time_ms}ms</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-slate-400">Data Health:</span>
                  <span className="text-xs font-bold text-emerald-400">{data.quality?.health_score}%</span>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
              <button
                onClick={() => setActiveTab('executive')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'executive'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Executive Briefing
              </button>

              <button
                onClick={() => setActiveTab('visual')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'visual'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Adaptive Dashboard ({data.dashboard?.charts?.length || 0})
              </button>

              <button
                onClick={() => setActiveTab('ml')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'ml'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <Brain className="w-3.5 h-3.5" />
                ML Discovery & Personas
              </button>

              <button
                onClick={() => setActiveTab('health')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'health'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Data Health & Audit Log
              </button>
            </div>

            {/* TAB 1: EXECUTIVE BRIEFING */}
            {activeTab === 'executive' && (
              <div className="space-y-6">
                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {data.dashboard?.kpi_cards?.map((card) => (
                    <div
                      key={card.id}
                      className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 hover:border-indigo-500/30 transition-all group"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-slate-400">{card.title}</span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          {card.badge}
                        </span>
                      </div>
                      <div className="text-2xl font-black text-white tracking-tight group-hover:text-indigo-200 transition-colors">
                        {card.value}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{card.subtitle}</div>
                    </div>
                  ))}
                </div>

                {/* Executive Summary Card */}
                <div className="bg-gradient-to-br from-indigo-950/40 via-slate-900/60 to-slate-900/60 border border-indigo-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Autonomous Executive Narrative</h3>
                  </div>
                  <p className="text-slate-200 text-sm md:text-base leading-relaxed">
                    {data.narrative?.executive_summary}
                  </p>
                </div>

                {/* Natural Language Copilot Bar */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Search className="w-4 h-4 text-indigo-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider">Ask AutoAnalyst Copilot</span>
                    </div>
                    <span className="text-[10px] text-slate-500">Autonomous Statistical Query Engine</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        value={copilotQuery}
                        onChange={(e) => setCopilotQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAskCopilot()}
                        placeholder="Ask anything about this dataset (e.g., 'What is the top anomaly?', 'Summarize clusters', 'Primary driver?')..."
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
                      />
                    </div>
                    <button
                      onClick={() => handleAskCopilot()}
                      className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/20"
                    >
                      <Send className="w-3.5 h-3.5" />
                      Ask
                    </button>
                  </div>

                  {/* Suggested Query Chips */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {[
                      'Top outlier & root cause',
                      'Describe cluster personas',
                      'What is the primary driver?',
                      'Data health diagnosis',
                    ].map((chip, cIdx) => (
                      <button
                        key={cIdx}
                        onClick={() => {
                          setCopilotQuery(chip)
                          handleAskCopilot(chip)
                        }}
                        className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-indigo-500/40 text-[11px] text-slate-400 hover:text-indigo-300 transition-all"
                      >
                        {chip}
                      </button>
                    ))}
                  </div>

                  {/* Copilot Answer Box */}
                  {copilotAnswer && (
                    <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-slate-200 leading-relaxed flex items-start gap-2.5 mt-2">
                      <Sparkles className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-indigo-300">Copilot Insight: </span>
                        <span>{copilotAnswer}</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Grid: Statistical Drivers & Prescriptive Next-Best Actions */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Key Drivers */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                      <TrendingUp className="w-4 h-4 text-cyan-400" />
                      <h4 className="text-sm font-bold text-white">Statistical Drivers & Correlations</h4>
                    </div>

                    <div className="space-y-3">
                      {data.narrative?.key_drivers?.map((driver, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-white">{driver.title}</span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                                driver.severity === 'high'
                                  ? 'bg-rose-500/20 text-rose-300'
                                  : 'bg-cyan-500/20 text-cyan-300'
                              }`}
                            >
                              {driver.severity?.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">{driver.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Prescriptive Actions */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                      <Zap className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-bold text-white">Prescriptive Next-Best Actions</h4>
                    </div>

                    <div className="space-y-3">
                      {data.narrative?.recommendations?.map((rec, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-indigo-400">{rec.priority}</span>
                          </div>
                          <p className="text-xs font-medium text-slate-200">{rec.action}</p>
                          <p className="text-[11px] text-slate-500">Impact: {rec.impact}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: ADAPTIVE VISUAL DASHBOARD */}
            {activeTab === 'visual' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {data.dashboard?.charts?.map((chart) => (
                    <div
                      key={chart.id}
                      className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4 hover:border-indigo-500/30 transition-all"
                    >
                      <div>
                        <h4 className="text-sm font-bold text-white">{chart.title}</h4>
                        <p className="text-xs text-slate-400 mt-0.5">{chart.subtitle}</p>
                      </div>

                      <div className="h-64 w-full pt-2">
                        <ResponsiveContainer width="100%" height="100%">
                          {chart.chart_type === 'area' ? (
                            <AreaChart data={chart.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <defs>
                                <linearGradient id={`grad-${chart.id}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                              <XAxis dataKey={chart.x_key} stroke="#64748b" tick={{ fontSize: 11 }} />
                              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                              />
                              <Area
                                type="monotone"
                                dataKey={chart.y_key}
                                stroke="#6366f1"
                                strokeWidth={2.5}
                                fillOpacity={1}
                                fill={`url(#grad-${chart.id})`}
                              />
                            </AreaChart>
                          ) : chart.chart_type === 'bar' ? (
                            <BarChart data={chart.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                              <XAxis dataKey={chart.x_key} stroke="#64748b" tick={{ fontSize: 11 }} />
                              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                              />
                              <Bar dataKey={chart.y_key} fill="#10b981" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          ) : chart.chart_type === 'scatter' ? (
                            <ScatterChart margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                              <XAxis dataKey={chart.x_key} name={chart.x_label} stroke="#64748b" tick={{ fontSize: 11 }} />
                              <YAxis dataKey={chart.y_key} name={chart.y_label} stroke="#64748b" tick={{ fontSize: 11 }} />
                              <Tooltip
                                cursor={{ strokeDasharray: '3 3' }}
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                              />
                              <Scatter data={chart.data} fill="#06b6d4" />
                            </ScatterChart>
                          ) : (
                            <BarChart data={chart.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                              <XAxis dataKey={chart.x_key} stroke="#64748b" tick={{ fontSize: 11 }} />
                              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                              />
                              <Bar dataKey={chart.y_key} fill="#f59e0b" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          )}
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: ML DISCOVERY & PERSONAS */}
            {activeTab === 'ml' && (
              <div className="space-y-6">
                {/* Clusters Section */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Brain className="w-5 h-5 text-indigo-400" />
                      <div>
                        <h4 className="text-sm font-bold text-white">Unsupervised K-Means Behavioral Personas</h4>
                        <p className="text-xs text-slate-400">
                          Optimal cohort partitioning calculated via silhouette heuristic
                        </p>
                      </div>
                    </div>
                    {data.patterns?.clusters?.enabled && (
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {data.patterns.clusters.k} Cohorts Discovered
                      </span>
                    )}
                  </div>

                  {data.patterns?.clusters?.enabled ? (
                    <div className="space-y-6">
                      {/* Persona Cards */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {data.patterns.clusters.profiles?.map((prof, i) => (
                          <div
                            key={prof.cluster_id}
                            className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3 relative overflow-hidden"
                          >
                            <div
                              className="absolute top-0 left-0 right-0 h-1"
                              style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
                            />
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white">{prof.name}</span>
                              <span className="text-[11px] font-semibold text-slate-400">{prof.percentage}%</span>
                            </div>
                            <div className="text-xs text-slate-400">
                              <span className="text-slate-200 font-semibold">{prof.count}</span> records
                            </div>
                            <div className="space-y-1">
                              {prof.defining_traits?.map((trait, tIdx) => (
                                <div key={tIdx} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                                  <div
                                    className="w-1.5 h-1.5 rounded-full"
                                    style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
                                  />
                                  <span>{trait}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* 2D Cluster Scatter Plot */}
                      {data.patterns.clusters.visualization_points?.length > 0 && (
                        <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800 space-y-2">
                          <h5 className="text-xs font-semibold text-slate-300">
                            2D Cluster Projection: {data.patterns.clusters.x_axis} vs {data.patterns.clusters.y_axis}
                          </h5>
                          <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <ScatterChart margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis dataKey="x" name={data.patterns.clusters.x_axis} stroke="#64748b" tick={{ fontSize: 11 }} />
                                <YAxis dataKey="y" name={data.patterns.clusters.y_axis} stroke="#64748b" tick={{ fontSize: 11 }} />
                                <Tooltip
                                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                                />
                                <Scatter data={data.patterns.clusters.visualization_points}>
                                  {data.patterns.clusters.visualization_points.map((entry, index) => (
                                    <Cell
                                      key={`cell-${index}`}
                                      fill={CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length]}
                                    />
                                  ))}
                                </Scatter>
                              </ScatterChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">Clustering inactive for this dataset shape.</p>
                  )}
                </div>

                {/* Isolation Forest Anomaly Radar */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-rose-400" />
                      <div>
                        <h4 className="text-sm font-bold text-white">Isolation Forest Anomaly Radar</h4>
                        <p className="text-xs text-slate-400">
                          Multi-dimensional outliers with exact root-cause driver attribution
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {data.patterns?.anomalies?.outlier_count || 0} Flagged Records ({data.patterns?.anomalies?.outlier_rate_pct || 0}%)
                    </span>
                  </div>

                  {data.patterns?.anomalies?.top_outliers?.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="p-3">Row #</th>
                            <th className="p-3">Anomaly Score</th>
                            <th className="p-3">Primary Trigger Column</th>
                            <th className="p-3">Deviation</th>
                            <th className="p-3">Root Cause Reason</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-300">
                          {data.patterns.anomalies.top_outliers.map((outlier) => (
                            <tr key={outlier.row_index} className="hover:bg-slate-800/40 transition-colors">
                              <td className="p-3 font-mono font-semibold text-white">#{outlier.row_index}</td>
                              <td className="p-3 font-mono text-rose-400 font-semibold">{outlier.anomaly_score}</td>
                              <td className="p-3 font-medium text-slate-200">
                                {outlier.primary_driver?.replace('_', ' ').title()}
                              </td>
                              <td className="p-3">
                                <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 font-mono">
                                  +{outlier.deviation_sigma}σ
                                </span>
                              </td>
                              <td className="p-3 text-slate-400">{outlier.reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No anomalous spikes detected.</p>
                  )}
                </div>

                {/* Feature Importance & Correlation Matrix Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Random Forest Feature Importance */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-amber-400" />
                        <div>
                          <h4 className="text-sm font-bold text-white">Auto-ML Key Driver Ranking</h4>
                          <p className="text-xs text-slate-400">
                            Random Forest feature importance on '{data.patterns?.feature_importance?.target_metric || 'Target'}'
                          </p>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        Supervised ML
                      </span>
                    </div>

                    {data.patterns?.feature_importance?.enabled && data.patterns.feature_importance.drivers?.length > 0 ? (
                      <div className="space-y-3 pt-1">
                        {data.patterns.feature_importance.drivers.map((d, dIdx) => (
                          <div key={dIdx} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium text-slate-200">{d.feature}</span>
                              <span className="font-mono text-amber-400 font-semibold">{d.importance_pct}%</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div
                                className="bg-gradient-to-r from-amber-500 to-orange-400 h-2 rounded-full"
                                style={{ width: `${d.importance_pct}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">Feature importance requires at least 3 numeric dimensions.</p>
                    )}
                  </div>

                  {/* Correlation Heatmap Grid */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-cyan-400" />
                        <div>
                          <h4 className="text-sm font-bold text-white">Correlation Matrix Heatmap</h4>
                          <p className="text-xs text-slate-400">Pairwise Pearson correlation coefficients</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        Collinearity
                      </span>
                    </div>

                    {data.patterns?.correlation_matrix && Object.keys(data.patterns.correlation_matrix).length > 0 ? (
                      <div className="overflow-x-auto pt-1">
                        <table className="w-full text-center text-xs">
                          <thead>
                            <tr>
                              <th className="p-2 text-left text-slate-500 font-mono text-[10px]"></th>
                              {Object.keys(data.patterns.correlation_matrix).map((c) => (
                                <th key={c} className="p-2 font-mono text-[10px] text-slate-400 uppercase">
                                  {c.slice(0, 8)}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {Object.entries(data.patterns.correlation_matrix).map(([rowCol, rowVals]) => (
                              <tr key={rowCol}>
                                <td className="p-2 text-left font-mono text-[10px] text-slate-300 uppercase font-semibold">
                                  {rowCol.slice(0, 10)}
                                </td>
                                {Object.entries(rowVals).map(([colName, rVal]) => {
                                  const isSelf = rowCol === colName
                                  const isPos = rVal > 0.3
                                  const isNeg = rVal < -0.3
                                  return (
                                    <td key={colName} className="p-1.5 font-mono text-[11px]">
                                      <span
                                        className={`inline-block px-2 py-1 rounded text-[10px] font-semibold ${
                                          isSelf
                                            ? 'bg-slate-800 text-slate-400'
                                            : isPos
                                            ? 'bg-emerald-500/20 text-emerald-300'
                                            : isNeg
                                            ? 'bg-rose-500/20 text-rose-300'
                                            : 'bg-slate-950 text-slate-400'
                                        }`}
                                      >
                                        {rVal.toFixed(2)}
                                      </span>
                                    </td>
                                  )
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">Insufficient numeric dimensions for correlation matrix.</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: DATA HEALTH & AUDIT TRAIL */}
            {activeTab === 'health' && (
              <div className="space-y-6">
                {/* Health Metrics Header */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                    <span className="text-xs font-medium text-slate-400">Completeness Score</span>
                    <div className="text-2xl font-black text-emerald-400 mt-1">
                      {data.quality?.quality_metrics?.completeness_score}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {data.quality?.quality_metrics?.total_missing_imputed} missing cells imputed
                    </p>
                  </div>

                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                    <span className="text-xs font-medium text-slate-400">Uniqueness Score</span>
                    <div className="text-2xl font-black text-indigo-400 mt-1">
                      {data.quality?.quality_metrics?.uniqueness_score}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {data.quality?.quality_metrics?.duplicates_removed} duplicate rows resolved
                    </p>
                  </div>

                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                    <span className="text-xs font-medium text-slate-400">Validity Score</span>
                    <div className="text-2xl font-black text-cyan-400 mt-1">
                      {data.quality?.quality_metrics?.validity_score}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">100% schema type-conformance</p>
                  </div>
                </div>

                {/* Inferred Column Schema */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Layers className="w-5 h-5 text-indigo-400" />
                      <h4 className="text-sm font-bold text-white">Inferred Column Schema (Zero-Shot Discovery)</h4>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="p-3">Clean Column Name</th>
                          <th className="p-3">Original Header</th>
                          <th className="p-3">Inferred Type</th>
                          <th className="p-3">Confidence</th>
                          <th className="p-3">Nulls</th>
                          <th className="p-3">Unique Values</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                        {Object.entries(data.schema || {}).map(([col, info]) => (
                          <tr key={col} className="hover:bg-slate-800/40">
                            <td className="p-3 font-semibold text-white">{col}</td>
                            <td className="p-3 text-slate-400 font-sans">{info.original_name || col}</td>
                            <td className="p-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] uppercase font-sans font-semibold ${
                                  info.inferred_type === 'numeric'
                                    ? 'bg-emerald-500/20 text-emerald-300'
                                    : info.inferred_type === 'datetime'
                                    ? 'bg-cyan-500/20 text-cyan-300'
                                    : info.inferred_type === 'categorical'
                                    ? 'bg-indigo-500/20 text-indigo-300'
                                    : 'bg-slate-800 text-slate-300'
                                }`}
                              >
                                {info.inferred_type}
                              </span>
                            </td>
                            <td className="p-3 text-slate-300">{(info.confidence * 100).toFixed(0)}%</td>
                            <td className="p-3 text-slate-400">{info.null_count}</td>
                            <td className="p-3 text-slate-400">{info.unique_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Audit Trail Log */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h4 className="text-sm font-bold text-white">Reversible Cleaning & Audit Log</h4>
                  </div>

                  <div className="space-y-2">
                    {data.quality?.audit_log?.map((log, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-mono text-[10px] uppercase">
                            {log.stage}
                          </span>
                          <span className="text-slate-200">{log.action}</span>
                        </div>
                        <span className="text-slate-500 text-[11px]">{log.impact}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cleaned Sample Preview */}
                {data.sample_data?.length > 0 && (
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <h4 className="text-sm font-bold text-white">Cleaned Data Preview (First 50 Rows)</h4>
                      <a
                        href={analystAPI.downloadCleanedUrl(data.analysis_id)}
                        download
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
                      >
                        Download Full Cleaned CSV <ArrowRight className="w-3 h-3" />
                      </a>
                    </div>
                    <div className="overflow-x-auto max-h-96">
                      <table className="w-full text-left text-xs whitespace-nowrap">
                        <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                          <tr>
                            {Object.keys(data.sample_data[0] || {}).map((col) => (
                              <th key={col} className="p-2.5 font-mono">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-300">
                          {data.sample_data.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-slate-800/30">
                              {Object.values(row).map((val, cIdx) => (
                                <td key={cIdx} className="p-2.5 font-mono text-[11px]">
                                  {val !== null ? String(val) : <span className="text-slate-600">null</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
