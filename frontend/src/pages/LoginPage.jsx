import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import {
  LogIn,
  UserPlus,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Eye,
  EyeOff,
  Check,
  X,
  User,
  Plus,
  Activity,
} from 'lucide-react'
import { authAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LoginPage({ initialMode = 'login' }) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user, loading: authLoading, login, signup, logout } = useAuth()

  const [isRegister, setIsRegister] = useState(
    initialMode === 'register' || searchParams.get('mode') === 'register'
  )
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Redirect immediately if already authenticated (unless explicit logout/switch requested)
  useEffect(() => {
    if (searchParams.get('logout') === 'true' || searchParams.get('switch') === 'true') {
      logout()
      return
    }
    if (!authLoading && user) {
      const from = searchParams.get('from')
      if (from && !from.startsWith('/login') && !from.startsWith('/signup')) {
        navigate(from, { replace: true })
        return
      }
      if (user.onboarding_status === 'completed' || user.has_store) {
        navigate('/dashboard', { replace: true })
      } else {
        navigate('/setup', { replace: true })
      }
    }
  }, [user, authLoading, navigate, searchParams, logout])

  // Password strength checks for strong password instructions
  const hasMinLength = password.length >= 8
  const hasNumber = /\d/.test(password)
  const hasLetterOrSpecial = (/[a-zA-Z]/.test(password) && /[^a-zA-Z0-9]/.test(password)) || (/[a-z]/.test(password) && /[A-Z]/.test(password))
  const strengthScore = [hasMinLength, hasNumber, hasLetterOrSpecial].filter(Boolean).length

  const getStrengthLabel = () => {
    if (!password) return { label: '', color: '#e5e5e5', width: '0%' }
    if (strengthScore === 1) return { label: 'Weak', color: '#ef4444', width: '33%' }
    if (strengthScore === 2) return { label: 'Medium', color: '#f59e0b', width: '66%' }
    return { label: 'Strong', color: '#059669', width: '100%' }
  }

  const trackAuthEvent = (eventName) => {
    try {
      window.dispatchEvent(
        new CustomEvent('tp_auth_analytics', { detail: { event: eventName, timestamp: Date.now() } })
      )
    } catch {}
  }

  const navigatePostAuth = (authenticatedUser) => {
    const from = searchParams.get('from')
    if (from && !from.startsWith('/login') && !from.startsWith('/signup')) {
      navigate(from, { replace: true })
      return
    }
    if (authenticatedUser?.onboarding_status === 'completed' || authenticatedUser?.has_store) {
      navigate('/dashboard', { replace: true })
    } else {
      navigate('/setup', { replace: true })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const normalizedEmail = email.trim().toLowerCase()
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!normalizedEmail || !emailRegex.test(normalizedEmail)) {
      setError('Please enter a valid email address.')
      return
    }

    if (isRegister) {
      if (password.length < 8) {
        setError('Password must be at least 8 characters long.')
        return
      }
      if (!/\d/.test(password)) {
        setError('Password must contain at least one number.')
        return
      }
    }

    setLoading(true)
    trackAuthEvent(isRegister ? 'signup_started' : 'login_started')
    try {
      if (isRegister) {
        const authedUser = await signup(normalizedEmail, password)
        trackAuthEvent('signup_completed')
        navigatePostAuth(authedUser)
      } else {
        const authedUser = await login(normalizedEmail, password)
        trackAuthEvent('login_completed')
        navigatePostAuth(authedUser)
      }
    } catch (err) {
      setError(
        err.message ||
        'Authentication failed. Please check your details and try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  // Handle Real Google OAuth 2.0 Flow
  const handleGoogleOAuth = () => {
    trackAuthEvent('google_auth_started')
    // Redirects browser directly to backend OAuth authorize endpoint,
    // which generates cryptographic CSRF state and opens accounts.google.com
    window.location.href = '/api/v1/auth/google/authorize'
  }

  // Do not render login form if session already active or auth is loading
  const isLoggingOut = searchParams.get('logout') === 'true' || searchParams.get('switch') === 'true'
  if (!isLoggingOut && (authLoading || user)) {
    return (
      <div style={{
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        background: '#FAF9F6',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 4px 14px rgba(5, 150, 105, 0.25)',
          }}>
            <Activity style={{ width: 22, height: 22, color: '#fff' }} />
          </div>
          <p style={{ fontSize: 14, color: '#6b7280', fontWeight: 500 }}>
            {user ? 'Redirecting to your workspace...' : 'Loading TrendPulse...'}
          </p>
        </div>
      </div>
    )
  }

  const inputStyle = {
    width: '100%',
    padding: '13px 16px',
    borderRadius: 12,
    border: '1.5px solid #e5e5e5',
    fontSize: 14,
    color: '#1a1a1a',
    background: '#FAFAF9',
    outline: 'none',
    transition: 'all 0.15s ease',
    boxSizing: 'border-box',
  }

  const socialButtonStyle = {
    width: '100%',
    padding: '12px 20px',
    borderRadius: 100,
    border: '1.5px solid #e5e5e5',
    background: '#ffffff',
    color: '#111827',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    transition: 'all 0.15s ease',
    boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
  }

  const strength = getStrengthLabel()

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: '#FAF9F6',
      color: '#1a1a1a',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* ── Minimal Brand Top Bar ─────────────────────────────────── */}
      <header style={{
        padding: '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(0,0,0,0.05)',
        background: '#FAF9F6',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(5, 150, 105, 0.3)',
          }}>
            <Activity style={{ width: 18, height: 18, color: '#fff' }} />
          </div>
          <span style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.5px', color: '#0a0a0a' }}>
            TrendPulse
          </span>
          <span style={{
            fontSize: 10,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
            color: '#059669',
            background: '#ecfdf5',
            padding: '2px 7px',
            borderRadius: 20,
            border: '1px solid #a7f3d0',
          }}>
            Intel
          </span>
        </div>

        <div>
          <Link
            to="/"
            style={{
              fontSize: 13,
              color: '#888',
              textDecoration: 'none',
              fontWeight: 500,
              transition: 'color 0.15s',
            }}
            onMouseEnter={(e) => e.target.style.color = '#059669'}
            onMouseLeave={(e) => e.target.style.color = '#888'}
          >
            ← Back to Homepage
          </Link>
        </div>
      </header>

      {/* ── Auth Card ───────────────────────────────────────────── */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '36px 20px',
      }}>
        <div style={{ width: '100%', maxWidth: 440 }}>
          {/* Card */}
          <div style={{
            background: '#fff',
            borderRadius: 24,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '36px 32px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
          }}>
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 12px',
                borderRadius: 100,
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                fontSize: 11,
                fontWeight: 600,
                color: '#059669',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: 12,
              }}>
                Brand Intelligence
              </div>
              <h1 style={{
                fontSize: 24,
                fontWeight: 800,
                letterSpacing: '-0.5px',
                color: '#0a0a0a',
                margin: '0 0 6px',
              }}>
                {isRegister ? 'Join TrendPulse' : 'Welcome back'}
              </h1>
              <p style={{ fontSize: 14, color: '#6b7280', margin: 0, lineHeight: 1.4 }}>
                {isRegister
                  ? 'AI-driven market intelligence for clothing brands.'
                  : 'Log in to access your brand intelligence workspace.'}
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div style={{
                padding: '12px 14px',
                borderRadius: 12,
                background: '#FEF2F2',
                border: '1px solid #FECACA',
                fontSize: 13,
                color: '#DC2626',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                marginBottom: 18,
              }}>
                <AlertCircle style={{ width: 16, height: 16, flexShrink: 0, marginTop: 1 }} />
                <span>{error}</span>
              </div>
            )}

            {/* Tab Switcher */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 4,
              padding: 4,
              background: '#F5F5F4',
              borderRadius: 12,
              marginBottom: 20,
            }}>
              <button
                type="button"
                onClick={() => { setIsRegister(false); setError('') }}
                style={{
                  padding: '9px 16px',
                  borderRadius: 10,
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 600,
                  transition: 'all 0.2s',
                  background: !isRegister ? '#fff' : 'transparent',
                  color: !isRegister ? '#0a0a0a' : '#888',
                  boxShadow: !isRegister ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
                }}
              >
                Log In
              </button>
              <button
                type="button"
                onClick={() => { setIsRegister(true); setError('') }}
                style={{
                  padding: '9px 16px',
                  borderRadius: 10,
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 600,
                  transition: 'all 0.2s',
                  background: isRegister ? '#fff' : 'transparent',
                  color: isRegister ? '#0a0a0a' : '#888',
                  boxShadow: isRegister ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
                }}
              >
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#374151',
                  marginBottom: 5,
                }}>
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  autoComplete="username email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="founder@brand.com"
                  style={inputStyle}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#059669'
                    e.target.style.background = '#fff'
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#e5e5e5'
                    e.target.style.background = '#FAFAF9'
                  }}
                />
              </div>

              <div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 5,
                }}>
                  <label style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#374151',
                  }}>
                    Password *
                  </label>
                  {!isRegister && (
                    <Link
                      to="/forgot-password"
                      style={{
                        fontSize: 12,
                        color: '#059669',
                        textDecoration: 'none',
                        fontWeight: 600,
                      }}
                    >
                      Forgot password?
                    </Link>
                  )}
                </div>

                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    autoComplete={isRegister ? 'new-password' : 'current-password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={isRegister ? 'Create secure password (8+ chars)' : '••••••••'}
                    style={{
                      ...inputStyle,
                      paddingRight: 44,
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#059669'
                      e.target.style.background = '#fff'
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#e5e5e5'
                      e.target.style.background = '#FAFAF9'
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: 12,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: '#9ca3af',
                      cursor: 'pointer',
                      padding: 4,
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    {showPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                  </button>
                </div>

                {/* Password Strength Meter for Signup */}
                {isRegister && password && (
                  <div style={{
                    marginTop: 10,
                    padding: '10px 12px',
                    borderRadius: 10,
                    background: '#f9fafb',
                    border: '1px solid #f3f4f6',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontSize: 11, color: '#6b7280' }}>Password Strength:</span>
                      <span style={{ fontSize: 11, fontWeight: 600, color: strength.color }}>{strength.label}</span>
                    </div>
                    <div style={{
                      height: 4,
                      width: '100%',
                      background: '#f3f4f6',
                      borderRadius: 2,
                      overflow: 'hidden',
                      marginBottom: 8,
                    }}>
                      <div style={{
                        height: '100%',
                        width: strength.width,
                        background: strength.color,
                        transition: 'all 0.3s ease',
                      }} />
                    </div>

                    {/* Requirements Checklist */}
                    <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: 11,
                        color: hasMinLength ? '#059669' : '#6b7280',
                        fontWeight: hasMinLength ? 600 : 400,
                      }}>
                        {hasMinLength ? <Check style={{ width: 12, height: 12, color: '#059669' }} /> : <span style={{ width: 12, height: 12, display: 'inline-block', borderRadius: '50%', border: '1px solid #d1d5db' }} />}
                        <span>At least 8 characters</span>
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: 11,
                        color: hasNumber ? '#059669' : '#6b7280',
                        fontWeight: hasNumber ? 600 : 400,
                      }}>
                        {hasNumber ? <Check style={{ width: 12, height: 12, color: '#059669' }} /> : <span style={{ width: 12, height: 12, display: 'inline-block', borderRadius: '50%', border: '1px solid #d1d5db' }} />}
                        <span>At least one number (0-9)</span>
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: 11,
                        color: hasLetterOrSpecial ? '#059669' : '#6b7280',
                        fontWeight: hasLetterOrSpecial ? 600 : 400,
                      }}>
                        {hasLetterOrSpecial ? <Check style={{ width: 12, height: 12, color: '#059669' }} /> : <span style={{ width: 12, height: 12, display: 'inline-block', borderRadius: '50%', border: '1px solid #d1d5db' }} />}
                        <span>Mixed letters (uppercase & lowercase) or symbols</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Submit CTA */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '13px 20px',
                  borderRadius: 100,
                  border: 'none',
                  background: '#059669',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  transition: 'all 0.15s',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  marginTop: 6,
                }}
                onMouseEnter={(e) => { if (!loading) e.target.style.background = '#047857' }}
                onMouseLeave={(e) => { if (!loading) e.target.style.background = '#059669' }}
              >
                {loading ? (
                  <span>Processing...</span>
                ) : isRegister ? (
                  <>
                    <span>Continue with Email</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </>
                ) : (
                  <>
                    <span>Log In to Workspace</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </>
                )}
              </button>
            </form>

            {/* ── Linktree-Style OR Divider ──────────────────────── */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              margin: '22px 0',
            }}>
              <div style={{ flex: 1, height: 1, background: '#e5e7eb' }} />
              <span style={{
                padding: '0 12px',
                fontSize: 12,
                fontWeight: 600,
                color: '#6b7280',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                OR
              </span>
              <div style={{ flex: 1, height: 1, background: '#e5e7eb' }} />
            </div>

            {/* ── Linktree-Style Direct Social Auth Options ──────── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {/* Continue with Google (Real OAuth 2.0) */}
              <button
                type="button"
                onClick={handleGoogleOAuth}
                style={socialButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#d1d5db'
                  e.currentTarget.style.background = '#f9fafb'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e5e5e5'
                  e.currentTarget.style.background = '#ffffff'
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.26v3.15C3.27 21.36 7.35 24 12 24z"/>
                  <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.26C.46 8.16 0 9.94 0 12s.46 3.84 1.26 5.42l4.02-3.15z"/>
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.27 2.64 1.26 6.58l4.02 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                </svg>
                <span>Continue with Google</span>
              </button>
            </div>

            {/* Terms notice */}
            <p style={{
              fontSize: 11,
              color: '#6b7280',
              textAlign: 'center',
              marginTop: 18,
              lineHeight: 1.5,
            }}>
              By clicking Continue, you agree to TrendPulse's{' '}
              <a href="#" style={{ color: '#059669', textDecoration: 'underline' }}>Privacy Notice</a>,{' '}
              <a href="#" style={{ color: '#059669', textDecoration: 'underline' }}>Terms of Service</a>, and data protection policies.
            </p>

            {/* Switch mode footer */}
            <div style={{
              textAlign: 'center',
              marginTop: 16,
              fontSize: 13,
              color: '#4b5563',
            }}>
              {isRegister ? (
                <span>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setIsRegister(false); setError('') }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#059669',
                      fontWeight: 700,
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    Log in
                  </button>
                </span>
              ) : (
                <span>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setIsRegister(true); setError('') }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#059669',
                      fontWeight: 700,
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    Sign up
                  </button>
                </span>
              )}
            </div>
          </div>

          {/* Trust Badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            marginTop: 20,
            fontSize: 12,
            color: '#9ca3af',
          }}>
            <ShieldCheck style={{ width: 14, height: 14, color: '#059669' }} />
            <span>Market Velocity Intelligence • Predictive Demand Modeling • Enterprise Data Security</span>
          </div>
        </div>
      </div>
    </div>
  )
}
