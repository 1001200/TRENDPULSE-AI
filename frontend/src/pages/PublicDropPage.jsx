import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Sparkles, CheckCircle2, AlertCircle, ArrowRight,
  ShieldCheck, X, ExternalLink, QrCode, Lock,
  Copy, Check, ShoppingBag, Clock, Truck,
  Phone, MapPin, User, Share2, Search, Banknote
} from 'lucide-react'
import { dropPublicAPI } from '../api/client'

function InstagramIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
      <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
    </svg>
  )
}

// Indian Pincode to City/State basic prefix map for instant autofill
const PINCODE_MAP = {
  '11': { city: 'New Delhi', state: 'Delhi' },
  '12': { city: 'Gurugram / Faridabad', state: 'Haryana' },
  '14': { city: 'Ludhiana / Amritsar', state: 'Punjab' },
  '16': { city: 'Chandigarh', state: 'Punjab' },
  '20': { city: 'Noida / Ghaziabad', state: 'Uttar Pradesh' },
  '22': { city: 'Lucknow', state: 'Uttar Pradesh' },
  '30': { city: 'Jaipur', state: 'Rajasthan' },
  '38': { city: 'Ahmedabad', state: 'Gujarat' },
  '39': { city: 'Surat', state: 'Gujarat' },
  '40': { city: 'Mumbai', state: 'Maharashtra' },
  '41': { city: 'Pune', state: 'Maharashtra' },
  '50': { city: 'Hyderabad', state: 'Telangana' },
  '56': { city: 'Bengaluru', state: 'Karnataka' },
  '60': { city: 'Chennai', state: 'Tamil Nadu' },
  '68': { city: 'Kochi', state: 'Kerala' },
  '70': { city: 'Kolkata', state: 'West Bengal' },
}

function resolvePincode(pin) {
  if (!pin || pin.length < 2) return null
  const prefix = pin.substring(0, 2)
  return PINCODE_MAP[prefix] || null
}

