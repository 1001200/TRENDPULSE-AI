import { NavLink, useNavigate } from 'react-router-dom'
import {
  Zap, MessageSquare, Sliders, Shirt, IndianRupee,
  Sparkles, Heart, Database, Upload, LogOut, ChevronDown
} from 'lucide-react'
import { useStore } from '../../context/StoreContext'
import './Sidebar.css'

const operationsNav = [
  { to: '/briefing',   icon: Zap,           label: 'CEO BRIEFING',      badge: '60-Sec' },
  { to: '/copilot',    icon: MessageSquare, label: 'AI COPILOT',        badge: 'Chat' },
  { to: '/simulator',  icon: Sliders,       label: 'WHAT-IF SIMULATOR', badge: 'Model' },
  { to: '/inventory',  icon: Shirt,         label: 'INVENTORY & SIZES' },
  { to: '/economics',  icon: IndianRupee,   label: 'UNIT ECONOMICS' },
  { to: '/trends',     icon: Sparkles,      label: 'VIRAL TRENDS' },
  { to: '/customers',  icon: Heart,         label: 'CUSTOMER CHURN' },
]

const managementNav = [
  { to: '/analyst', icon: Sparkles, label: 'AUTO ANALYST', badge: 'NEW' },
  { to: '/admin',   icon: Database, label: 'ALL DATASETS' },
  { to: '/upload',  icon: Upload,   label: 'UPLOAD DATA' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const { datasets, activeDatasetId, selectStore, dataset } = useStore()

  const handleLogout = () => {
    localStorage.removeItem('tp_token')
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Bauhaus Geometric Brand Trio */}
      <div className="sidebar-brand">
        <div className="bauhaus-logo-trio">
          <span className="bauhaus-shape bauhaus-shape--circle" />
          <span className="bauhaus-shape bauhaus-shape--square" />
          <span className="bauhaus-shape bauhaus-shape--triangle" />
        </div>
        <div className="sidebar-brand-text">
          <div className="sidebar-title">TRENDPULSE</div>
          <div className="sidebar-subtitle">FASHION INTELLIGENCE</div>
        </div>
      </div>

      {/* Active Store Selector */}
      <div className="sidebar-store-selector">
        <label className="sidebar-store-label">ACTIVE STORE DATASET</label>
        <div className="sidebar-select-wrap">
          <select
            className="sidebar-store-select"
            value={activeDatasetId || ''}
            onChange={(e) => selectStore(e.target.value)}
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                #{d.id} • {d.filename.slice(0, 20)}
              </option>
            ))}
            {datasets.length === 0 && (
              <option value="">No datasets found</option>
            )}
          </select>
          <ChevronDown size={14} className="select-arrow" />
        </div>
      </div>

      {/* Scrollable Nav Area */}
      <div className="sidebar-nav-scroll">
        {/* Operations Section */}
        <div className="nav-section-label">OPERATIONS</div>
        <nav className="sidebar-nav">
          {operationsNav.map(({ to, icon: Icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
            >
              <Icon size={16} strokeWidth={2.5} />
              <span className="nav-link-text">{label}</span>
              {badge && <span className="nav-item-badge">{badge}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Management Section */}
        <div className="nav-section-label" style={{ marginTop: 20 }}>CATALOG DATA</div>
        <nav className="sidebar-nav">
          {managementNav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
            >
              <Icon size={16} strokeWidth={2.5} />
              <span className="nav-link-text">{label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <button className="nav-link nav-link--danger" onClick={handleLogout}>
          <LogOut size={16} strokeWidth={2.5} />
          <span>LOGOUT</span>
        </button>
      </div>
    </aside>
  )
}
