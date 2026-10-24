import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Plus,
  Copy,
  ExternalLink,
  CheckCircle,
  Clock,
  TrendingUp,
  Package,
  IndianRupee,
  Settings,
  LogOut,
  ChevronRight,
  Eye,
  Pause,
  Play,
  Download,
  ShieldCheck,
  AlertCircle,
  Users,
  BarChart3,
  Store,
  Tag,
  X,
  Sparkles,
} from 'lucide-react'
import { authAPI, businessAPI, dropSellerAPI } from '../api/client'

function InstagramIcon({ style }) {
  return (
    <svg style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  )
}

export default function SellerDashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState('')
  const [copiedLink, setCopiedLink] = useState(null)

  // Create Drop Modal State
  const [showCreateDropModal, setShowCreateDropModal] = useState(false)
  const [newDropTitle, setNewDropTitle] = useState('')
  const [newDropSlug, setNewDropSlug] = useState('')
  const [creatingDrop, setCreatingDrop] = useState(false)
  const [createDropError, setCreateDropError] = useState('')

  const openCreateDropModal = () => {
    setNewDropTitle('')
    setNewDropSlug('')
    setCreateDropError('')
    setShowCreateDropModal(true)
  }

  const handleTitleChange = (val) => {
    setNewDropTitle(val)
    const baseSlug = val
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
    if (baseSlug) {
      setNewDropSlug(baseSlug)
    } else {
      setNewDropSlug('')
    }
  }

  const handleCreateDropSubmit = async (e) => {
    e.preventDefault()
    if (!newDropTitle.trim() || !newDropSlug.trim()) {
      setCreateDropError('Please enter a drop title.')
      return
    }
    setCreatingDrop(true)
    setCreateDropError('')
    try {
      const res = await dropSellerAPI.createDrop(newDropTitle.trim(), newDropSlug.trim())
      setShowCreateDropModal(false)
      navigate(`/seller/lister?dropId=${res.data.id}`)
    } catch (err) {
      setCreateDropError(err.response?.data?.detail || 'Failed to create drop. Slug may already be in use.')
    } finally {
      setCreatingDrop(false)
    }
  }

  useEffect(() => {
    let isMounted = true
    const loadDashboard = async () => {
      try {
        // Check auth & store status
        const meRes = await authAPI.me()
        if (!isMounted) return
        if (!meRes.data?.has_store) {
          navigate('/setup', { replace: true })
          return
        }

        // Load dashboard
        const dashRes = await businessAPI.getDashboard()
        setDashboardData(dashRes.data)
      } catch (err) {
        if (err.response?.status === 401) {
          localStorage.removeItem('tp_token')
          navigate('/login')
          return
        }
        if (isMounted) {
          setError('Failed to load dashboard data.')
        }
      }
      if (isMounted) {
        setLoading(false)
      }
    }

    loadDashboard()
    return () => { isMounted = false }
  }, [navigate])

  const handleCopyLink = (slug) => {
    const link = `${window.location.origin}/drop/${slug}`
    navigator.clipboard.writeText(link)
    setCopiedLink(slug)
    setTimeout(() => setCopiedLink(null), 2000)
  }

  const handleLogout = () => {
    localStorage.removeItem('tp_token')
    navigate('/login')
  }

  const handleToggleDropStatus = async (dropId, currentStatus) => {
    try {
      const newStatus = currentStatus === 'live' ? 'archived' : 'live'
      await dropSellerAPI.updateDropStatus(dropId, newStatus)
      // Reload
      const dashRes = await businessAPI.getDashboard()
      setDashboardData(dashRes.data)
    } catch {
      setError('Failed to update drop status.')
    }
  }

  const handleExportCSV = async () => {
    try {
      const res = await dropSellerAPI.exportShiprocketCSV()
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'shiprocket_orders.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Failed to export CSV.')
    }
  }

  if (loading) {
    return (
      <div style={{
        fontFamily: "'Inter', sans-serif",
        background: '#FAF9F6',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <div style={{ textAlign: 'center', color: '#999' }}>
          <div style={{
            width: 40,
            height: 40,
            border: '3px solid #e5e5e5',
            borderTopColor: '#059669',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px',
          }} />
          <p style={{ fontSize: 14 }}>Loading dashboard...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  const store = dashboardData?.store || {}
  const liveDrops = dashboardData?.live_drops || []
  const previousDrops = dashboardData?.previous_drops || []
  const recentOrders = dashboardData?.recent_orders || []
  const totalRevenue = dashboardData?.total_verified_revenue || 0

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: '#FAF9F6',
      color: '#1a1a1a',
      minHeight: '100vh',
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* ── Header ──────────────────────────────────────────────── */}
      <header style={{
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        background: 'rgba(250, 249, 246, 0.95)',
        backdropFilter: 'blur(20px)',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: 'linear-gradient(135deg, #059669, #047857)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: 13,
              color: '#fff',
            }}>
              TP
            </div>
            <span style={{ fontWeight: 700, fontSize: 17, color: '#1a1a1a', letterSpacing: '-0.5px' }}>
              TrendPulse
            </span>
            <span style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#059669',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              padding: '3px 10px',
              borderRadius: 100,
            }}>
              Dashboard
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <Link
              to="/seller/lister"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 8,
                border: '1px solid #e5e5e5',
                background: '#fff',
                fontSize: 13,
                fontWeight: 500,
                color: '#333',
                textDecoration: 'none',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#333' }}
            >
              <Tag style={{ width: 14, height: 14, color: '#059669' }} />
              Drops Lister
            </Link>
            <Link
              to="/seller/orders"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 8,
                border: '1px solid #e5e5e5',
                background: '#fff',
                fontSize: 13,
                fontWeight: 500,
                color: '#333',
                textDecoration: 'none',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#2563eb'; e.currentTarget.style.color = '#2563eb' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#333' }}
            >
              <Package style={{ width: 14, height: 14, color: '#2563eb' }} />
              Orders
            </Link>
            <button
              onClick={() => navigate('/setup?edit=true')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 8,
                border: '1px solid #e5e5e5',
                background: '#fff',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
                color: '#555',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#555' }}
            >
              <Settings style={{ width: 14, height: 14 }} />
              Edit Store
            </button>
            <button
              onClick={handleLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 8,
                border: '1px solid #e5e5e5',
                background: '#fff',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
                color: '#999',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#EF4444'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#999'}
            >
              <LogOut style={{ width: 14, height: 14 }} />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px 80px' }}>
        {/* Error */}
        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 12,
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            fontSize: 13,
            color: '#DC2626',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 20,
          }}>
            <AlertCircle style={{ width: 16, height: 16 }} />
            <span>{error}</span>
          </div>
        )}

        {/* ── Store Profile Banner ──────────────────────────── */}
        <div style={{
          background: '#fff',
          borderRadius: 20,
          border: '1px solid rgba(0,0,0,0.06)',
          padding: '28px 28px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
          boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: 'linear-gradient(135deg, #059669, #0EA5E9)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 22,
              fontWeight: 700,
            }}>
              {store.name ? store.name[0].toUpperCase() : 'S'}
            </div>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0a0a0a', margin: '0 0 4px', letterSpacing: '-0.3px' }}>
                {store.name || 'Your Store'}
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                {store.instagram_handle && (
                  <span style={{ fontSize: 13, color: '#777', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <InstagramIcon style={{ width: 14, height: 14 }} />
                    @{store.instagram_handle}
                  </span>
                )}
                {store.upi_id && (
                  <span style={{ fontSize: 13, color: '#777', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <IndianRupee style={{ width: 13, height: 13 }} />
                    {store.upi_id}
                  </span>
                )}
                {store.niche && (
                  <span style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: '#7C3AED',
                    background: '#F5F3FF',
                    padding: '3px 10px',
                    borderRadius: 100,
                  }}>
                    {store.niche}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={openCreateDropModal}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '14px 24px',
              borderRadius: 14,
              border: 'none',
              background: '#059669',
              color: '#fff',
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#047857'; e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = '#059669'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            <Plus style={{ width: 18, height: 18 }} />
            Create New Drop
          </button>
        </div>

        {/* ── Stats Cards ──────────────────────────────────── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginBottom: 24,
        }}>
          {[
            {
              label: 'Active Drops',
              value: liveDrops.length,
              icon: <TrendingUp style={{ width: 18, height: 18 }} />,
              accent: '#059669',
              bg: '#f0fdf4',
            },
            {
              label: 'Total Drops',
              value: liveDrops.length + previousDrops.length,
              icon: <Package style={{ width: 18, height: 18 }} />,
              accent: '#7C3AED',
              bg: '#F5F3FF',
            },
            {
              label: 'Recent Orders',
              value: recentOrders.length,
              icon: <Users style={{ width: 18, height: 18 }} />,
              accent: '#0EA5E9',
              bg: '#F0F9FF',
            },
            {
              label: 'Verified Revenue',
              value: `₹${totalRevenue.toLocaleString('en-IN')}`,
              icon: <IndianRupee style={{ width: 18, height: 18 }} />,
              accent: '#F59E0B',
              bg: '#FFFBEB',
            },
          ].map((stat, i) => (
            <div key={i} style={{
              background: '#fff',
              borderRadius: 16,
              border: '1px solid rgba(0,0,0,0.05)',
              padding: '22px 20px',
              boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
            }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: stat.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: stat.accent,
                marginBottom: 12,
              }}>
                {stat.icon}
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#0a0a0a', marginBottom: 2 }}>
                {stat.value}
              </div>
              <div style={{ fontSize: 12, fontWeight: 500, color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* ── Live Drops ───────────────────────────────────── */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22C55E', animation: 'pulse 2s infinite' }} />
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0a0a0a', margin: 0 }}>
              Live Drops
            </h3>
          </div>

          {liveDrops.length === 0 ? (
            <div style={{
              background: '#fff',
              borderRadius: 16,
              border: '1px dashed #d4d4d4',
              padding: '48px 24px',
              textAlign: 'center',
            }}>
              <Package style={{ width: 32, height: 32, color: '#ccc', margin: '0 auto 12px' }} />
              <p style={{ fontSize: 15, color: '#999', marginBottom: 16 }}>No active drops right now.</p>
              <button
                onClick={openCreateDropModal}
                style={{
                  padding: '12px 24px',
                  borderRadius: 12,
                  border: 'none',
                  background: '#059669',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                }}
              >
                <Plus style={{ width: 16, height: 16 }} />
                Create Your First Drop
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {liveDrops.map((drop) => (
                <div key={drop.id} style={{
                  background: '#fff',
                  borderRadius: 16,
                  border: '1px solid rgba(0,0,0,0.06)',
                  padding: '24px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <h4 style={{ fontSize: 17, fontWeight: 600, color: '#0a0a0a', margin: 0 }}>
                          {drop.title}
                        </h4>
                        <span style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: '#22C55E',
                          background: '#f0fdf4',
                          border: '1px solid #bbf7d0',
                          padding: '2px 10px',
                          borderRadius: 100,
                          textTransform: 'uppercase',
                        }}>
                          🟢 Live
                        </span>
                      </div>

                      {/* Progress bar */}
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#999', marginBottom: 4 }}>
                          <span>{drop.claimed_items} of {drop.total_items} pieces claimed</span>
                          <span style={{ fontWeight: 600, color: '#059669' }}>{drop.clearance_pct}%</span>
                        </div>
                        <div style={{ height: 6, background: '#f0f0f0', borderRadius: 10, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            width: `${drop.clearance_pct}%`,
                            background: 'linear-gradient(90deg, #059669, #22C55E)',
                            borderRadius: 10,
                            transition: 'width 0.5s ease',
                          }} />
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, color: '#777' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <IndianRupee style={{ width: 13, height: 13 }} />
                          ₹{(drop.revenue || 0).toLocaleString('en-IN')} collected
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Clock style={{ width: 13, height: 13 }} />
                          {drop.created_at ? new Date(drop.created_at).toLocaleDateString('en-IN') : '-'}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <button
                        onClick={() => navigate(`/seller/lister?dropId=${drop.id}`)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '10px 16px',
                          borderRadius: 10,
                          border: 'none',
                          background: '#059669',
                          cursor: 'pointer',
                          fontSize: 13,
                          fontWeight: 600,
                          color: '#fff',
                          transition: 'all 0.2s',
                          whiteSpace: 'nowrap',
                          boxShadow: '0 2px 6px rgba(5, 150, 105, 0.25)',
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = '#047857' }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = '#059669' }}
                      >
                        <Tag style={{ width: 14, height: 14 }} /> Add / Manage Items
                      </button>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          onClick={() => handleCopyLink(drop.slug)}
                          style={{
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 6,
                            padding: '8px 12px',
                            borderRadius: 8,
                            border: '1px solid #e5e5e5',
                            background: '#fff',
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: 500,
                            color: copiedLink === drop.slug ? '#059669' : '#555',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {copiedLink === drop.slug ? (
                            <><CheckCircle style={{ width: 13, height: 13 }} /> Copied</>
                          ) : (
                            <><Copy style={{ width: 13, height: 13 }} /> Link</>
                          )}
                        </button>
                        <button
                          onClick={() => window.open(`/drop/${drop.slug}`, '_blank')}
                          style={{
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 6,
                            padding: '8px 12px',
                            borderRadius: 8,
                            border: '1px solid #e5e5e5',
                            background: '#fff',
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: 500,
                            color: '#555',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          <Eye style={{ width: 13, height: 13 }} /> Preview
                        </button>
                        <button
                          onClick={() => handleToggleDropStatus(drop.id, drop.status)}
                          style={{
                            padding: '8px 10px',
                            borderRadius: 8,
                            border: '1px solid #FED7AA',
                            background: '#FFFBEB',
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: 500,
                            color: '#D97706',
                            transition: 'all 0.2s',
                          }}
                          title="Archive Drop"
                        >
                          <Pause style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Previous Drops ──────────────────────────────── */}
        {previousDrops.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0a0a0a', marginBottom: 16 }}>
              Previous Drops
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {previousDrops.map((drop) => (
                <div key={drop.id} style={{
                  background: '#fff',
                  borderRadius: 16,
                  border: '1px solid rgba(0,0,0,0.06)',
                  padding: '20px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                    <h4 style={{ fontSize: 15, fontWeight: 600, color: '#0a0a0a', margin: 0 }}>
                      {drop.title}
                    </h4>
                    <span style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: '#999',
                      background: '#f5f5f4',
                      padding: '3px 8px',
                      borderRadius: 100,
                      textTransform: 'uppercase',
                    }}>
                      {drop.status}
                    </span>
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: 12,
                    fontSize: 12,
                    marginBottom: 12,
                  }}>
                    <div>
                      <div style={{ color: '#bbb', marginBottom: 2 }}>Pieces</div>
                      <div style={{ fontWeight: 600, color: '#1a1a1a' }}>{drop.total_items}</div>
                    </div>
                    <div>
                      <div style={{ color: '#bbb', marginBottom: 2 }}>Claimed</div>
                      <div style={{ fontWeight: 600, color: '#059669' }}>{drop.claimed_items}</div>
                    </div>
                    <div>
                      <div style={{ color: '#bbb', marginBottom: 2 }}>Revenue</div>
                      <div style={{ fontWeight: 600, color: '#1a1a1a' }}>₹{(drop.revenue || 0).toLocaleString('en-IN')}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      onClick={() => handleToggleDropStatus(drop.id, drop.status)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        borderRadius: 8,
                        border: '1px solid #e5e5e5',
                        background: '#fff',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 500,
                        color: '#059669',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 4,
                      }}
                    >
                      <Play style={{ width: 12, height: 12 }} /> Reopen
                    </button>
                    <button
                      onClick={() => handleCopyLink(drop.slug)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        borderRadius: 8,
                        border: '1px solid #e5e5e5',
                        background: '#fff',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 500,
                        color: '#555',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 4,
                      }}
                    >
                      <Copy style={{ width: 12, height: 12 }} /> Link
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Recent Orders ───────────────────────────────── */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0a0a0a', margin: 0 }}>
              Recent Orders
            </h3>
            {recentOrders.length > 0 && (
              <button
                onClick={handleExportCSV}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '10px 16px',
                  borderRadius: 10,
                  border: '1px solid #e5e5e5',
                  background: '#fff',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 500,
                  color: '#555',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#555' }}
              >
                <Download style={{ width: 14, height: 14 }} />
                Export Shiprocket CSV
              </button>
            )}
          </div>

          {recentOrders.length === 0 ? (
            <div style={{
              background: '#fff',
              borderRadius: 16,
              border: '1px dashed #d4d4d4',
              padding: '48px 24px',
              textAlign: 'center',
            }}>
              <Users style={{ width: 32, height: 32, color: '#ccc', margin: '0 auto 12px' }} />
              <p style={{ fontSize: 15, color: '#999' }}>No orders yet. Share your drop link to start receiving orders!</p>
            </div>
          ) : (
            <div style={{
              background: '#fff',
              borderRadius: 16,
              border: '1px solid rgba(0,0,0,0.06)',
              overflow: 'hidden',
              boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
            }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                      {['Buyer', 'Item', 'Amount', 'Payment', 'UTR', 'City', 'Date'].map(h => (
                        <th key={h} style={{
                          padding: '14px 16px',
                          textAlign: 'left',
                          fontWeight: 600,
                          color: '#999',
                          fontSize: 11,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {recentOrders.map((order, i) => (
                      <tr key={order.id} style={{
                        borderBottom: i < recentOrders.length - 1 ? '1px solid #f5f5f4' : 'none',
                      }}>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 500, color: '#1a1a1a' }}>{order.buyer_name}</div>
                          <div style={{ fontSize: 12, color: '#999' }}>@{order.buyer_ig}</div>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#555' }}>{order.item_title}</td>
                        <td style={{ padding: '12px 16px', fontWeight: 600, color: '#0a0a0a' }}>₹{order.total_amount?.toLocaleString('en-IN')}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{
                            fontSize: 11,
                            fontWeight: 600,
                            padding: '3px 10px',
                            borderRadius: 100,
                            background: order.payment_status === 'verified' ? '#f0fdf4' : '#FFFBEB',
                            color: order.payment_status === 'verified' ? '#059669' : '#D97706',
                            border: `1px solid ${order.payment_status === 'verified' ? '#bbf7d0' : '#FED7AA'}`,
                          }}>
                            {order.payment_status === 'verified' ? '✓ Verified' : '⏳ Pending'}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#999', fontFamily: 'monospace', fontSize: 12 }}>
                          {order.utr_reference || '—'}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#777' }}>{order.city}, {order.state}</td>
                        <td style={{ padding: '12px 16px', color: '#999', fontSize: 12 }}>
                          {order.created_at ? new Date(order.created_at).toLocaleDateString('en-IN') : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Create Drop Modal ────────────────────────────── */}
      {showCreateDropModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.45)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          zIndex: 100,
        }}>
          <div style={{
            background: '#fff',
            borderRadius: 20,
            width: '100%',
            maxWidth: 480,
            padding: 28,
            boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
            border: '1px solid rgba(0,0,0,0.06)',
            position: 'relative',
          }}>
            <button
              onClick={() => setShowCreateDropModal(false)}
              style={{
                position: 'absolute',
                top: 20,
                right: 20,
                background: '#f5f5f4',
                border: 'none',
                borderRadius: '50%',
                width: 32,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: '#666',
              }}
            >
              <X style={{ width: 16, height: 16 }} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 10,
                background: '#f0fdf4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#059669',
              }}>
                <Sparkles style={{ width: 16, height: 16 }} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#0a0a0a' }}>
                Create New Drop
              </h3>
            </div>
            <p style={{ fontSize: 13, color: '#777', marginBottom: 20, lineHeight: 1.4 }}>
              Launch an Instagram drop campaign. You can immediately upload pieces, set measurements, and generate UPI QR codes.
            </p>

            {createDropError && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 10,
                background: '#FEF2F2',
                border: '1px solid #FECACA',
                color: '#DC2626',
                fontSize: 12,
                marginBottom: 16,
              }}>
                {createDropError}
              </div>
            )}

            <form onSubmit={handleCreateDropSubmit}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 6 }}>
                  Drop Campaign Title *
                </label>
                <input
                  type="text"
                  required
                  value={newDropTitle}
                  onChange={(e) => handleTitleChange(e.target.value)}
                  placeholder="e.g. 90s Carhartt & Racing Tees Drop"
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: 10,
                    border: '1px solid #e5e5e5',
                    fontSize: 14,
                    outline: 'none',
                    boxSizing: 'border-box',
                    background: '#FAFAF9',
                  }}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
              </div>

              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 6 }}>
                  Public Drop URL Slug *
                </label>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: '#FAFAF9',
                  border: '1px solid #e5e5e5',
                  borderRadius: 10,
                  padding: '0 12px',
                }}>
                  <span style={{ fontSize: 13, color: '#999', fontFamily: 'monospace' }}>
                    /drop/
                  </span>
                  <input
                    type="text"
                    required
                    value={newDropSlug}
                    onChange={(e) => setNewDropSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                    placeholder="90s-carhartt-racing-tees"
                    style={{
                      flex: 1,
                      padding: '12px 6px',
                      border: 'none',
                      background: 'transparent',
                      fontSize: 13,
                      outline: 'none',
                      fontFamily: 'monospace',
                      color: '#059669',
                      fontWeight: 600,
                    }}
                  />
                </div>
                <p style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                  This creates your link: {window.location.origin}/drop/{newDropSlug || 'your-drop'}
                </p>
              </div>

              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  type="button"
                  onClick={() => setShowCreateDropModal(false)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: 10,
                    border: '1px solid #e5e5e5',
                    background: '#fff',
                    color: '#666',
                    fontSize: 14,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingDrop}
                  style={{
                    flex: 2,
                    padding: '12px',
                    borderRadius: 10,
                    border: 'none',
                    background: '#059669',
                    color: '#fff',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: creatingDrop ? 'not-allowed' : 'pointer',
                    opacity: creatingDrop ? 0.6 : 1,
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                >
                  {creatingDrop ? 'Creating...' : 'Create & Add Items →'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  )
}
