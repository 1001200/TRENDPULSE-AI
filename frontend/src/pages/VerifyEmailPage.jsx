import React, { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react'
import { authAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()
  const token = searchParams.get('token')

  const [loading, setLoading] = useState(Boolean(token))
  const [verified, setVerified] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return

    let isMounted = true
    authAPI.verifyEmail(token)
      .then(async () => {
        if (isMounted) {
          setVerified(true)
          await refreshUser?.()
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(
            err.response?.data?.detail ||
            'Email verification link is invalid or has expired.'
          )
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [token, refreshUser])

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: '#FAF9F6',
      color: '#1a1a1a',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
    }}>
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
        </div>
      </header>

      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '36px 20px',
      }}>
        <div style={{ width: '100%', maxWidth: 460 }}>
          <div style={{
            background: '#fff',
            borderRadius: 24,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '36px 32px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
            textAlign: 'center',
          }}>
            {loading ? (
              <div>
                <div style={{
                  width: 44,
                  height: 44,
                  border: '3px solid rgba(5, 150, 105, 0.15)',
                  borderTopColor: '#059669',
                  borderRadius: '50%',
                  margin: '0 auto 16px',
                  animation: 'spin 0.8s linear infinite',
                }} />
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: '#111827', margin: '0 0 6px' }}>
                  Verifying your email...
                </h2>
                <p style={{ fontSize: 14, color: '#6b7280', margin: 0 }}>
                  Please hold on while we validate your verification token.
                </p>
              </div>
            ) : verified ? (
              <div>
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
                  <CheckCircle2 style={{ width: 32, height: 32 }} />
                </div>
                <h1 style={{
                  fontSize: 22,
                  fontWeight: 800,
                  letterSpacing: '-0.5px',
                  color: '#0a0a0a',
                  margin: '0 0 10px',
                }}>
                  Email Verified Successfully!
                </h1>
                <p style={{ fontSize: 14, color: '#4b5563', lineHeight: 1.6, margin: '0 0 24px' }}>
                  Your account email has been verified. You now have full access to manage your store and drops.
                </p>
                <button
                  type="button"
                  onClick={() => navigate(user?.has_store ? '/dashboard' : '/setup')}
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
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                >
                  <span>{user?.has_store ? 'Go to Dashboard' : 'Continue Store Setup'}</span>
                  <ArrowRight style={{ width: 16, height: 16 }} />
                </button>
              </div>
            ) : error ? (
              <div>
                <div style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: '#FEF2F2',
                  border: '1px solid #FECACA',
                  color: '#DC2626',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 18px',
                }}>
                  <AlertCircle style={{ width: 32, height: 32 }} />
                </div>
                <h1 style={{
                  fontSize: 22,
                  fontWeight: 800,
                  letterSpacing: '-0.5px',
                  color: '#0a0a0a',
                  margin: '0 0 10px',
                }}>
                  Verification Link Invalid
                </h1>
                <p style={{ fontSize: 14, color: '#6b7280', lineHeight: 1.6, margin: '0 0 24px' }}>
                  {error}
                </p>
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
                  }}
                >
                  Return to Sign In
                </Link>
              </div>
            ) : (
              <div>
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
                  <ShieldCheck style={{ width: 32, height: 32 }} />
                </div>
                <h1 style={{
                  fontSize: 22,
                  fontWeight: 800,
                  letterSpacing: '-0.5px',
                  color: '#0a0a0a',
                  margin: '0 0 10px',
                }}>
                  Email Verification
                </h1>
                <p style={{ fontSize: 14, color: '#6b7280', lineHeight: 1.6, margin: '0 0 24px' }}>
                  No verification token was found in the link. Please open the link sent directly to your inbox.
                </p>
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
                  }}
                >
                  Return to Sign In
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
