import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Mail, CheckCircle2, AlertCircle, Send } from 'lucide-react'
import { authAPI } from '../api/client'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) return

    setLoading(true)
    setError('')
    try {
      await authAPI.forgotPassword(email.trim())
      setSubmitted(true)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to process password reset request. Please try again later.'
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
            {submitted ? (
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
                  Check your inbox
                </h1>
                <p style={{ fontSize: 14, color: '#4b5563', lineHeight: 1.6, margin: '0 0 24px' }}>
                  If an account exists for <strong>{email}</strong>, we have sent instructions to reset your password.
                </p>
                <div style={{
                  padding: '12px 14px',
                  background: '#f9fafb',
                  borderRadius: 12,
                  border: '1px solid #f3f4f6',
                  fontSize: 12,
                  color: '#6b7280',
                  marginBottom: 24,
                  textAlign: 'left',
                  lineHeight: 1.5,
                }}>
                  Note: The reset link expires in 1 hour. Be sure to check your spam or promotions folder if it doesn't appear within a few minutes.
                </div>
                <Link
                  to="/login"
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '12px 20px',
                    borderRadius: 100,
                    background: '#059669',
                    color: '#fff',
                    fontSize: 14,
                    fontWeight: 600,
                    textDecoration: 'none',
                    boxSizing: 'border-box',
                    textAlign: 'center',
                  }}
                >
                  Return to Sign In
                </Link>
                <button
                  type="button"
                  onClick={() => { setSubmitted(false); setEmail(''); setError('') }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#6b7280',
                    fontSize: 13,
                    marginTop: 16,
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Try another email
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
                    <Mail style={{ width: 22, height: 22 }} />
                  </div>
                  <h1 style={{
                    fontSize: 22,
                    fontWeight: 800,
                    letterSpacing: '-0.5px',
                    color: '#0a0a0a',
                    margin: '0 0 8px',
                  }}>
                    Reset your password
                  </h1>
                  <p style={{ fontSize: 14, color: '#6b7280', margin: 0, lineHeight: 1.5 }}>
                    Enter the email address registered with your TrendPulse store.
                  </p>
                </div>

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

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: 12,
                      fontWeight: 600,
                      color: '#374151',
                      marginBottom: 5,
                    }}>
                      Account Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="seller@store.com"
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
                      opacity: loading ? 0.7 : 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 8,
                      boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                    }}
                  >
                    {loading ? 'Sending link...' : (
                      <>
                        <span>Send Reset Link</span>
                        <Send style={{ width: 15, height: 15 }} />
                      </>
                    )}
                  </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: 22 }}>
                  <Link
                    to="/login"
                    style={{ fontSize: 13, color: '#6b7280', textDecoration: 'none', fontWeight: 500 }}
                    onMouseEnter={(e) => e.target.style.color = '#059669'}
                    onMouseLeave={(e) => e.target.style.color = '#6b7280'}
                  >
                    Remember your password? <strong>Sign In</strong>
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
