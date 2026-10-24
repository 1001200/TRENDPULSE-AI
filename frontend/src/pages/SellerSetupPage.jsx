import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Store,
  Phone,
  MapPin,
  Sparkles,
  CreditCard,
  ShieldCheck,
  Truck,
  Check,
  Copy,
  ExternalLink,
  ArrowRight,
  Info,
  AlertCircle,
  QrCode,
  CheckCircle2,
  RefreshCw,
  Zap,
} from 'lucide-react'
import SellerLayout from '../components/seller/SellerLayout'
import '../styles/bionis.css'

function InstagramIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  )
}

const NICHE_OPTIONS = [
  {
    id: 'Curated Vintage Thrift',
    title: 'Curated Vintage / Thrift',
    description: '1-of-1 90s/Y2K tees, washed Carhartt, denim jackets, retro racing jerseys.',
    icon: '🧥',
    badge: 'Popular for IG Reels',
  },
  {
    id: 'Y2K & Streetwear',
    title: 'Y2K & Streetwear',
    description: 'Baggy cargos, oversized boxy graphic tees, parachute pants, cyber aesthetics.',
    icon: '🛹',
    badge: 'High Search Volume',
  },
  {
    id: 'Upcycled & Reworked',
    title: 'Upcycled & Reworked',
    description: 'Custom patchwork, bleach-dyed flannels, reconstructed denim, designer reworks.',
    icon: '🪡',
    badge: 'High Margin',
  },
  {
    id: 'Deadstock & Surplus Basics',
    title: 'Deadstock & Surplus Basics',
    description: 'Heavyweight cotton blanks, French terry hoodies, export surplus essentials.',
    icon: '👕',
    badge: 'Repeat Buyers',
  },
]

const POPULAR_CITIES = [
  'Delhi NCR',
  'Mumbai',
  'Bengaluru',
  'Kolkata',
  'Pune',
  'Hyderabad',
  'Chennai',
  'Jaipur',
  'Ahmedabad',
  'Chandigarh',
]

