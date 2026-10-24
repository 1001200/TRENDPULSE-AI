import React, { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Lock, CheckCircle2, AlertCircle, Eye, EyeOff, Check } from 'lucide-react'
import { authAPI } from '../api/client'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  // Password strength checks
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!token) {
      setError('Missing or invalid reset token. Please request a new password reset link.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await authAPI.resetPassword(token, password)
      setSuccess(true)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Password reset failed. The link may be expired or already used.'
      )
    } finally {
      setLoading(false)
    }
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

      {/* Header */}
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
          <Link to="/landing" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
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
          </Link>
          <Link
            to="/login"
            style={{ fontSize: 13, fontWeight: 500, color: '#888', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}
            onMouseEnter={(e) => e.target.style.color = '#059669'}
            onMouseLeave={(e) => e.target.style.color = '#888'}
          >
            <ArrowLeft style={{ width: 14, height: 14 }} />
            Back to Sign In
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '36px 20px',
      }}>
        <div style={{ width: '100%', maxWidth: 440 }}>
          <div style={{
            background: '#fff',
            borderRadius: 24,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '36px 32px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
          }}>
            {success ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  color: '#059669',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 18px',
                }}>
                  <CheckCircle2 style={{ width: 30, height: 30 }} />
                </div>
                <h1 style={{
                  fontSize: 22,
                  fontWeight: 800,
                  letterSpacing: '-0.5px',
                  color: '#0a0a0a',
                  margin: '0 0 10px',
                }}>
                  Password reset successfully
                </h1>
                <p style={{ fontSize: 14, color: '#4b5563', lineHeight: 1.6, margin: '0 0 24px' }}>
                  Your password has been updated. All active sessions have been terminated for security. You can now log in with your new password.
                </p>
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  style={{
                    width: '100%',
                    padding: '13px 20px',
                    borderRadius: 100,
                    border: 'none',
                    background: '#059669',
                    color: '#fff',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                >
                  Log In Now
                </button>
              </div>
            ) : (
              <div>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: 14,
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    color: '#059669',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 14px',
                  }}>
                    <Lock style={{ width: 22, height: 22 }} />
                  </div>
                  <h1 style={{
                    fontSize: 22,
                    fontWeight: 800,
                    letterSpacing: '-0.5px',
                    color: '#0a0a0a',
                    margin: '0 0 8px',
                  }}>
                    Create new password
                  </h1>
                  <p style={{ fontSize: 14, color: '#6b7280', margin: 0, lineHeight: 1.5 }}>
                    Enter a new secure password for your TrendPulse account.
                  </p>
                </div>

                {!token && (
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
                    <span>No reset token detected in URL. Please click the exact link from your reset email.</span>
                  </div>
                )}

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

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: 12,
                      fontWeight: 600,
                      color: '#374151',
                      marginBottom: 5,
                    }}>
                      New Password *
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Choose a new strong password"
                        style={{ ...inputStyle, paddingRight: 44 }}
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
                          cursor: 'pointer',
                          color: '#9ca3af',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        {showPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                      </button>
                    </div>

                    {/* Password Strength Checklist */}
                    <div style={{
                      marginTop: 10,
                      padding: '10px 12px',
                      borderRadius: 10,
                      background: '#f9fafb',
                      border: '1px solid #f3f4f6',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontSize: 11, fontWeight: 600, color: '#4b5563' }}>
                          Password Strength: {strength.label || 'None'}
                        </span>
                      </div>
                      <div style={{
                        height: 4,
                        width: '100%',
                        background: '#e5e7eb',
                        borderRadius: 10,
                        overflow: 'hidden',
                        marginBottom: 8,
                      }}>
                        <div style={{
                          height: '100%',
                          width: strength.width,
                          background: strength.color,
                          transition: 'all 0.25s ease',
                        }} />
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
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
                          <span>Mixed letters or symbols</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: 12,
                      fontWeight: 600,
                      color: '#374151',
                      marginBottom: 5,
                    }}>
                      Confirm Password *
                    </label>
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-type new password"
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

                  <button
                    type="submit"
                    disabled={loading || !token}
                    style={{
                      width: '100%',
                      padding: '13px 20px',
                      borderRadius: 100,
                      border: 'none',
                      background: '#059669',
                      color: '#fff',
                      fontSize: 14,
                      fontWeight: 600,
                      cursor: (loading || !token) ? 'not-allowed' : 'pointer',
                      opacity: (loading || !token) ? 0.6 : 1,
                      marginTop: 6,
                      boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                    }}
                  >
                    {loading ? 'Saving new password...' : 'Update Password'}
                  </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: 22 }}>
                  <Link
                    to="/forgot-password"
                    style={{ fontSize: 13, color: '#6b7280', textDecoration: 'none' }}
                  >
                    Need a new reset link? <strong>Request Link</strong>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
