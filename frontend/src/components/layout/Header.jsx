import { useLocation } from 'react-router-dom'
import { Bell, Sparkles } from 'lucide-react'
import { useStore } from '../../context/StoreContext'
import './Header.css'

const pageTitles = {
  '/': 'STORE REPOSITORIES',
  '/briefing': 'CEO EXECUTIVE BRIEFING',
  '/copilot': 'AI FASHION COPILOT WORKSPACE',
  '/simulator': 'WHAT-IF PRICE ELASTICITY LAB',
  '/inventory': 'INVENTORY & SIZE CURVE HEALTH',
  '/economics': 'UNIT ECONOMICS & CASH LEAKS',
  '/trends': 'VIRAL TRENDS & AESTHETIC VELOCITY',
  '/customers': 'CUSTOMER RETENTION & VIP CHURN',
  '/upload': 'DATA INGESTION LAB',
  '/login': 'MERCHANT ACCESS',
}

export default function Header() {
  const location = useLocation()
  const { dataset, activeDatasetId } = useStore()

  // Check for /dataset/:id pattern
  const isDatasetPage = location.pathname.startsWith('/dataset/')
  const title = pageTitles[location.pathname] || (isDatasetPage ? 'DATASET EXECUTIVE BRIEFING' : 'TRENDPULSE INTELLIGENCE')

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="header-title">{title}</h1>
      </div>
      <div className="header-right">
        {dataset && (
          <div className="header-badge">
            <span className="header-badge-dot" />
            <span>ACTIVE: #{activeDatasetId}</span>
          </div>
        )}
        <button className="header-icon-btn" title="Alerts">
          <Bell size={18} strokeWidth={2.5} />
        </button>
        <div className="header-avatar" title="Merchant Founder">
          <span>US</span>
        </div>
      </div>
    </header>
  )
}
