import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, Database, Check } from 'lucide-react'
import { checkBackendHealth, loadSampleData, getBusinessProfile } from '../../services/api'

const PAGE_TITLES = {
  '/': 'Overview',
  '/sales': 'Sales Performance',
  '/products': 'Products',
  '/sizes-pricing': 'Sizes & Pricing',
  '/customers': 'Customers',
  '/trends': 'Trends',
  '/upload': 'Upload Data',
  '/settings': 'Settings',
}

export default function Topbar() {
  const location = useLocation()
  const [hasData, setHasData] = useState(false)
  const [loadingSample, setLoadingSample] = useState(false)
  const [sampleLoaded, setSampleLoaded] = useState(false)
  const [businessProfile, setBusinessProfile] = useState({
    business_name: 'Studio Atelier',
    account_type: 'Business Account'
  })

  // Current formatted date matching reference e.g., "Friday, October 24th 2026"
  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  })

  const currentTitle = PAGE_TITLES[location.pathname] || 'Overview'

  useEffect(() => {
    const checkHealth = async () => {
      const res = await checkBackendHealth()
      if (res.ok) {
        setHasData(res.data.has_data || false)
      }
    }
    checkHealth()

    const fetchProfile = async () => {
      const res = await getBusinessProfile()
      if (res.ok && res.data) {
        setBusinessProfile(res.data)
      }
    }
    fetchProfile()

    const handleProfileUpdated = (e) => {
      if (e.detail) {
        setBusinessProfile(prev => ({ ...prev, ...e.detail }))
      } else {
        fetchProfile()
      }
    }
    window.addEventListener('trendpulse_profile_updated', handleProfileUpdated)
    return () => {
      window.removeEventListener('trendpulse_profile_updated', handleProfileUpdated)
    }
  }, [location.pathname])

  const handleQuickLoad = async () => {
    setLoadingSample(true)
    const res = await loadSampleData()
    if (res.ok) {
      setHasData(true)
      setSampleLoaded(true)
      setTimeout(() => {
        window.location.reload()
      }, 500)
    }
    setLoadingSample(false)
  }

  const displayName = businessProfile.business_name || 'My Business'
  const displayRole = businessProfile.account_type || 'Business Account'
  const getInitials = (name) => {
    if (!name) return 'MB'
    const words = name.trim().split(/\s+/)
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }
  const initials = getInitials(displayName)

  return (
    <header className="topbar">
      {/* Left: Title + Date */}
      <div className="topbar-header-left">
        <h1 className="topbar-page-title">{currentTitle}</h1>
        <div className="topbar-date-row">
          <span className="topbar-date-dot" />
          <span className="topbar-date-subtitle">{formattedDate}</span>
        </div>
      </div>

      {/* Right: Actions matching reference (Search, Notification, Profile) */}
      <div className="topbar-actions-right">
        {/* Quick Load Sample Data pill if not loaded */}
        {!hasData && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleQuickLoad}
            disabled={loadingSample}
            style={{ fontSize: '0.74rem' }}
          >
            <Database size={13} />
            <span>{loadingSample ? 'Loading...' : sampleLoaded ? 'Data Loaded!' : 'Load Sample Data'}</span>
          </button>
        )}

        {/* Circular Notification/Mail Button */}
        <button
          className="topbar-circle-btn"
          title="Notifications & Alerts"
          onClick={() => alert('All systems operational. No unread alerts.')}
        >
          <Bell size={18} />
        </button>

        {/* Dynamic Business Profile Pill */}
        <div className="user-profile-pill" title={`${displayName} (${displayRole})`}>
          <div className="user-avatar-circle">
            {initials}
          </div>
          <div className="user-info-text">
            <span className="user-name-title">{displayName}</span>
            <span className="user-role-sub">{displayRole}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
