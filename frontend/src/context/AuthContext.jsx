import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const cached = localStorage.getItem('tp_user')
      return cached ? JSON.parse(cached) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(() => !localStorage.getItem('tp_user'))
  const [authError, setAuthError] = useState(null)

  // Fetch current session profile from backend
  const fetchCurrentUser = useCallback(async () => {
    try {
      const res = await authAPI.me()
      if (res.data?.access_token) {
        localStorage.setItem('tp_token', res.data.access_token)
      }
      try {
        localStorage.setItem('tp_user', JSON.stringify(res.data))
      } catch {}
      setUser(res.data)
      setAuthError(null)
      return res.data
    } catch (err) {
      setUser(null)
      localStorage.removeItem('tp_token')
      localStorage.removeItem('tp_user')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial session boot
  useEffect(() => {
    fetchCurrentUser()
  }, [fetchCurrentUser])

  // Multi-tab synchronization and 401 handling
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'tp_auth_sync') {
        // Another tab logged in or logged out
        fetchCurrentUser()
      }
    }

    const handleUnauthorized = () => {
      setUser(null)
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('tp_auth_unauthorized', handleUnauthorized)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('tp_auth_unauthorized', handleUnauthorized)
    }
  }, [fetchCurrentUser])

  const notifyOtherTabs = () => {
    try {
      localStorage.setItem('tp_auth_sync', Date.now().toString())
    } catch {}
  }

  // Register with email and password only
  const signup = async (email, password) => {
    setAuthError(null)
    try {
      const res = await authAPI.register(email.trim(), password)
      if (res.data?.access_token) {
        localStorage.setItem('tp_token', res.data.access_token)
      }
      const userData = await fetchCurrentUser()
      notifyOtherTabs()
      return userData
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Registration failed. Please try again.'
      setAuthError(msg)
      throw new Error(msg)
    }
  }

  // Authenticate with email and password
  const login = async (email, password) => {
    setAuthError(null)
    try {
      const res = await authAPI.login(email.trim(), password)
      if (res.data?.access_token) {
        localStorage.setItem('tp_token', res.data.access_token)
      }
      const userData = await fetchCurrentUser()
      notifyOtherTabs()
      return userData
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.'
      setAuthError(msg)
      throw new Error(msg)
    }
  }

  // Authenticate with Google ID Token
  const googleAuth = async (credential) => {
    setAuthError(null)
    try {
      const res = await authAPI.googleLogin(credential)
      if (res.data?.access_token) {
        localStorage.setItem('tp_token', res.data.access_token)
      }
      const userData = await fetchCurrentUser()
      notifyOtherTabs()
      return userData
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Google sign-in failed. Please try again.'
      setAuthError(msg)
      throw new Error(msg)
    }
  }

  // Redirect to real Google OAuth 2.0 authorization endpoint
  const startGoogleOAuth = () => {
    window.location.href = authAPI.googleAuthorizeUrl
  }

  // End session
  const logout = async () => {
    try {
      await authAPI.logout()
    } catch {}
    localStorage.removeItem('tp_token')
    localStorage.removeItem('tp_user')
    setUser(null)
    setAuthError(null)
    notifyOtherTabs()
  }

  const value = {
    user,
    isAuthenticated: Boolean(user),
    onboardingStatus: user?.onboarding_status || (user?.has_store ? 'completed' : 'not_started'),
    onboardingStep: user?.onboarding_step || 1,
    hasStore: Boolean(user?.has_store),
    loading,
    authError,
    setAuthError,
    signup,
    login,
    googleAuth,
    startGoogleOAuth,
    logout,
    refreshUser: fetchCurrentUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