export default function PublicDropPage() {
  const { slug } = useParams()
  const [drop, setDrop] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Active Checkout Modal state
  const [activeItem, setActiveItem] = useState(null)
  const [checkoutStep, setCheckoutStep] = useState('details') // 'details' | 'payment' | 'success'
  const [paymentMethod, setPaymentMethod] = useState('upi') // 'upi' | 'cod'

  // Form State
  const [buyerPhone, setBuyerPhone] = useState('')
  const [buyerName, setBuyerName] = useState('')
  const [buyerIg, setBuyerIg] = useState('')
  const [addressLine, setAddressLine] = useState('')
  const [pincode, setPincode] = useState('')
  const [city, setCity] = useState('')
  const [stateName, setStateName] = useState('')
  const [utrReference, setUtrReference] = useState('')
  const [isCheckingOut, setIsCheckingOut] = useState(false)
  const [orderConfirmed, setOrderConfirmed] = useState(null)

  // UI state
  const [copiedUpi, setCopiedUpi] = useState(false)
  const [copiedLink, setCopiedLink] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSize, setSelectedSize] = useState('ALL')

  useEffect(() => {
    loadDrop()
    const interval = setInterval(loadDrop, 15000) // Poll every 15s for live inventory updates
    return () => clearInterval(interval)
  }, [slug])

  const loadDrop = async () => {
    try {
      const res = await dropPublicAPI.getDrop(slug || 'vintage-curations')
      setDrop(res.data)
      setError(null)
    } catch (err) {
      console.error(err)
      setError('Drop not found or currently inactive.')
    } finally {
      setLoading(false)
    }
  }

  // Handle Pincode Auto-Fill
  const handlePincodeChange = (val) => {
    const clean = val.replace(/\D/g, '').slice(0, 6)
    setPincode(clean)
    if (clean.length >= 2) {
      const match = resolvePincode(clean)
      if (match) {
        if (!city) setCity(match.city)
        if (!stateName) setStateName(match.state)
      }
    }
  }

  // Step 1: Open Buy Modal
  const handleStartBuy = (item) => {
    setActiveItem(item)
    setCheckoutStep('details')
    setPaymentMethod('upi')
    setUtrReference('')
  }

  // Handle Form Submission from Details screen (UPI proceeds to QR; COD orders directly)
  const handleProceedFromDetails = async (e) => {
    e.preventDefault()
    if (!buyerPhone || buyerPhone.length < 10) {
      alert('Please enter a valid 10-digit WhatsApp phone number.')
      return
    }
    if (!buyerName || !addressLine || pincode.length !== 6 || !city || !stateName) {
      alert('Please complete all shipping address fields.')
      return
    }

    if (paymentMethod === 'cod') {
      setIsCheckingOut(true)
      try {
        const orderRes = await dropPublicAPI.checkout(activeItem.id, {
          buyer_name: buyerName,
          buyer_ig: buyerIg || 'instagram_user',
          buyer_phone: buyerPhone,
          address_line: addressLine,
          pincode: pincode,
          city: city,
          state: stateName,
          utr_reference: 'COD',
        })
        setOrderConfirmed(orderRes.data)
        setCheckoutStep('success')
        loadDrop()
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to place Cash on Delivery order.')
      } finally {
        setIsCheckingOut(false)
      }
      return
    }

    // Direct UPI Selected -> Move to Step 2
    setCheckoutStep('payment')

    // Automatically trigger UPI intent on mobile devices if direct link available
    const upiDetails = getUpiDetails(activeItem)
    if (upiDetails && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
      window.location.href = upiDetails.uri
    }
  }

  // Submit 12-Digit UTR to Confirm UPI Purchase
  const handleSubmitUTR = async (e) => {
    e.preventDefault()
    if (!utrReference || utrReference.length < 6) {
      alert('Please enter your 12-digit UPI Reference Number (UTR) from your payment receipt.')
      return
    }

    setIsCheckingOut(true)
    try {
      const orderRes = await dropPublicAPI.checkout(activeItem.id, {
        buyer_name: buyerName,
        buyer_ig: buyerIg || 'instagram_user',
        buyer_phone: buyerPhone,
        address_line: addressLine,
        pincode: pincode,
        city: city,
        state: stateName,
        utr_reference: utrReference,
      })
      setOrderConfirmed(orderRes.data)
      setCheckoutStep('success')
      loadDrop()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit order.')
    } finally {
      setIsCheckingOut(false)
    }
  }

  // Generate UPI Intent URI with pre-filled exact price
  const getUpiDetails = (item) => {
    if (!item || !drop) return null
    const shipping = drop.flat_shipping_fee || 70
    const totalAmount = parseFloat(item.price_inr) + shipping
    const note = `Order #${item.id} - ${item.title.slice(0, 20)}`
    const uri = `upi://pay?pa=${encodeURIComponent(drop.upi_id)}&pn=${encodeURIComponent(drop.store_name)}&am=${totalAmount.toFixed(2)}&cu=INR&tn=${encodeURIComponent(note)}`
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(uri)}&size=280x280&margin=10`
    return { shipping, totalAmount, uri, qrUrl }
  }

  const handleCopyUpi = () => {
    if (!drop?.upi_id) return
    navigator.clipboard.writeText(drop.upi_id)
    setCopiedUpi(true)
    setTimeout(() => setCopiedUpi(false), 2000)
  }

  const handleShareDrop = () => {
    const url = window.location.href
    if (navigator.share) {
      navigator.share({
        title: `${drop?.store_name} — Live Drop`,
        text: `Check out ${drop?.title} on TrendPulse!`,
        url: url
      }).catch(() => {})
    } else {
      navigator.clipboard.writeText(url)
      setCopiedLink(true)
      setTimeout(() => setCopiedLink(false), 2000)
    }
  }

  const items = drop?.items || []

  // Calculate real-time available stock across the drop
  const totalAvailableStock = useMemo(() => {
    return items.reduce((sum, item) => {
      const units = item.available_units !== undefined && item.available_units !== null
        ? item.available_units
        : (item.status === 'available' ? (item.stock_units || 1) : 0)
      return sum + units
    }, 0)
  }, [items])

  const isDropClosed = drop?.status === 'closed'
  const isDropSoldOut = drop?.status === 'sold_out' || totalAvailableStock === 0

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter(item => {
      const matchesSearch = searchQuery === '' || 
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.aesthetic?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.category?.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesSize = selectedSize === 'ALL' || item.size_label?.toUpperCase() === selectedSize
      return matchesSearch && matchesSize
    })
  }, [items, searchQuery, selectedSize])

  const uniqueSizes = useMemo(() => {
    const sizes = new Set(items.map(i => i.size_label?.toUpperCase()).filter(Boolean))
    return ['ALL', ...Array.from(sizes)]
  }, [items])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col items-center justify-center p-6 text-gray-800 font-['Outfit',sans-serif]">
        <div className="relative mb-4">
          <div className="w-10 h-10 rounded-full border-2 border-emerald-600/20 border-t-emerald-600 animate-spin" />
        </div>
        <p className="font-mono text-xs uppercase tracking-widest text-gray-500 font-semibold">Loading Live Drop...</p>
      </div>
    )
  }

  if (error || !drop) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col items-center justify-center p-6 text-center text-gray-900 font-['Outfit',sans-serif]">
        <div className="w-14 h-14 bg-rose-50 border border-rose-200 text-rose-600 rounded-2xl flex items-center justify-center mb-4 shadow-xs">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-gray-900 mb-2">Drop Link Unavailable</h1>
        <p className="text-xs font-mono text-gray-500 max-w-sm mb-6 leading-relaxed">
          {error || 'This drop is currently inactive or being prepared by the seller.'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-5 py-2.5 bg-gray-900 hover:bg-black text-white text-xs font-mono font-medium rounded-xl shadow-xs transition-all cursor-pointer"
        >
          Check Again
        </button>
      </div>
    )
  }

  const activeItemUpi = activeItem ? getUpiDetails(activeItem) : null

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-gray-900 font-['Outfit',sans-serif] selection:bg-emerald-100 selection:text-emerald-900 flex flex-col items-center">
      
      {/* ── Top Sticky Header (Clean Gallery Light) ─────────────── */}
      <header className="w-full bg-white/95 backdrop-blur-md border-b border-gray-200/80 sticky top-0 z-40 shadow-xs">
        <div className="w-full max-w-xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="relative flex h-2 w-2">
                  {!isDropClosed && !isDropSoldOut && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                  )}
                  <span className={`relative inline-flex rounded-full h-2 w-2 ${
                    isDropClosed ? 'bg-gray-400' : isDropSoldOut ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}></span>
                </span>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700">
                  {isDropClosed ? 'Drop Closed' : isDropSoldOut ? 'Sold Out' : 'Live Drop'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-base font-black tracking-tight text-gray-900">{drop.store_name}</h1>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleShareDrop}
              title="Share Drop"
              className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200/80 transition-all text-xs flex items-center gap-1.5 cursor-pointer"
            >
              {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Share2 className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline font-mono text-[11px] font-medium">{copiedLink ? 'Copied' : 'Share'}</span>
            </button>

            {drop.instagram_handle && (
              <a
                href={`https://instagram.com/${drop.instagram_handle}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-pink-50 via-rose-50 to-amber-50 hover:from-pink-100 hover:to-amber-100 text-gray-800 text-xs font-mono font-semibold border border-pink-200 transition-all shadow-2xs"
              >
                <InstagramIcon className="w-3.5 h-3.5 text-pink-600" />
                <span>@{drop.instagram_handle}</span>
              </a>
            )}
          </div>
        </div>
      </header>

      {/* ── Centered Main Content Wrapper ────────────────────────── */}
      <div className="w-full max-w-xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* Clean Drop Title & Real-Time Stock Header (Clutter-Free) */}
        <div className="flex items-center justify-between gap-3 pt-1">
          <div>
            <h2 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-gray-900">
              {drop.title}
            </h2>
            <p className="text-xs text-gray-500 font-mono mt-0.5">
              Flat ₹{drop.flat_shipping_fee || 70} India-wide shipping • Direct UPI & COD
            </p>
          </div>
          
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-bold shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
            <span>{totalAvailableStock} in stock</span>
          </div>
        </div>

        {/* Notices */}
        {isDropClosed && (
          <section className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-center space-y-1">
            <h3 className="font-bold text-sm text-amber-900">Drop Closed by Store</h3>
            <p className="text-xs font-mono text-amber-800">
              This drop is currently paused. Follow @{drop.instagram_handle} for updates.
            </p>
          </section>
        )}

        {isDropSoldOut && !isDropClosed && (
          <section className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-center space-y-1">
            <h3 className="font-bold text-sm text-emerald-900">🎉 All Pieces Sold Out!</h3>
            <p className="text-xs font-mono text-emerald-800">
              Thank you for shopping! Follow @{drop.instagram_handle} to catch the next drop first.
            </p>
          </section>
        )}

        {/* Search & Filter Bar (Only shown if multiple items exist) */}
        {items.length > 1 && (
          <section className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search pieces, styles, or sizes..."
                  className="w-full bg-white border border-gray-200 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600/20 font-mono shadow-2xs"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {uniqueSizes.length > 2 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
                  {uniqueSizes.map(size => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      className={`px-3 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                        selectedSize === size
                          ? 'bg-gray-900 text-white shadow-xs'
                          : 'bg-white text-gray-600 hover:text-gray-900 border border-gray-200 shadow-2xs'
                      }`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── Garment Product Cards ────────────────────────────────── */}
        <main className="space-y-6">
          {filteredItems.length === 0 ? (
            <div className="py-16 text-center text-gray-400 font-mono text-xs">
              No pieces match your search or filter.
            </div>
          ) : (
            filteredItems.map((item) => {
              const itemStock = item.available_units !== undefined && item.available_units !== null
                ? item.available_units
                : (item.stock_units || 1)
              const isSold = item.status === 'sold' || itemStock <= 0
              const shipping = drop.flat_shipping_fee || 70
              const totalWithShipping = parseFloat(item.price_inr) + shipping

              return (
                <article
                  key={item.id}
                  className={`bg-white border border-gray-200/90 rounded-2xl overflow-hidden shadow-sm transition-all duration-300 ${
                    isSold ? 'opacity-70 grayscale-[20%]' : 'hover:shadow-md hover:border-gray-300'
                  }`}
                >
                  {/* Photo Display - Box dynamically adjusts to natural image size, zero cropping */}
                  <div className="relative w-full bg-gray-50 overflow-hidden flex items-center justify-center">
                    {item.photo_url ? (
                      <img
                        src={item.photo_url}
                        alt={item.title}
                        className="w-full h-auto object-contain block"
                        loading="lazy"
                      />
                    ) : (
                      <div className="text-center p-12 text-gray-400 flex flex-col items-center">
                        <Sparkles className="w-10 h-10 text-gray-300 mb-2" />
                        <span className="text-xs font-mono font-semibold uppercase tracking-widest text-gray-500">
                          {item.aesthetic || 'Vintage Curated Piece'}
                        </span>
                      </div>
                    )}

                    {/* Floating Aesthetic Tag (Top Left) */}
                    {item.aesthetic && (
                      <div className="absolute top-3.5 left-3.5 bg-white/95 backdrop-blur-md text-gray-900 border border-gray-200/80 px-3 py-1 rounded-lg text-[11px] font-mono uppercase tracking-wider font-bold shadow-xs">
                        {item.aesthetic}
                      </div>
                    )}

                    {/* Condition Tag (Top Right) */}
                    {item.condition_score && (
                      <div className="absolute top-3.5 right-3.5 bg-white/95 backdrop-blur-md text-emerald-800 border border-emerald-200 px-3 py-1 rounded-lg text-[11px] font-mono font-bold shadow-xs">
                        ⭐ {item.condition_score} CONDITION
                      </div>
                    )}

                    {/* Sold Overlay */}
                    {isSold && (
                      <div className="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center">
                        <div className="bg-rose-600 text-white font-mono font-bold text-xs tracking-widest uppercase px-5 py-2 rounded-xl shadow-md">
                          SOLD OUT
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Card Body with Generous Breathing Space */}
                  <div className="p-5 sm:p-6 space-y-5">
                    {/* Title & Price Row */}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 tracking-tight leading-snug">
                          {item.title}
                        </h3>
                        
                        {/* Real-Time Stock & Category Row */}
                        <div className="flex items-center gap-2 mt-1.5">
                          {item.category && (
                            <span className="text-[11px] font-mono text-gray-500 uppercase tracking-wider font-medium">
                              {item.category}
                            </span>
                          )}
                          {item.category && <span className="text-gray-300">•</span>}
                          
                          {isSold ? (
                            <span className="text-[11px] font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200/60">
                              Out of stock
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200/60">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                              {itemStock} in stock
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-2xl font-black font-['Outfit'] text-emerald-700 tracking-tight">
                          ₹{item.price_inr}
                        </div>
                        <span className="text-[10px] font-mono text-gray-400 block mt-0.5">
                          + ₹{shipping} Express Delivery
                        </span>
                      </div>
                    </div>

                    {/* Measurements & Specs Grid */}
                    <div className="grid grid-cols-4 gap-2.5">
                      <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-center">
                        <span className="text-[10px] font-mono uppercase text-gray-400 block mb-0.5 font-medium">Size</span>
                        <strong className="text-sm font-bold font-mono text-gray-900 block">
                          {item.size_label || 'OS'}
                        </strong>
                      </div>
                      <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-center">
                        <span className="text-[10px] font-mono uppercase text-gray-400 block mb-0.5 font-medium">Chest</span>
                        <strong className="text-sm font-bold font-mono text-gray-900 block">
                          {item.chest_inches ? `${item.chest_inches}"` : '—'}
                        </strong>
                      </div>
                      <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-center">
                        <span className="text-[10px] font-mono uppercase text-gray-400 block mb-0.5 font-medium">Length</span>
                        <strong className="text-sm font-bold font-mono text-gray-900 block">
                          {item.length_inches ? `${item.length_inches}"` : '—'}
                        </strong>
                      </div>
                      <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-center">
                        <span className="text-[10px] font-mono uppercase text-gray-400 block mb-0.5 font-medium">Condition</span>
                        <strong className="text-sm font-bold font-mono text-gray-900 block">
                          {item.condition_score || '9/10'}
                        </strong>
                      </div>
                    </div>

                    {/* CTA Button with Clear Spacing */}
                    <div className="pt-2">
                      {isSold ? (
                        <button
                          disabled
                          className="w-full py-3.5 bg-gray-100 text-gray-400 rounded-xl font-mono text-xs uppercase tracking-wider font-bold cursor-not-allowed text-center"
                        >
                          Sold Out
                        </button>
                      ) : isDropClosed ? (
                        <button
                          disabled
                          className="w-full py-3.5 bg-gray-100 text-gray-400 rounded-xl font-mono text-xs uppercase tracking-wider font-bold cursor-not-allowed text-center"
                        >
                          Drop Paused
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartBuy(item)}
                          className="w-full py-4 px-6 bg-[#059669] hover:bg-[#047857] active:scale-[0.99] text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                        >
                          <span>BUY NOW • ₹{totalWithShipping.toFixed(0)} (UPI / COD)</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              )
            })
          )}
        </main>

        {/* Footer */}
        <footer className="pt-8 pb-12 text-center border-t border-gray-200/80 space-y-1.5">
          <p className="text-xs font-mono text-gray-500">
            Powered by <strong className="text-gray-900">TrendPulse</strong> Drop Engine
          </p>
          <p className="text-[11px] font-mono text-gray-400">
            Direct UPI & Cash on Delivery Available
          </p>
        </footer>
      </div>

      {/* ── Light-Themed Checkout Modal with UPI & COD Options ── */}
      {activeItem && activeItemUpi && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl border border-gray-200 shadow-2xl max-h-[92vh] flex flex-col text-gray-900 overflow-hidden">
            
            {/* Modal Header */}
            <div className="p-5 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-2 h-2 rounded-full ${checkoutStep === 'success' ? 'bg-emerald-600' : 'bg-emerald-500 animate-pulse'}`} />
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-800">
                    {checkoutStep === 'details' && 'Step 1: Shipping & Payment Method'}
                    {checkoutStep === 'payment' && 'Step 2: Instant UPI Payment'}
                    {checkoutStep === 'success' && 'Order Confirmed'}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-gray-900 truncate max-w-[280px] sm:max-w-[340px]">
                  {activeItem.title}
                </h3>
              </div>
              <button
                onClick={() => setActiveItem(null)}
                className="p-2 text-gray-400 hover:text-gray-700 rounded-full hover:bg-gray-200/60 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Selected Piece Strip */}
            <div className="px-5 py-3.5 bg-gray-50/50 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {activeItem.photo_url ? (
                  <img
                    src={activeItem.photo_url}
                    alt={activeItem.title}
                    className="w-11 h-11 rounded-lg object-contain bg-white border border-gray-200"
                  />
                ) : (
                  <div className="w-11 h-11 rounded-lg bg-gray-100 flex items-center justify-center border border-gray-200">
                    <Sparkles className="w-4 h-4 text-gray-400" />
                  </div>
                )}
                <div>
                  <span className="text-xs font-mono font-bold text-gray-900 block">Size {activeItem.size_label}</span>
                  <span className="text-[11px] font-mono text-gray-500 block">{activeItem.aesthetic || 'Vintage Piece'}</span>
                </div>
              </div>

              <div className="text-right font-mono">
                <span className="text-[10px] text-gray-400 block">Total Due</span>
                <span className="text-sm font-bold text-emerald-700">₹{activeItemUpi.totalAmount.toFixed(0)}</span>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-5 sm:p-6 overflow-y-auto space-y-4">
              
              {/* STEP 1: Address Details & Payment Method Selection Form */}
              {checkoutStep === 'details' && (
                <form onSubmit={handleProceedFromDetails} className="space-y-4">
                  <div>
                    <label className="block text-xs font-mono font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-emerald-600" />
                      <span>WhatsApp Phone Number *</span>
                    </label>
                    <div className="relative">
                      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-mono text-gray-500">
                        +91
                      </span>
                      <input
                        type="tel"
                        required
                        maxLength={10}
                        placeholder="9876543210"
                        value={buyerPhone}
                        onChange={(e) => setBuyerPhone(e.target.value.replace(/\D/g, ''))}
                        className="w-full pl-12 pr-3.5 py-3 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600/30 transition-all shadow-2xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-mono font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Full Name *</span>
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Rahul Sharma"
                        value={buyerName}
                        onChange={(e) => setBuyerName(e.target.value)}
                        className="w-full px-3.5 py-3 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600/30 transition-all shadow-2xs"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-mono font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                        <InstagramIcon className="w-3.5 h-3.5 text-pink-600" />
                        <span>Instagram (Optional)</span>
                      </label>
                      <input
                        type="text"
                        placeholder="@rahul_vintage"
                        value={buyerIg}
                        onChange={(e) => setBuyerIg(e.target.value)}
                        className="w-full px-3.5 py-3 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600/30 transition-all shadow-2xs"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-mono font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Complete Delivery Address *</span>
                    </label>
                    <textarea
                      required
                      rows="2"
                      placeholder="House / Flat No., Building, Street, Landmark..."
                      value={addressLine}
                      onChange={(e) => setAddressLine(e.target.value)}
                      className="w-full px-3.5 py-3 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600/30 transition-all shadow-2xs resize-none"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2.5">
                    <div>
                      <label className="block text-[11px] font-mono text-gray-500 mb-1">
                        Pincode *
                      </label>
                      <input
                        type="text"
                        required
                        maxLength={6}
                        placeholder="302020"
                        value={pincode}
                        onChange={(e) => handlePincodeChange(e.target.value)}
                        className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 shadow-2xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-mono text-gray-500 mb-1">
                        City *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Jaipur"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 shadow-2xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-mono text-gray-500 mb-1">
                        State *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Rajasthan"
                        value={stateName}
                        onChange={(e) => setStateName(e.target.value)}
                        className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-xl text-xs font-mono text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 shadow-2xs"
                      />
                    </div>
                  </div>

                  {city && stateName && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs font-mono text-emerald-800">
                      <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                      <span>Delivery Route: {city}, {stateName}</span>
                    </div>
                  )}

                  {/* Payment Method Selector (Direct UPI vs Cash on Delivery) */}
                  <div className="space-y-2 pt-1">
                    <label className="block text-xs font-mono font-bold text-gray-900">
                      Choose Payment Method *
                    </label>
                    <div className="grid grid-cols-2 gap-2.5">
                      {/* Direct UPI Option */}
                      <div
                        onClick={() => setPaymentMethod('upi')}
                        className={`p-3.5 rounded-xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                          paymentMethod === 'upi'
                            ? 'border-emerald-600 bg-emerald-50/60 shadow-xs'
                            : 'border-gray-200 bg-white hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold font-mono text-gray-900">
                            ⚡ Direct UPI
                          </span>
                          <span className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                            paymentMethod === 'upi' ? 'border-emerald-600 bg-emerald-600' : 'border-gray-300'
                          }`}>
                            {paymentMethod === 'upi' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-500 font-mono leading-snug">
                          Pre-filled QR / GPay / PhonePe. Instant lock.
                        </p>
                      </div>

                      {/* Cash on Delivery Option */}
                      <div
                        onClick={() => setPaymentMethod('cod')}
                        className={`p-3.5 rounded-xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                          paymentMethod === 'cod'
                            ? 'border-emerald-600 bg-emerald-50/60 shadow-xs'
                            : 'border-gray-200 bg-white hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold font-mono text-gray-900">
                            💵 Cash on Delivery
                          </span>
                          <span className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                            paymentMethod === 'cod' ? 'border-emerald-600 bg-emerald-600' : 'border-gray-300'
                          }`}>
                            {paymentMethod === 'cod' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-500 font-mono leading-snug">
                          Pay ₹{activeItemUpi.totalAmount.toFixed(0)} cash upon doorstep arrival.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Pricing Breakdown */}
                  <div className="p-4 bg-gray-50 rounded-2xl border border-gray-200 space-y-2 text-xs font-mono">
                    <div className="flex justify-between text-gray-600">
                      <span>Item Price</span>
                      <span className="text-gray-900 font-semibold">₹{activeItem.price_inr}</span>
                    </div>
                    <div className="flex justify-between text-gray-600">
                      <span>Express Shipping</span>
                      <span className="text-gray-900 font-semibold">₹{activeItemUpi.shipping}</span>
                    </div>
                    <div className="border-t border-gray-200 pt-2 flex justify-between font-bold text-sm text-gray-900">
                      <span>{paymentMethod === 'cod' ? 'Total Cash on Delivery' : 'Total Payable'}</span>
                      <span className="text-emerald-700">₹{activeItemUpi.totalAmount.toFixed(0)}</span>
                    </div>
                  </div>

                  {/* Submit CTA (Dynamic based on selected payment method) */}
                  {paymentMethod === 'upi' ? (
                    <button
                      type="submit"
                      className="w-full py-4 bg-[#059669] hover:bg-[#047857] active:scale-[0.99] text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-sm flex items-center justify-center gap-2 cursor-pointer transition-all"
                    >
                      <span>Continue to Pre-Filled UPI Pay</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isCheckingOut}
                      className="w-full py-4 bg-gray-900 hover:bg-black active:scale-[0.99] text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-sm flex items-center justify-center gap-2 cursor-pointer transition-all disabled:opacity-50"
                    >
                      {isCheckingOut ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Placing COD Order...</span>
                        </>
                      ) : (
                        <>
                          <span>Confirm Cash on Delivery (₹{activeItemUpi.totalAmount.toFixed(0)})</span>
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        </>
                      )}
                    </button>
                  )}
                </form>
              )}

              {/* STEP 2: Instant UPI Payment */}
              {checkoutStep === 'payment' && (
                <div className="space-y-4">
                  {/* Dynamic Pre-Filled QR Card */}
                  <div className="p-5 bg-emerald-50/60 border border-emerald-200 rounded-2xl text-center space-y-4">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-emerald-200 text-emerald-800 text-[11px] font-mono font-bold shadow-2xs">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Exact Price Pre-Filled • No Manual Typing</span>
                    </div>

                    {/* QR Code Presentation */}
                    <div className="inline-block p-3.5 bg-white border border-gray-200 rounded-2xl shadow-sm">
                      <img
                        src={activeItemUpi.qrUrl}
                        alt={`Scan to Pay ₹${activeItemUpi.totalAmount.toFixed(0)}`}
                        className="w-48 h-48 object-contain mx-auto"
                      />
                    </div>

                    <div className="space-y-1">
                      <div className="text-2xl font-black font-['Outfit'] text-emerald-800">
                        ₹{activeItemUpi.totalAmount.toFixed(0)}
                      </div>
                      <p className="text-xs text-gray-600 font-mono">
                        Scan with GPay, PhonePe, Paytm, or any UPI app
                      </p>
                    </div>

                    {/* Direct Native App Trigger Button (Mobile High Impact) */}
                    <a
                      href={activeItemUpi.uri}
                      className="w-full py-3.5 bg-[#059669] hover:bg-[#047857] text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-sm flex items-center justify-center gap-2"
                    >
                      <span>⚡ Open Directly in UPI App</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>

                    {/* Copyable UPI ID Strip */}
                    <div className="flex items-center justify-between px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-xs font-mono">
                      <span className="text-gray-600 truncate max-w-[200px]">
                        UPI ID: <strong className="text-gray-900">{drop.upi_id}</strong>
                      </span>
                      <button
                        type="button"
                        onClick={handleCopyUpi}
                        className="text-emerald-700 hover:text-emerald-800 flex items-center gap-1 font-bold shrink-0 cursor-pointer"
                      >
                        {copiedUpi ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Enter UTR Form */}
                  <form onSubmit={handleSubmitUTR} className="space-y-3 pt-1">
                    <div>
                      <label className="block text-xs font-mono font-bold text-gray-900 mb-1.5 text-center">
                        Enter 12-Digit UPI Reference Number (UTR) *
                      </label>
                      <input
                        type="text"
                        required
                        maxLength={16}
                        placeholder="e.g. 428910293812"
                        value={utrReference}
                        onChange={(e) => setUtrReference(e.target.value.replace(/[^a-zA-Z0-9]/g, ''))}
                        className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl font-mono text-base tracking-widest text-center text-gray-900 placeholder:text-gray-400 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 shadow-2xs"
                      />
                      <span className="block text-[11px] text-gray-500 font-mono mt-1.5 text-center">
                        Found under "UPI Ref No" or "UTR" on your payment receipt screenshot.
                      </span>
                    </div>

                    <button
                      type="submit"
                      disabled={isCheckingOut}
                      className="w-full py-4 bg-[#059669] hover:bg-[#047857] text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-sm flex items-center justify-center gap-2 cursor-pointer transition-all disabled:opacity-50"
                    >
                      {isCheckingOut ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Confirming Order...</span>
                        </>
                      ) : (
                        <>
                          <span>Verify UTR & Confirm Order</span>
                          <CheckCircle2 className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </form>
                </div>
              )}

              {/* STEP 3: Order Confirmed Screen (Works for both UPI & COD) */}
              {checkoutStep === 'success' && orderConfirmed && (
                <div className="py-6 text-center space-y-4">
                  <div className="w-16 h-16 bg-emerald-100 border border-emerald-200 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
                    <CheckCircle2 className="w-9 h-9" />
                  </div>

                  <div>
                    <h3 className="text-xl font-black text-gray-900 font-['Outfit']">
                      {orderConfirmed.utr_reference === 'COD' || orderConfirmed.payment_status === 'cod'
                        ? 'Cash on Delivery Order Placed!'
                        : 'Order Confirmed!'}
                    </h3>
                    <p className="text-xs font-mono text-gray-500 mt-1">
                      Order Reference: <strong className="text-emerald-700">ORD-{orderConfirmed.id}</strong>
                    </p>
                  </div>

                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-2xl text-left text-xs font-mono space-y-2 text-gray-700">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Recipient</span>
                      <span className="text-gray-900 font-bold">{orderConfirmed.buyer_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Destination</span>
                      <span className="text-gray-900">{orderConfirmed.city}, {orderConfirmed.pincode}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Payment Method</span>
                      <span className={`font-bold ${
                        orderConfirmed.utr_reference === 'COD' || orderConfirmed.payment_status === 'cod'
                          ? 'text-blue-700'
                          : 'text-emerald-700'
                      }`}>
                        {orderConfirmed.utr_reference === 'COD' || orderConfirmed.payment_status === 'cod'
                          ? `Cash on Delivery (₹${orderConfirmed.total_amount_inr})`
                          : `UPI (UTR: ${orderConfirmed.utr_reference})`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Dispatch Status</span>
                      <span className="text-gray-800">Dispatching within 24–48 hours</span>
                    </div>
                  </div>

                  {/* WhatsApp Seller Link */}
                  <a
                    href={`https://wa.me/?text=${encodeURIComponent(
                      orderConfirmed.utr_reference === 'COD' || orderConfirmed.payment_status === 'cod'
                        ? `Hi ${drop.store_name}! I just placed a Cash on Delivery order for ${activeItem.title}.\nOrder ID: ORD-${orderConfirmed.id}\nAmount to collect on delivery: ₹${orderConfirmed.total_amount_inr}\nShipping to: ${orderConfirmed.buyer_name}, ${orderConfirmed.city}`
                        : `Hi ${drop.store_name}! I just ordered ${activeItem.title} on your drop page.\nOrder ID: ORD-${orderConfirmed.id}\nUTR: ${orderConfirmed.utr_reference}\nShipping to: ${orderConfirmed.buyer_name}, ${orderConfirmed.city}`
                    )}`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-3.5 bg-[#25D366] hover:bg-[#22bf5b] text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-xs flex items-center justify-center gap-2"
                  >
                    <span>{orderConfirmed.utr_reference === 'COD' || orderConfirmed.payment_status === 'cod' ? 'Send Order to Seller on WhatsApp' : 'Send Receipt on WhatsApp'}</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>

                  <button
                    onClick={() => setActiveItem(null)}
                    className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-mono text-xs rounded-xl border border-gray-200 transition-colors cursor-pointer"
                  >
                    Return to Catalog
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
