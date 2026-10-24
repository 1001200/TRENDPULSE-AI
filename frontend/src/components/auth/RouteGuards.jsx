import React from 'react'
import { Navigate, useLocation, useSearchParams, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

function LoadingSpinner() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#FAF9F6',
      fontFamily: "'Inter', sans-serif",
      gap: 16,
    }}>
      <div style={{
        width: 38,
        height: 38,
        border: '3px solid rgba(5, 150, 105, 0.15)',
        borderTopColor: '#059669',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>
        Loading TrendPulse...
      </span>
    </div>
  )
}

/**
 * ProtectedRoute: Requires active authentication and completed onboarding.
 * - If not logged in -> redirects to /login?from=...
 * - If logged in but onboarding not completed -> redirects to /setup
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading, onboardingStatus, user, hasStore } = useAuth()
  const location = useLocation()

  if (loading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    const returnUrl = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?from=${returnUrl}`} replace />
  }

  const isComplete = onboardingStatus === 'completed' || hasStore || user?.has_store
  if (!isComplete) {
    return <Navigate to="/setup" replace />
  }

  return children ? children : <Outlet />
}

/**
 * OnboardingRoute: Guard for /setup
 * - If not logged in -> redirects to /login?from=/setup
 * - If logged in and onboarding already completed (and not in edit mode) -> redirects to /dashboard
 * - If edit=true is present in search params, allowed to edit profile
 */
export function OnboardingRoute({ children }) {
  const { isAuthenticated, loading, onboardingStatus, user, hasStore } = useAuth()
  const [searchParams] = useSearchParams()
  const isEditing = searchParams.get('edit') === 'true'

  if (loading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login?from=/setup" replace />
  }

  const isComplete = onboardingStatus === 'completed' || hasStore || user?.has_store
  if (isComplete && !isEditing) {
    return <Navigate to="/dashboard" replace />
  }

  return children ? children : <Outlet />
}

/**
 * PublicOnlyRoute: Renders public auth routes without aggressively hijacking
 * the user away to /setup if they intentionally opened /login or /signup.
 */
export function PublicOnlyRoute({ children }) {
  const { loading } = useAuth()

  if (loading) {
    return <LoadingSpinner />
  }

  return children ? children : <Outlet />
}
