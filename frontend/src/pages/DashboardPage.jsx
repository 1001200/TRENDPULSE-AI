import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, ShieldCheck, TrendingUp, Brain, Clock, Trash2, ArrowRight } from 'lucide-react'
import { datasetAPI } from '../api/client'
import { useStore } from '../context/StoreContext'
import { formatCurrency, formatNumber, formatDate } from '../utils/formatters'
import './DashboardPage.css'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { selectStore, refreshStore } = useStore()
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const res = await datasetAPI.list()
      setDatasets(res.data.datasets || [])
    } catch {
      // If unauthorized, redirect to login
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Delete this dataset?')) return
    await datasetAPI.delete(id)
    loadDatasets()
    refreshStore()
  }

  const completedCount = datasets.filter(d => d.status === 'completed').length

  return (
    <div className="page-container">
      {/* Bauhaus Constructivist KPI Grid */}
      <div className="kpi-grid animate-in">
        <div className="kpi-card kpi-card--yellow">
          <div className="kpi-icon">
            <Database size={20} strokeWidth={2.5} />
          </div>
          <div className="kpi-label">TOTAL STORE RUNS</div>
          <div className="kpi-value">{datasets.length}</div>
          <div className="kpi-sub">INGESTED CATALOGS</div>
        </div>

        <div className="kpi-card kpi-card--blue">
          <div className="kpi-icon">
            <ShieldCheck size={20} strokeWidth={2.5} />
          </div>
          <div className="kpi-label">PROCESSED HEALTHY</div>
          <div className="kpi-value">{completedCount}</div>
          <div className="kpi-sub">AUTONOMOUS DIAGNOSES</div>
        </div>

        <div className="kpi-card kpi-card--red">
          <div className="kpi-icon">
            <Brain size={20} strokeWidth={2.5} />
          </div>
          <div className="kpi-label">ML ENGINES ACTIVE</div>
          <div className="kpi-value">{completedCount > 0 ? completedCount * 6 : 0}</div>
          <div className="kpi-sub">6 PREDICTIVE MODELS / RUN</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">
            <TrendingUp size={20} strokeWidth={2.5} />
          </div>
          <div className="kpi-label">ENGINE ARCHITECTURE</div>
          <div className="kpi-value">V4.0</div>
          <div className="kpi-sub">BAUHAUS INTELLIGENCE</div>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="card animate-in animate-in-delay-1 card-glyph-square">
        <div className="card-header">
          <div className="card-title">STORE REPOSITORIES &amp; UPLOADS</div>
          <button className="btn btn-red btn-sm" onClick={() => navigate('/upload')}>
            + INGEST NEW DATASET
          </button>
        </div>

        {loading ? (
          <div className="dash-skeleton">
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 54, marginBottom: 10 }} />)}
          </div>
        ) : datasets.length === 0 ? (
          <div className="dash-empty">
            <Database size={48} strokeWidth={2.5} />
            <h3 style={{ textTransform: 'uppercase' }}>NO STORE DATASETS INGESTED</h3>
            <p>Upload a fashion e-commerce CSV to generate your Bauhaus autonomous briefing.</p>
            <button className="btn btn-yellow mt-md" onClick={() => navigate('/upload')}>
              UPLOAD CATALOG NOW
            </button>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>RUN ID</th>
                  <th>SOURCE FILE</th>
                  <th>PROCESSING STATUS</th>
                  <th>ROWS INGESTED</th>
                  <th>UPLOAD DATE</th>
                  <th style={{ textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr
                    key={d.id}
                    className="dash-row"
                    onClick={() => {
                      if (d.status === 'completed') {
                        selectStore(d.id)
                        navigate('/briefing')
                      }
                    }}
                  >
                    <td className="font-mono" style={{ fontWeight: 900 }}>#{d.id}</td>
                    <td className="truncate" style={{ maxWidth: 300, fontWeight: 700 }}>
                      {d.filename}
                    </td>
                    <td>
                      <span className={`badge ${d.status === 'completed' ? 'badge--emerald' : d.status === 'failed' ? 'badge--rose' : 'badge--amber'}`}>
                        {d.status}
                      </span>
                    </td>
                    <td className="font-mono">{formatNumber(d.rows_received || 0)}</td>
                    <td style={{ fontSize: '0.82rem', fontWeight: 600 }}>{formatDate(d.created_at)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                        {d.status === 'completed' && (
                          <button
                            className="btn btn-sm btn-yellow"
                            onClick={(e) => {
                              e.stopPropagation()
                              selectStore(d.id)
                              navigate('/briefing')
                            }}
                          >
                            OPEN BRIEFING <ArrowRight size={14} />
                          </button>
                        )}
                        <button
                          className="btn-trash"
                          onClick={(e) => handleDelete(d.id, e)}
                          title="Delete Dataset"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
