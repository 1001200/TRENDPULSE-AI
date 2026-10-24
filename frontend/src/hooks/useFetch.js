import { useState, useEffect, useCallback } from 'react'

/**
 * Generic data-fetching hook with loading / error states.
 * Calls apiCall() on mount and when deps change.
 */
export function useFetch(apiCall, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiCall()
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}
