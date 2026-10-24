import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Store,
  CreditCard,
  Truck,
  CheckCircle,
  ArrowRight,
  AlertCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { authAPI, businessAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'

function InstagramIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  )
}

const NICHE_OPTIONS = [
  { id: 'Curated Vintage Thrift', title: 'Curated Vintage / Thrift', icon: '🧥' },
  { id: 'Y2K & Streetwear', title: 'Y2K & Streetwear', icon: '🛹' },
  { id: 'Upcycled & Reworked', title: 'Upcycled & Reworked', icon: '🪡' },
  { id: 'Deadstock & Surplus Basics', title: 'Deadstock & Surplus', icon: '📦' },
  { id: 'Indie Designer', title: 'Indie Designer', icon: '✨' },
  { id: 'Other', title: 'Other', icon: '🏷️' },
]

const FULFILLMENT_OPTIONS = [
  {
    id: 'self',
    title: 'Self-Pack & Ship',
    description: 'You pack and ship orders yourself using Shiprocket / Delhivery.',
    icon: '📦',
  },
  {
    id: 'supplier',
    title: 'Supplier Dropship',
    description: 'Forward orders to your supplier who ships directly to customers.',
    icon: '🚛',
  },
]

export default function BusinessSetupPage() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [userEmail, setUserEmail] = useState('')

  const [formData, setFormData] = useState({
    businessName: '',
    instagramHandle: '',
    upiId: '',
    shippingFee: '70',
    fulfillmentType: 'self',
    supplierPhone: '',
    niche: 'Curated Vintage Thrift',
    city: '',
  })

  // Check auth and redirect if store already exists (unless in edit mode)
  const isEditMode = window.location.search.includes('edit=true')

  useEffect(() => {
    let isMounted = true
    const checkProfile = async () => {
      try {
        const meRes = await authAPI.me()
        if (!isMounted) return
        setUserEmail(meRes.data?.email || '')

        if (meRes.data?.has_store && !isEditMode) {
          navigate('/dashboard', { replace: true })
          return
        }

        if (isEditMode) {
          try {
            const profRes = await businessAPI.getProfile()
            if (profRes.data) {
              setFormData({
                businessName: profRes.data.name || '',
                instagramHandle: profRes.data.instagram_handle || '',
                upiId: profRes.data.upi_id || '',
                shippingFee: (profRes.data.flat_shipping_fee || 70).toString(),
                fulfillmentType: profRes.data.fulfillment_type || 'self',
                supplierPhone: profRes.data.supplier_phone || '',
                niche: profRes.data.niche || 'Curated Vintage Thrift',
                city: profRes.data.city || '',
              })
            }
          } catch (e) {
            console.error('Failed to load store profile', e)
          }
        } else if (meRes.data?.full_name) {
          // Pre-fill business name from full_name if available
          setFormData(prev => ({ ...prev, businessName: meRes.data.full_name }))
        }
      } catch (err) {
        if (!isMounted) return
        localStorage.removeItem('tp_token')
        navigate('/login', { replace: true })
        return
      }
      if (isMounted) {
        setLoading(false)
      }
    }

    checkProfile()
    return () => { isMounted = false }
  }, [navigate, isEditMode])

  const updateField = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Basic validation
    if (!formData.businessName.trim()) {
      setError('Please enter your business name.')
      return
    }
    if (!formData.instagramHandle.trim()) {
      setError('Please enter your Instagram handle.')
      return
    }
    if (!formData.upiId.trim()) {
      setError('Please enter your UPI ID for receiving payments.')
      return
    }

    setSubmitting(true)
    try {
      await businessAPI.setupProfile({
        business_name: formData.businessName.trim(),
        instagram_handle: formData.instagramHandle.trim().replace(/^@/, ''),
        upi_id: formData.upiId.trim(),
        flat_shipping_fee: parseFloat(formData.shippingFee) || 70,
        fulfillment_type: formData.fulfillmentType,
        supplier_phone: formData.fulfillmentType === 'supplier' ? formData.supplierPhone : null,
        niche: formData.niche,
        city: formData.city.trim() || 'Delhi',
      })
      try {
        await refreshUser()
      } catch {}
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Setup failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const inputStyle = {
    width: '100%',
    padding: '14px 16px',
    borderRadius: 12,
    border: '1.5px solid #e5e5e5',
    fontSize: 15,
    color: '#1a1a1a',
    background: '#FAFAF9',
    outline: 'none',
    transition: 'all 0.2s ease',
    boxSizing: 'border-box',
  }

  const labelStyle = {
    display: 'block',
    fontSize: 13,
    fontWeight: 600,
    color: '#555',
    marginBottom: 6,
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
          <p style={{ fontSize: 14 }}>Loading...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

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
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>
              {userEmail}
            </span>
            <button
              type="button"
              onClick={async () => {
                try {
                  await authAPI.logout()
                } catch {}
                localStorage.removeItem('tp_token')
                window.location.href = '/login'
              }}
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: '#6b7280',
                background: '#ffffff',
                border: '1px solid #e5e7eb',
                padding: '5px 12px',
                borderRadius: 7,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Sign Out
            </button>
            {isEditMode && (
              <Link
                to="/dashboard"
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#059669',
                  textDecoration: 'none',
                  padding: '6px 12px',
                  borderRadius: 8,
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                }}
              >
                ← Back to Dashboard
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* ── Setup Content ───────────────────────────────────────── */}
      <div style={{
        maxWidth: 600,
        margin: '0 auto',
        padding: '48px 20px 80px',
      }}>
        {/* Progress (hide in edit mode) */}
        {!isEditMode && (
          <>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 12,
            }}>
              <div style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: '#059669',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 700,
              }}>✓</div>
              <div style={{ height: 2, flex: 1, background: '#059669', borderRadius: 2 }} />
              <div style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: '#059669',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 700,
              }}>2</div>
              <div style={{ height: 2, flex: 1, background: '#e5e5e5', borderRadius: 2 }} />
              <div style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: '#f5f5f4',
                color: '#bbb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 700,
              }}>3</div>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 11,
              color: '#999',
              marginBottom: 36,
              fontWeight: 500,
            }}>
              <span style={{ color: '#059669' }}>Account Created</span>
              <span style={{ color: '#059669', fontWeight: 600 }}>Business Setup</span>
              <span>Dashboard</span>
            </div>
          </>
        )}

        {/* Welcome */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 8,
        }}>
          <Sparkles style={{ width: 24, height: 24, color: '#059669' }} />
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.5px', color: '#0a0a0a', margin: 0 }}>
            {isEditMode ? 'Update Store Profile' : 'Set Up Your Store'}
          </h1>
        </div>
        <p style={{ fontSize: 15, color: '#777', marginBottom: 32, lineHeight: 1.5 }}>
          {isEditMode
            ? 'Update your business identity, direct personal UPI ID, and shipping defaults.'
            : 'Tell us about your business. This info is used across all your drops and only needs to be entered once.'}
        </p>

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
            alignItems: 'flex-start',
            gap: 8,
            marginBottom: 20,
          }}>
            <AlertCircle style={{ width: 16, height: 16, flexShrink: 0, marginTop: 1 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* ── Business Identity ───────────────────────────── */}
          <div style={{
            background: '#fff',
            borderRadius: 20,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '28px 24px',
            marginBottom: 20,
            boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <Store style={{ width: 18, height: 18, color: '#059669' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a' }}>Business Identity</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={labelStyle}>
                  Business / Brand Name <span style={{ color: '#EF4444' }}>*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.businessName}
                  onChange={(e) => updateField('businessName', e.target.value)}
                  placeholder="e.g. Vintage Curations"
                  style={inputStyle}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
              </div>

              <div>
                <label style={labelStyle}>
                  Instagram Handle <span style={{ color: '#EF4444' }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <span style={{
                    position: 'absolute',
                    left: 16,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#bbb',
                    fontSize: 15,
                  }}>@</span>
                  <input
                    type="text"
                    required
                    value={formData.instagramHandle}
                    onChange={(e) => updateField('instagramHandle', e.target.value.replace(/^@/, ''))}
                    placeholder="vintage.curations"
                    style={{ ...inputStyle, paddingLeft: 36 }}
                    onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                  />
                </div>
              </div>

              <div>
                <label style={labelStyle}>City</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  placeholder="Delhi"
                  style={inputStyle}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
              </div>
            </div>
          </div>

          {/* ── Niche ──────────────────────────────────────── */}
          <div style={{
            background: '#fff',
            borderRadius: 20,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '28px 24px',
            marginBottom: 20,
            boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Sparkles style={{ width: 18, height: 18, color: '#7C3AED' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a' }}>Your Niche</span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))',
              gap: 8,
            }}>
              {NICHE_OPTIONS.map((niche) => (
                <button
                  key={niche.id}
                  type="button"
                  onClick={() => updateField('niche', niche.id)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 12,
                    border: `1.5px solid ${formData.niche === niche.id ? '#059669' : '#e5e5e5'}`,
                    background: formData.niche === niche.id ? '#f0fdf4' : '#FAFAF9',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span style={{ fontSize: 18 }}>{niche.icon}</span>
                  <span style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: formData.niche === niche.id ? '#047857' : '#555',
                  }}>
                    {niche.title}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* ── Payments ───────────────────────────────────── */}
          <div style={{
            background: '#fff',
            borderRadius: 20,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '28px 24px',
            marginBottom: 20,
            boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <CreditCard style={{ width: 18, height: 18, color: '#0EA5E9' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a' }}>Payments</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={labelStyle}>
                  Payee UPI ID / VPA <span style={{ color: '#EF4444' }}>*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.upiId}
                  onChange={(e) => updateField('upiId', e.target.value)}
                  placeholder="yourname@okaxis"
                  style={inputStyle}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, fontSize: 12, color: '#999' }}>
                  <ShieldCheck style={{ width: 13, height: 13, color: '#059669' }} />
                  <span>100% direct P2P — all payments go straight to your bank</span>
                </div>
              </div>

              <div>
                <label style={labelStyle}>
                  Flat Shipping Fee (₹)
                </label>
                <input
                  type="number"
                  value={formData.shippingFee}
                  onChange={(e) => updateField('shippingFee', e.target.value)}
                  placeholder="70"
                  style={inputStyle}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
              </div>
            </div>
          </div>

          {/* ── Fulfillment ────────────────────────────────── */}
          <div style={{
            background: '#fff',
            borderRadius: 20,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '28px 24px',
            marginBottom: 32,
            boxShadow: '0 1px 4px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Truck style={{ width: 18, height: 18, color: '#F59E0B' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a' }}>Fulfillment</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {FULFILLMENT_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => updateField('fulfillmentType', opt.id)}
                  style={{
                    padding: '16px 18px',
                    borderRadius: 14,
                    border: `1.5px solid ${formData.fulfillmentType === opt.id ? '#059669' : '#e5e5e5'}`,
                    background: formData.fulfillmentType === opt.id ? '#f0fdf4' : '#FAFAF9',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 12,
                  }}
                >
                  <span style={{ fontSize: 22, marginTop: 2 }}>{opt.icon}</span>
                  <div>
                    <div style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: formData.fulfillmentType === opt.id ? '#047857' : '#1a1a1a',
                      marginBottom: 2,
                    }}>
                      {opt.title}
                    </div>
                    <div style={{ fontSize: 13, color: '#999', lineHeight: 1.4 }}>
                      {opt.description}
                    </div>
                  </div>
                </button>
              ))}

              {formData.fulfillmentType === 'supplier' && (
                <div style={{ marginTop: 8 }}>
                  <label style={labelStyle}>Supplier WhatsApp Number</label>
                  <input
                    type="text"
                    value={formData.supplierPhone}
                    onChange={(e) => updateField('supplierPhone', e.target.value)}
                    placeholder="+91 98765 43210"
                    style={inputStyle}
                    onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* ── Submit ─────────────────────────────────────── */}
          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%',
              padding: '16px 24px',
              borderRadius: 14,
              border: 'none',
              background: '#059669',
              color: '#fff',
              fontSize: 16,
              fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer',
              opacity: submitting ? 0.6 : 1,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              boxShadow: '0 4px 14px rgba(5, 150, 105, 0.25)',
            }}
            onMouseEnter={(e) => { if (!submitting) e.target.style.background = '#047857' }}
            onMouseLeave={(e) => { if (!submitting) e.target.style.background = '#059669' }}
          >
            {submitting ? (
              <span>{isEditMode ? 'Saving changes...' : 'Setting up your store...'}</span>
            ) : (
              <>
                <CheckCircle style={{ width: 18, height: 18 }} />
                <span>{isEditMode ? 'Save Changes & Return to Dashboard' : 'Complete Setup & Go to Dashboard'}</span>
                <ArrowRight style={{ width: 18, height: 18 }} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
