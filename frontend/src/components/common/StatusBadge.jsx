import React, { useState, useEffect } from 'react'
import { checkBackendHealth } from '../../services/api'
import { Server, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react'

export default function StatusBadge() {
  const [status, setStatus] = useState('checking') // 'connected' | 'error' | 'checking'
  const [details, setDetails] = useState(null)

  const verifyConnection = async () => {
    setStatus('checking')
    const result = await checkBackendHealth()
    if (result.ok) {
      setStatus('connected')
      setDetails(result.data)
    } else {
      setStatus('error')
      setDetails({ error: result.error })
    }
  }

  useEffect(() => {
    verifyConnection()
    // Poll health periodically every 20 seconds
    const interval = setInterval(verifyConnection, 20000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div 
      className={`status-badge ${status}`}
      title={status === 'connected' ? `Connected to ${details?.app} (v${details?.version}) - DB: ${details?.database}` : `Backend unreachable: ${details?.error || 'Offline'}`}
      onClick={verifyConnection}
      style={{ cursor: 'pointer' }}
    >
      <span className={`status-indicator ${status === 'connected' ? 'pulse' : ''}`} />
      <span>
        {status === 'connected' && 'API Online'}
        {status === 'checking' && 'Connecting...'}
        {status === 'error' && 'API Offline'}
      </span>
    </div>
  )
}
