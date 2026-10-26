import React, { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Trash2, AlertTriangle, CheckCircle2, ShieldCheck, Save } from 'lucide-react'
import { resetData, getBusinessProfile, updateBusinessProfile } from '../services/api'

export default function SettingsPage() {
  const [resetting, setResetting] = useState(false)
  const [resetDone, setResetDone] = useState(false)
  const [confirmReset, setConfirmReset] = useState(false)

  // Store Profile State
  const [businessName, setBusinessName] = useState('Studio Atelier')
  const [instagramHandle, setInstagramHandle] = useState('@studio.atelier')
  const [currency, setCurrency] = useState('₹ INR (Indian Rupee)')
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileSaved, setProfileSaved] = useState(false)

  useEffect(() => {
    const fetchProfile = async () => {
      const res = await getBusinessProfile()
      if (res.ok && res.data) {
        setBusinessName(res.data.business_name || 'My Business')
        setInstagramHandle(res.data.instagram_handle || '@store')
        if (res.data.currency) setCurrency(res.data.currency)
      }
    }
    fetchProfile()
  }, [])

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSavingProfile(true)
    const res = await updateBusinessProfile({
      business_name: businessName,
      instagram_handle: instagramHandle
    })
    setSavingProfile(false)
    if (res.ok) {
      setProfileSaved(true)
      window.dispatchEvent(new CustomEvent('trendpulse_profile_updated', {
        detail: {
          business_name: res.data.business_name,
          instagram_handle: res.data.instagram_handle
        }
      }))
      setTimeout(() => setProfileSaved(false), 3000)
    }
  }

  const handleReset = async () => {
    setResetting(true)
    const res = await resetData()
    setResetting(false)
    if (res.ok) {
      setResetDone(true)
      setConfirmReset(false)
      setTimeout(() => setResetDone(false), 3000)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Store Profile */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--mint-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--forest-green)' }}>
              <SettingsIcon size={18} />
            </div>
            <div>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', display: 'block' }}>Store Profile</span>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Configure your business details and handle</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {profileSaved && (
              <span className="pill-badge green">
                <CheckCircle2 size={13} />
                <span>Saved</span>
              </span>
            )}
            <button
              className="btn btn-primary btn-sm"
              onClick={handleSaveProfile}
              disabled={savingProfile}
            >
              <Save size={14} />
              <span>{savingProfile ? 'Saving...' : 'Save Profile'}</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleSaveProfile} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Store / Business Name</label>
            <input
              type="text"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="e.g. Studio Atelier"
              style={{
                width: '100%',
                padding: '0.6rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                background: '#F9FAF8',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Instagram Handle</label>
            <input
              type="text"
              value={instagramHandle}
              onChange={(e) => setInstagramHandle(e.target.value)}
              placeholder="e.g. @studio.atelier"
              style={{
                width: '100%',
                padding: '0.6rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                background: '#F9FAF8',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Default Currency</label>
            <input
              type="text"
              value={currency}
              disabled
              style={{
                width: '100%',
                padding: '0.6rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                background: '#F1F3EF',
                fontSize: '0.85rem',
                color: 'var(--text-muted)',
                outline: 'none'
              }}
            />
          </div>
        </form>
      </div>

      {/* Data Management */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', display: 'block' }}>Reset Business Data</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Permanently clear all uploaded sales, inventory records, and caches.</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {resetDone && (
              <span className="pill-badge green">
                <CheckCircle2 size={13} />
                <span>Cleared Successfully</span>
              </span>
            )}
            {!confirmReset ? (
              <button className="btn btn-danger btn-sm" onClick={() => setConfirmReset(true)}>
                <Trash2 size={14} />
                <span>Reset All Data</span>
              </button>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--badge-red-text)', fontWeight: 600 }}>
                  <AlertTriangle size={13} style={{ verticalAlign: 'middle', marginRight: '3px' }} /> Confirm?
                </span>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={handleReset}
                  disabled={resetting}
                >
                  {resetting ? 'Deleting...' : 'Yes, Delete'}
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setConfirmReset(false)}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Pro Membership Card */}
      <div className="sage-gradient-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <ShieldCheck size={18} color="var(--forest-dark)" />
          <span style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--forest-dark)' }}>TrendPulse Pro Workspace</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
          Designed specifically for independent fashion and clothing thrift businesses.
          Turn spreadsheets and drop receipts into clear revenue drivers and customer patterns.
        </p>
      </div>
    </div>
  )
}
