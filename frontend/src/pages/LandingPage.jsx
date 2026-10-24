import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  ArrowRight,
  ShieldCheck,
  Clock,
  Truck,
  Zap,
  ChevronDown,
  QrCode,
  Package,
  IndianRupee,
  Smartphone,
  CheckCircle,
  Star,
  TrendingUp,
  Users,
} from 'lucide-react'

function InstagramIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  )
}

export default function LandingPage() {
  const { user, isAuthenticated, logout } = useAuth()
  const [openFaq, setOpenFaq] = useState(0)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const features = [
    {
      icon: <QrCode className="w-6 h-6" />,
      title: 'Pre-Filled UPI QR Codes',
      description: 'Amount auto-locks in GPay / PhonePe — buyers never calculate or mistype prices. Zero payment friction.',
      accent: '#059669',
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: 'Persistent Inventory',
      description: 'No timers. No stress. Drops stay open until sold out or manually closed by you.',
      accent: '#7C3AED',
    },
    {
      icon: <IndianRupee className="w-6 h-6" />,
      title: '100% Direct P2P Payments',
      description: 'Every rupee goes straight to your UPI. Zero platform commission. Zero escrow delays.',
      accent: '#0EA5E9',
    },
    {
      icon: <Truck className="w-6 h-6" />,
      title: 'One-Click Dispatch',
      description: 'Shiprocket CSV export with addresses pre-filled. Print courier slips in seconds.',
      accent: '#F59E0B',
    },
  ]

  const stats = [
    { value: '0%', label: 'Commission', icon: <IndianRupee className="w-4 h-4" /> },
    { value: '₹70', label: 'Flat Shipping', icon: <Package className="w-4 h-4" /> },
    { value: '30s', label: 'Per Listing', icon: <Zap className="w-4 h-4" /> },
    { value: '100%', label: 'Direct UPI', icon: <ShieldCheck className="w-4 h-4" /> },
  ]

  const steps = [
    {
      number: '01',
      title: 'Sign Up Free',
      description: 'Create your seller account in 30 seconds with just your email.',
    },
    {
      number: '02',
      title: 'Setup Your Store',
      description: 'Enter your business name, Instagram handle, and UPI ID — one time only.',
    },
    {
      number: '03',
      title: 'Create a Drop',
      description: 'List your pieces with measurements, prices, and photos. Takes under 10 minutes.',
    },
    {
      number: '04',
      title: 'Share & Sell',
      description: 'Get a custom link, share on your Instagram story, and watch orders come in.',
    },
  ]

  const faqs = [
    {
      q: 'How does the 10-minute atomic lock eliminate buyer ghosting?',
      a: 'When a buyer clicks your drop link and selects a 1-of-1 piece, TrendPulse freezes that item exclusively to their session for 10 minutes. A visible countdown creates authentic urgency. If payment completes, the item is SOLD. If they abandon, the hold releases automatically.',
    },
    {
      q: 'Does TrendPulse take a commission on my sales?',
      a: 'None. TrendPulse charges 0% commission. All transactions go through direct peer-to-peer UPI straight to your VPA. 100% of the price lands in your bank account.',
    },
    {
      q: 'Do I need a registered business or GST to sell?',
      a: 'No. TrendPulse is built for solo Indian vintage curators, thrift archivists, and streetwear creators. All you need is your UPI ID and an Instagram profile.',
    },
    {
      q: 'How does the ₹70 flat shipping work?',
      a: 'During checkout, TrendPulse automatically collects the buyer\'s shipping address and adds ₹70 to their total. When ready to pack, export a 1-click Shiprocket CSV to print courier slips instantly.',
    },
    {
      q: 'How fast can I list 15 pieces?',
      a: 'Under 10 minutes. The rapid lister captures only what thrift buyers care about: photos, garment category, chest & length measurements, condition grade, and price.',
    },
  ]

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: '#FAF9F6',
      color: '#1a1a1a',
      minHeight: '100vh',
      margin: 0,
      padding: 0,
    }}>
      {/* Google Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />

      {/* ── Navbar ─────────────────────────────────────────────────── */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: scrolled ? 'rgba(250, 249, 246, 0.95)' : 'transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(0,0,0,0.06)' : '1px solid transparent',
        transition: 'all 0.3s ease',
        padding: '0 24px',
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          height: 72,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #059669, #047857)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: 14,
              color: '#fff',
              letterSpacing: '-0.5px',
            }}>
              TP
            </div>
            <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.5px', color: '#1a1a1a' }}>
              TrendPulse
            </span>
          </div>

          {/* Nav Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {isAuthenticated ? (
              <>
                <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>
                  {user?.email}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: '#6b7280',
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    padding: '8px 14px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.borderColor = '#d1d5db'
                    e.target.style.color = '#374151'
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.borderColor = '#e5e7eb'
                    e.target.style.color = '#6b7280'
                  }}
                >
                  Sign Out
                </button>
                <Link
                  to="/dashboard"
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: '#fff',
                    background: '#059669',
                    textDecoration: 'none',
                    padding: '10px 20px',
                    borderRadius: 10,
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.background = '#047857'
                    e.target.style.transform = 'translateY(-1px)'
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.background = '#059669'
                    e.target.style.transform = 'translateY(0)'
                  }}
                >
                  Go to Dashboard →
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  style={{
                    fontSize: 14,
                    fontWeight: 500,
                    color: '#555',
                    textDecoration: 'none',
                    padding: '8px 16px',
                    borderRadius: 8,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.color = '#059669'}
                  onMouseLeave={(e) => e.target.style.color = '#555'}
                >
                  Log In
                </Link>
                <Link
                  to="/signup"
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: '#fff',
                    background: '#059669',
                    textDecoration: 'none',
                    padding: '10px 20px',
                    borderRadius: 10,
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.background = '#047857'
                    e.target.style.transform = 'translateY(-1px)'
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.background = '#059669'
                    e.target.style.transform = 'translateY(0)'
                  }}
                >
                  Get Started Free →
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '80px 24px 60px',
        textAlign: 'center',
      }}>
        {/* Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 16px',
          borderRadius: 100,
          background: '#fff',
          border: '1px solid rgba(5, 150, 105, 0.15)',
          fontSize: 13,
          fontWeight: 500,
          color: '#059669',
          marginBottom: 32,
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#059669', animation: 'pulse 2s infinite' }} />
          Built for Indian Instagram Curators & Thrift Sellers
        </div>

        {/* Headline */}
        <h1 style={{
          fontSize: 'clamp(36px, 5vw, 64px)',
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: '-1.5px',
          color: '#0a0a0a',
          margin: '0 auto 24px',
          maxWidth: 800,
        }}>
          Turn Instagram Reel Views{' '}
          <span style={{
            background: 'linear-gradient(135deg, #059669, #0EA5E9)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            into Direct UPI Sales
          </span>
        </h1>

        {/* Subheadline */}
        <p style={{
          fontSize: 'clamp(16px, 2vw, 20px)',
          color: '#666',
          maxWidth: 640,
          margin: '0 auto 40px',
          lineHeight: 1.6,
          fontWeight: 400,
        }}>
          Zero DM ghosting. Pre-filled dynamic UPI QR codes for each piece.
          100% direct bank deposits. Zero platform commission.
        </p>

        {/* CTA Buttons */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          flexWrap: 'wrap',
          marginBottom: 60,
        }}>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '16px 36px',
                borderRadius: 14,
                background: '#059669',
                color: '#fff',
                fontSize: 16,
                fontWeight: 600,
                textDecoration: 'none',
                boxShadow: '0 4px 14px rgba(5, 150, 105, 0.3)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#047857'
                e.target.style.transform = 'translateY(-2px)'
                e.target.style.boxShadow = '0 6px 20px rgba(5, 150, 105, 0.4)'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#059669'
                e.target.style.transform = 'translateY(0)'
                e.target.style.boxShadow = '0 4px 14px rgba(5, 150, 105, 0.3)'
              }}
            >
              Go to Your Dashboard
              <ArrowRight style={{ width: 18, height: 18 }} />
            </Link>
          ) : (
            <>
              <Link
                to="/signup"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '16px 32px',
                  borderRadius: 14,
                  background: '#059669',
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 600,
                  textDecoration: 'none',
                  boxShadow: '0 4px 14px rgba(5, 150, 105, 0.3)',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#047857'
                  e.target.style.transform = 'translateY(-2px)'
                  e.target.style.boxShadow = '0 6px 20px rgba(5, 150, 105, 0.4)'
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = '#059669'
                  e.target.style.transform = 'translateY(0)'
                  e.target.style.boxShadow = '0 4px 14px rgba(5, 150, 105, 0.3)'
                }}
              >
                Get Started Free
                <ArrowRight style={{ width: 18, height: 18 }} />
              </Link>
              <Link
                to="/login"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '16px 28px',
                  borderRadius: 14,
                  background: '#fff',
                  color: '#333',
                  fontSize: 16,
                  fontWeight: 500,
                  textDecoration: 'none',
                  border: '1px solid #e0e0e0',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = '#059669'
                  e.target.style.color = '#059669'
                }}
                onMouseLeave={(e) => {
                  e.target.style.borderColor = '#e0e0e0'
                  e.target.style.color = '#333'
                }}
              >
                Log In
              </Link>
            </>
          )}
        </div>

        {/* Stats Bar */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 16,
          maxWidth: 640,
          margin: '0 auto',
        }}>
          {stats.map((stat, i) => (
            <div key={i} style={{
              background: '#fff',
              borderRadius: 14,
              padding: '20px 16px',
              border: '1px solid rgba(0,0,0,0.05)',
              textAlign: 'center',
              boxShadow: '0 1px 4px rgba(0,0,0,0.03)',
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: 8,
                color: '#059669',
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
      </section>

      {/* ── Features ───────────────────────────────────────────────── */}
      <section style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '80px 24px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <h2 style={{
            fontSize: 'clamp(28px, 3.5vw, 40px)',
            fontWeight: 700,
            letterSpacing: '-0.8px',
            color: '#0a0a0a',
            marginBottom: 12,
          }}>
            Everything You Need to Sell
          </h2>
          <p style={{ fontSize: 16, color: '#777', maxWidth: 500, margin: '0 auto' }}>
            The complete checkout operating system for 1-of-1 vintage drops on Instagram.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 20,
        }}>
          {features.map((f, i) => (
            <div key={i} style={{
              background: '#fff',
              borderRadius: 20,
              padding: '32px 28px',
              border: '1px solid rgba(0,0,0,0.05)',
              transition: 'all 0.3s ease',
              cursor: 'default',
              boxShadow: '0 1px 4px rgba(0,0,0,0.03)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.08)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.03)'
            }}
            >
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                background: `${f.accent}10`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: f.accent,
                marginBottom: 20,
              }}>
                {f.icon}
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 600, color: '#0a0a0a', marginBottom: 8, letterSpacing: '-0.3px' }}>
                {f.title}
              </h3>
              <p style={{ fontSize: 14, color: '#777', lineHeight: 1.6, margin: 0 }}>
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────────── */}
      <section style={{
        background: '#fff',
        padding: '80px 24px',
        borderTop: '1px solid rgba(0,0,0,0.04)',
        borderBottom: '1px solid rgba(0,0,0,0.04)',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <h2 style={{
              fontSize: 'clamp(28px, 3.5vw, 40px)',
              fontWeight: 700,
              letterSpacing: '-0.8px',
              color: '#0a0a0a',
              marginBottom: 12,
            }}>
              How It Works
            </h2>
            <p style={{ fontSize: 16, color: '#777', maxWidth: 480, margin: '0 auto' }}>
              From signup to first sale in under 15 minutes.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 28,
          }}>
            {steps.map((step, i) => (
              <div key={i} style={{
                position: 'relative',
                padding: '32px 24px',
                background: '#FAF9F6',
                borderRadius: 20,
                border: '1px solid rgba(0,0,0,0.05)',
                textAlign: 'center',
              }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #059669, #047857)',
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: 16,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                  letterSpacing: '-0.5px',
                }}>
                  {step.number}
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 600, color: '#0a0a0a', marginBottom: 8 }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: 14, color: '#777', lineHeight: 1.5, margin: 0 }}>
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Buyer Flow Preview ──────────────────────────────────────── */}
      <section style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '80px 24px',
      }}>
        <div style={{
          background: '#fff',
          borderRadius: 24,
          padding: '48px 40px',
          border: '1px solid rgba(0,0,0,0.05)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 40,
          alignItems: 'center',
          boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
        }}>
          <div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '5px 12px',
              borderRadius: 100,
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              fontSize: 12,
              fontWeight: 600,
              color: '#059669',
              marginBottom: 20,
            }}>
              <Smartphone style={{ width: 14, height: 14 }} />
              Buyer Experience
            </div>
            <h2 style={{
              fontSize: 'clamp(24px, 3vw, 36px)',
              fontWeight: 700,
              letterSpacing: '-0.8px',
              color: '#0a0a0a',
              marginBottom: 16,
              lineHeight: 1.2,
            }}>
              Instagram Story → UPI Payment in 60 Seconds
            </h2>
            <p style={{ fontSize: 15, color: '#777', lineHeight: 1.7, marginBottom: 24 }}>
              Buyers tap your story link, browse your curated drop, select a 1-of-1 piece,
              fill their address, and pay instantly via pre-filled UPI — all inside Instagram's in-app browser.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                'Tap story link → opens drop storefront',
                'Select piece → 10-min atomic hold starts',
                'Fill address → pre-filled UPI QR appears',
                'Pay via GPay/PhonePe → piece is SOLD',
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <CheckCircle style={{ width: 18, height: 18, color: '#059669', flexShrink: 0 }} />
                  <span style={{ fontSize: 14, color: '#555' }}>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{
            background: '#FAF9F6',
            borderRadius: 20,
            padding: '32px 24px',
            border: '1px solid rgba(0,0,0,0.06)',
            textAlign: 'center',
          }}>
            <div style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #059669, #0EA5E9)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}>
              <InstagramIcon className="w-6 h-6" />
            </div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#999', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 8 }}>
              Buyer Journey
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {['📱 Instagram Story Swipe', '🛍️ Browse Curated Drop', '⏱️ 10-Min Atomic Hold', '💳 Pre-Filled UPI Pay', '✅ Confirmed & Shipped'].map((step, i) => (
                <div key={i} style={{
                  padding: '12px 16px',
                  background: '#fff',
                  borderRadius: 10,
                  fontSize: 14,
                  fontWeight: 500,
                  color: '#333',
                  border: '1px solid rgba(0,0,0,0.04)',
                }}>
                  {step}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ ─────────────────────────────────────────────────────── */}
      <section style={{
        background: '#fff',
        padding: '80px 24px',
        borderTop: '1px solid rgba(0,0,0,0.04)',
      }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{
              fontSize: 'clamp(28px, 3.5vw, 40px)',
              fontWeight: 700,
              letterSpacing: '-0.8px',
              color: '#0a0a0a',
              marginBottom: 12,
            }}>
              Frequently Asked Questions
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {faqs.map((faq, i) => (
              <div key={i} style={{
                background: openFaq === i ? '#f8faf8' : '#FAF9F6',
                borderRadius: 14,
                border: `1px solid ${openFaq === i ? 'rgba(5,150,105,0.2)' : 'rgba(0,0,0,0.05)'}`,
                overflow: 'hidden',
                transition: 'all 0.3s ease',
              }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%',
                    padding: '18px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 16,
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a' }}>
                    {faq.q}
                  </span>
                  <ChevronDown style={{
                    width: 18,
                    height: 18,
                    color: '#999',
                    flexShrink: 0,
                    transform: openFaq === i ? 'rotate(180deg)' : 'rotate(0)',
                    transition: 'transform 0.2s ease',
                  }} />
                </button>
                {openFaq === i && (
                  <div style={{
                    padding: '0 20px 18px',
                    fontSize: 14,
                    color: '#666',
                    lineHeight: 1.7,
                  }}>
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────── */}
      <section style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '80px 24px',
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #059669, #047857)',
          borderRadius: 28,
          padding: '64px 40px',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Decorative glow */}
          <div style={{
            position: 'absolute',
            top: -80,
            right: -80,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.08)',
          }} />
          <div style={{
            position: 'absolute',
            bottom: -60,
            left: -60,
            width: 160,
            height: 160,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.06)',
          }} />

          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 44px)',
            fontWeight: 700,
            color: '#fff',
            letterSpacing: '-1px',
            marginBottom: 16,
            position: 'relative',
          }}>
            Ready to Start Selling?
          </h2>
          <p style={{
            fontSize: 17,
            color: 'rgba(255,255,255,0.85)',
            maxWidth: 500,
            margin: '0 auto 32px',
            lineHeight: 1.6,
            position: 'relative',
          }}>
            Join hundreds of independent clothing brands using AI market intelligence to scale drops and optimize inventory demand.
          </p>
          <Link
            to={isAuthenticated ? "/dashboard" : "/signup"}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '16px 36px',
              borderRadius: 14,
              background: '#fff',
              color: '#059669',
              fontSize: 16,
              fontWeight: 700,
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
              transition: 'all 0.2s',
              position: 'relative',
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.2)'
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 4px 14px rgba(0,0,0,0.15)'
            }}
          >
            {isAuthenticated ? "Go to Your Dashboard" : "Get Started with TrendPulse"}
            <ArrowRight style={{ width: 18, height: 18 }} />
          </Link>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer style={{
        background: '#fff',
        borderTop: '1px solid rgba(0,0,0,0.06)',
        padding: '32px 24px',
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#999' }}>
            <ShieldCheck style={{ width: 16, height: 16, color: '#059669' }} />
            Market Velocity Intelligence • Predictive Demand Modeling • Enterprise Data Security
          </div>
          <span style={{ fontSize: 13, color: '#bbb' }}>
            © 2026 TrendPulse
          </span>
        </div>
      </footer>

      {/* Animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}