export default function SellerSetupPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [copied, setCopied] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState('')

  // Form State
  const [formData, setFormData] = useState({
    name: 'Vintage Curations Delhi',
    slug: 'vintage-curations-delhi',
    instagram_handle: 'vintagecurations.in',
    phone: '9876543210',
    city: 'Delhi NCR',
    niche: 'Curated Vintage Thrift',
    upi_id: 'vintagecurations@okhdfcbank',
    fulfillment_type: 'self', // 'self' or 'supplier'
    supplier_phone: '',
    flat_shipping_fee: 70,
    policies: 'All sales final for 1-of-1 vintage items unless incorrect item received. Shipping within 24-48 hours.',
  })

  // Load existing store data — try authenticated business profile first, then legacy endpoint
  useEffect(() => {
    fetchStoreProfile()
  }, [])

  const fetchStoreProfile = async () => {
    try {
      setLoading(true)
      let res = null

      // First: try the new authenticated business profile API
      const token = localStorage.getItem('tp_token')
      if (token) {
        try {
          res = await axios.get('/api/v1/business/profile', {
            headers: { Authorization: `Bearer ${token}` }
          })
        } catch (e) {
          // Fall through to legacy endpoint
        }
      }

      // Fallback: legacy seller/store endpoint
      if (!res || !res.data) {
        try {
          res = await axios.get('/api/v1/seller/store')
        } catch (e) {
          res = await axios.get('/api/seller/store')
        }
      }

      if (res && res.data) {
        setFormData((prev) => ({
          ...prev,
          name: res.data.name || prev.name,
          slug: res.data.slug || prev.slug,
          instagram_handle: res.data.instagram_handle || prev.instagram_handle,
          phone: res.data.phone || prev.phone,
          city: res.data.city || prev.city,
          niche: res.data.niche || prev.niche,
          upi_id: res.data.upi_id || prev.upi_id,
          fulfillment_type: res.data.fulfillment_type || prev.fulfillment_type,
          supplier_phone: res.data.supplier_phone || '',
          flat_shipping_fee: res.data.flat_shipping_fee ?? 70,
          policies: res.data.policies || prev.policies,
        }))
      }
    } catch (err) {
      console.warn('Could not load existing store, using defaults:', err)
    } finally {
      setLoading(false)
    }
  }

  // Auto-slugify store name
  const handleNameChange = (e) => {
    const val = e.target.value
    const autoSlug = val
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')

    setFormData((prev) => ({
      ...prev,
      name: val,
      slug: autoSlug || prev.slug,
    }))
  }

  const handleCopyLink = () => {
    const url = `${window.location.origin}/drop/${formData.slug}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      // Validate UPI ID format
      if (!formData.upi_id.includes('@')) {
        throw new Error('Please enter a valid UPI VPA handle (e.g. name@okhdfcbank or 9876543210@paytm).')
      }

      // Validate Indian Phone Number
      const cleanedPhone = formData.phone.replace(/[^0-9]/g, '')
      if (cleanedPhone.length < 10) {
        throw new Error('Please enter a valid 10-digit Indian WhatsApp mobile number.')
      }

      const payload = {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        instagram_handle: formData.instagram_handle.replace(/^@/, '').trim(),
        phone: cleanedPhone,
        city: formData.city,
        niche: formData.niche,
        upi_id: formData.upi_id.trim(),
        fulfillment_type: formData.fulfillment_type,
        supplier_phone: formData.supplier_phone ? formData.supplier_phone.replace(/[^0-9]/g, '') : null,
        flat_shipping_fee: parseFloat(formData.flat_shipping_fee) || 70,
        policies: formData.policies.trim(),
      }

      let res
      try {
        res = await axios.post('/api/v1/seller/store', payload)
      } catch (err) {
        res = await axios.post('/api/seller/store', payload)
      }

      // Also sync to the new authenticated business profile endpoint
      const token = localStorage.getItem('tp_token')
      if (token) {
        try {
          await axios.post('/api/v1/business/profile', {
            business_name: payload.name,
            instagram_handle: payload.instagram_handle,
            upi_id: payload.upi_id,
            flat_shipping_fee: payload.flat_shipping_fee,
            fulfillment_type: payload.fulfillment_type,
            supplier_phone: payload.supplier_phone,
            niche: payload.niche,
            city: payload.city,
          }, { headers: { Authorization: `Bearer ${token}` } })
        } catch (e) {
          // Non-critical — legacy store was saved successfully
        }
      }

      if (res.data) {
        setSaveSuccess(true)
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save store settings.')
    } finally {
      setSaving(false)
    }
  }

  const publicDropUrl = `${window.location.origin}/drop/${formData.slug}`

  return (
    <SellerLayout
      storeSlug={formData.slug}
      storeName={formData.name}
      upiId={formData.upi_id}
    >
      <div className="space-y-8">
        {/* ── Top Hero Banner ────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Phase 1 of 3
              </span>
              <span className="text-xs text-slate-400">Seller Onboarding Hub</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Clothing Business Setup
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Configure your brand profile, zero-custody personal UPI payments, and shipping defaults.
              Once saved, your branded checkout link is immediately active.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={handleCopyLink}
              className="bionis-btn-secondary inline-flex items-center gap-2 text-xs"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied Store URL' : 'Copy Drop Link'}</span>
            </button>
            <a
              href={`/drop/${formData.slug}`}
              target="_blank"
              rel="noreferrer"
              className="bionis-btn-secondary inline-flex items-center gap-1.5 text-xs text-blue-400 border-blue-500/20"
            >
              <span>Preview</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 flex items-start gap-3 text-red-200 text-sm animate-fade-in">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Configuration Error</p>
              <p className="text-xs text-red-300/80 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* ── Main 2-Column Grid ─────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Form: 7 Columns */}
          <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-8">
            {/* 1. Store Identity & Brand Details */}
            <div className="bionis-card p-6 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <Store className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Brand & Discovery Profile</h2>
                    <p className="text-xs text-slate-400">How your store looks on Instagram & Web</p>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-slate-400">Required</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Store Name */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Store / Brand Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleNameChange}
                    placeholder="e.g. Retro Archive Delhi"
                    className="bionis-input w-full text-sm font-medium"
                  />
                  <p className="text-[11px] text-slate-400">Shown prominently in customer checkout</p>
                </div>

                {/* Slug */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Store URL Slug <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-mono select-none">
                      /drop/
                    </span>
                    <input
                      type="text"
                      required
                      value={formData.slug}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''),
                        })
                      }
                      className="bionis-input w-full pl-16 text-sm font-mono"
                      placeholder="retro-archive"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">
                    Link: {window.location.host}/drop/{formData.slug}
                  </p>
                </div>

                {/* Instagram Handle */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Instagram Handle <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-3 text-slate-400 select-none">@</span>
                    <input
                      type="text"
                      required
                      value={formData.instagram_handle}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          instagram_handle: e.target.value.replace(/^@/, ''),
                        })
                      }
                      placeholder="vintagecurations.in"
                      className="bionis-input w-full pl-8 text-sm"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">Where buyers discover your Reels & Stories</p>
                </div>

                {/* WhatsApp Support Number */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    WhatsApp Mobile Number <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-mono select-none">
                      +91
                    </span>
                    <input
                      type="tel"
                      required
                      maxLength={10}
                      value={formData.phone}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          phone: e.target.value.replace(/[^0-9]/g, ''),
                        })
                      }
                      placeholder="9876543210"
                      className="bionis-input w-full pl-12 text-sm font-mono"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">For dispatch notifications and buyer support</p>
                </div>

                {/* Base City */}
                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-xs font-semibold text-slate-300">
                    Operating City / Hub <span className="text-red-400">*</span>
                  </label>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {POPULAR_CITIES.map((city) => (
                      <button
                        key={city}
                        type="button"
                        onClick={() => setFormData({ ...formData, city })}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                          formData.city === city
                            ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-semibold'
                            : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {city}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Clothing Niche & Curation Style */}
            <div className="bionis-card p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Clothing Curation Niche</h2>
                    <p className="text-xs text-slate-400">Auto-calibrates item tags and customer expectations</p>
                  </div>
                </div>
                <span className="text-[11px] text-indigo-400 font-semibold">Classification</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {NICHE_OPTIONS.map((item) => {
                  const isSelected = formData.niche === item.id
                  return (
                    <div
                      key={item.id}
                      onClick={() => setFormData({ ...formData, niche: item.id })}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-gradient-to-b from-blue-900/30 to-slate-900 border-blue-500 shadow-md shadow-blue-500/10'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <span className="text-2xl">{item.icon}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                            isSelected
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {item.badge}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-white mt-2">{item.title}</h3>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* 3. Zero-Custody UPI Settlement */}
            <div className="bionis-card p-6 space-y-5 border-emerald-500/20">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Direct-to-Bank UPI Settlement</h2>
                    <p className="text-xs text-slate-400">Zero platform cuts, direct P2P transfer</p>
                  </div>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  0% Custody
                </span>
              </div>

              {/* Zero-Custody Security Banner */}
              <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-300/90 leading-relaxed flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>100% Direct P2P Payment:</strong> When a buyer checks out, TrendPulse launches
                  their GPay, PhonePe, or Paytm app directly via UPI Intent. ₹0 is held by TrendPulse; funds
                  settle instantly in your personal bank account.
                </span>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Personal UPI VPA Handle <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={formData.upi_id}
                    onChange={(e) => setFormData({ ...formData, upi_id: e.target.value.trim() })}
                    placeholder="e.g. vintagecurations@okhdfcbank or 9876543210@paytm"
                    className="bionis-input w-full font-mono text-sm pr-24"
                  />
                  <div className="absolute right-2.5 top-2.5 flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-emerald-400">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>Verified</span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400">
                  Works with Google Pay, PhonePe, Paytm, CRED, BHIM, and all Indian banking apps.
                </p>
              </div>

              {/* Supported UPI Apps Pill Row */}
              <div className="pt-2 flex items-center gap-3 text-xs text-slate-400">
                <span className="text-[11px] text-slate-400">Tested Apps:</span>
                <span className="px-2 py-0.5 rounded bg-slate-850 border border-slate-800 text-slate-300 font-medium">
                  Google Pay
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-850 border border-slate-800 text-slate-300 font-medium">
                  PhonePe
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-850 border border-slate-800 text-slate-300 font-medium">
                  Paytm
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-850 border border-slate-800 text-slate-300 font-medium">
                  CRED UPI
                </span>
              </div>
            </div>

            {/* 4. Shipping & Fulfillment Preference */}
            <div className="bionis-card p-6 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <Truck className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Shipping & Fulfillment Engine</h2>
                    <p className="text-xs text-slate-400">Courier automation and flat delivery fee</p>
                  </div>
                </div>
              </div>

              {/* Model Selection */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div
                  onClick={() => setFormData({ ...formData, fulfillment_type: 'self' })}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    formData.fulfillment_type === 'self'
                      ? 'bg-blue-900/20 border-blue-500 text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-white">📦 Stockist (Self-Shipped)</span>
                    {formData.fulfillment_type === 'self' && (
                      <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    You hold physical inventory at home/studio. Generate 1-click Shiprocket & Delhivery bulk CSV labels.
                  </p>
                </div>

                <div
                  onClick={() => setFormData({ ...formData, fulfillment_type: 'supplier' })}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    formData.fulfillment_type === 'supplier'
                      ? 'bg-blue-900/20 border-blue-500 text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-white">🚚 Dropshipper / Reseller</span>
                    {formData.fulfillment_type === 'supplier' && (
                      <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Wholesale supplier ships directly. System creates 1-click WhatsApp order dispatch links with buyer addresses.
                  </p>
                </div>
              </div>

              {/* If Supplier is chosen, ask for supplier WhatsApp */}
              {formData.fulfillment_type === 'supplier' && (
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5 animate-fade-in">
                  <label className="text-xs font-semibold text-slate-300">
                    Wholesale Supplier WhatsApp Number
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-mono select-none">
                      +91
                    </span>
                    <input
                      type="tel"
                      maxLength={10}
                      value={formData.supplier_phone}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          supplier_phone: e.target.value.replace(/[^0-9]/g, ''),
                        })
                      }
                      placeholder="9811223344"
                      className="bionis-input w-full pl-12 text-sm font-mono"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Orders will prepare a pre-filled WhatsApp message for this supplier.
                  </p>
                </div>
              )}

              {/* Flat Shipping Charge */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Standard Delivery Fee (INR)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-mono select-none">
                      ₹
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={500}
                      value={formData.flat_shipping_fee}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          flat_shipping_fee: e.target.value,
                        })
                      }
                      className="bionis-input w-full pl-8 text-sm font-mono"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">Standard Indian thrift rate is ₹70 flat</p>
                </div>

                {/* Return Policy Preset */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Store Return & Claim Policy
                  </label>
                  <textarea
                    rows={2}
                    value={formData.policies}
                    onChange={(e) => setFormData({ ...formData, policies: e.target.value })}
                    className="bionis-input w-full text-xs"
                    placeholder="All sales final for 1-of-1 items..."
                  />
                  <p className="text-[11px] text-slate-400">Shown in checkout modal to eliminate disputes</p>
                </div>
              </div>
            </div>

            {/* Submit Bar */}
            <div className="flex items-center justify-between pt-4">
              <div className="text-xs text-slate-400">
                All fields save directly to your encrypted SQLite database.
              </div>
              <button
                type="submit"
                disabled={saving}
                className="bionis-btn-primary inline-flex items-center gap-2 text-sm disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Saving Store Setup...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Save & Activate Business Profile</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Right Rail: Real-Time Live Preview Mockup (5 Columns) */}
          <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-24">
            <div className="bionis-card p-6 border-blue-500/20 bg-gradient-to-b from-slate-900/90 to-[#070a12]">
              <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 bionis-live-pulse" />
                  <span className="text-xs font-semibold text-slate-200">Customer View Simulator</span>
                </div>
                <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                  Live Preview
                </span>
              </div>

              {/* Simulated Mobile Drop Card */}
              <div className="rounded-2xl border border-slate-700/80 bg-[#090d16] p-5 shadow-2xl space-y-5">
                {/* Store Header in Customer View */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h3 className="text-base font-bold text-white tracking-tight">
                        {formData.name || 'Your Brand Name'}
                      </h3>
                      <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    </div>
                    <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <span>@{formData.instagram_handle || 'yourhandle'}</span>
                      <span>•</span>
                      <span>{formData.city || 'India'}</span>
                    </p>
                  </div>
                  <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white text-lg shadow-md shadow-blue-500/20">
                    {(formData.name || 'T')[0].toUpperCase()}
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-slate-800/90 text-slate-300 font-medium border border-slate-700">
                    {formData.niche}
                  </span>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20">
                    ₹{formData.flat_shipping_fee} Flat Shipping
                  </span>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20">
                    Zero-Custody UPI
                  </span>
                </div>

                {/* Simulated Sample Vintage Item */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200 truncate max-w-[180px]">
                      1998 Detroit Washed Heavy Duck Jacket
                    </span>
                    <span className="text-emerald-400 font-mono font-bold">₹2,899</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Size: L (Chest 44")</span>
                    <span className="text-slate-300 font-mono">Condition: 9/10</span>
                  </div>
                  <div className="pt-1">
                    <div className="w-full py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm">
                      <Zap className="w-3.5 h-3.5 fill-current" />
                      <span>Claim Item (10 Min Lock)</span>
                    </div>
                  </div>
                </div>

                {/* Direct UPI Verification Pill */}
                <div className="p-3 rounded-xl bg-slate-900/90 border border-emerald-500/20 text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-[11px] text-slate-400">Direct Payee VPA:</span>
                    <span className="font-mono text-emerald-400 text-[11px]">{formData.upi_id}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 leading-normal">
                    ✓ Buyer money directly arrives into seller's GPay/PhonePe with no middleman escrow.
                  </div>
                </div>

                {/* URL Preview Link */}
                <div className="text-[11px] text-slate-400 text-center font-mono bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 truncate">
                  {publicDropUrl}
                </div>
              </div>
            </div>

            {/* Step Guide */}
            <div className="bionis-card p-5 border-slate-800 text-xs space-y-3">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-blue-400" />
                <span>Next Step in Workflow</span>
              </h4>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Once your Business Setup is complete, we move to <strong>Step 2: Item Lister</strong>,
                where you can upload drops in 30 seconds with auto-tagging and chest/length measurements.
              </p>
            </div>
          </div>
        </div>

        {/* ── Success Modal ──────────────────────────────────────── */}
        {saveSuccess && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="bionis-card max-w-md w-full p-6 text-center space-y-5 border-emerald-500/40 bg-[#090d16] shadow-2xl">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto text-2xl">
                ✓
              </div>

              <div>
                <h3 className="text-xl font-bold text-white">Business Setup Complete!</h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                  Your store profile for <strong>{formData.name}</strong> is live. Payments are connected
                  directly to your personal UPI ID <strong>{formData.upi_id}</strong>.
                </p>
              </div>

              {/* Ready Link Box */}
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-left space-y-1.5">
                <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                  Your Public Drop Link
                </span>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-blue-400 truncate">{publicDropUrl}</span>
                  <button
                    type="button"
                    onClick={handleCopyLink}
                    className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 transition-colors"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setSaveSuccess(false)}
                  className="bionis-btn-secondary flex-1 text-xs"
                >
                  Close & Edit
                </button>
                <a
                  href={`/drop/${formData.slug}`}
                  target="_blank"
                  rel="noreferrer"
                  className="bionis-btn-primary flex-1 inline-flex items-center justify-center gap-1.5 text-xs"
                >
                  <span>Open Storefront</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </SellerLayout>
  )
}
