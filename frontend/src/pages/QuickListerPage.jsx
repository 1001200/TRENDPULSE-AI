import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Shirt,
  Sparkles,
  ExternalLink,
  ArrowRight,
  Download,
  QrCode,
  CheckCircle2,
  ArrowLeft,
  Upload,
  Image as ImageIcon,
  Trash2,
  Check,
  Copy,
  AlertCircle,
  Layers,
} from 'lucide-react'
import { dropSellerAPI } from '../api/client'

export default function QuickListerPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [store, setStore] = useState(null)
  const [drops, setDrops] = useState([])
  const [selectedDropId, setSelectedDropId] = useState('')
  const [loading, setLoading] = useState(true)

  // New Item Form State
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('Tops')
  const [sizeLabel, setSizeLabel] = useState('L')
  const [chestInches, setChestInches] = useState('42')
  const [lengthInches, setLengthInches] = useState('28')
  const [priceInr, setPriceInr] = useState('799')
  const [conditionScore, setConditionScore] = useState('9/10')
  const [stockUnits, setStockUnits] = useState('1')

  // Custom Photo Upload State
  const [photoUrl, setPhotoUrl] = useState('')
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [showUrlFallback, setShowUrlFallback] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  // Success Item & QR Code State
  const [createdItem, setCreatedItem] = useState(null)
  const [copiedUpi, setCopiedUpi] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeletingItemId, setIsDeletingItemId] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [storeRes, dropsRes] = await Promise.all([
        dropSellerAPI.getStore(),
        dropSellerAPI.getDrops(),
      ])
      setStore(storeRes.data)
      setDrops(dropsRes.data)
      const queryDropId = new URLSearchParams(window.location.search).get('dropId')
      if (queryDropId && dropsRes.data.some((d) => d.id.toString() === queryDropId.toString())) {
        setSelectedDropId(queryDropId.toString())
      } else if (dropsRes.data.length > 0) {
        setSelectedDropId(dropsRes.data[0].id.toString())
      }
    } catch (err) {
      console.error('Failed to load seller drops:', err)
    } finally {
      setLoading(false)
    }
  }

  // Handle local device photo upload
  const handleDeviceFileUpload = async (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setUploadError('Please select a valid image file (PNG, JPG, WEBP).')
      return
    }

    setUploadError('')
    setIsUploadingPhoto(true)
    try {
      const res = await dropSellerAPI.uploadImage(file)
      if (res.data?.url) {
        setPhotoUrl(res.data.url)
      }
    } catch (err) {
      console.error('Failed to upload image:', err)
      setUploadError('Failed to upload image from device. You can paste a web URL instead.')
    } finally {
      setIsUploadingPhoto(false)
    }
  }

  const onFileInputChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      handleDeviceFileUpload(file)
    }
  }

  const onDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const onDragLeave = () => {
    setIsDragging(false)
  }

  const onDropFile = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleDeviceFileUpload(file)
    }
  }

  const handleQuickUpload = async (e) => {
    e.preventDefault()
    if (!selectedDropId) {
      alert('Please select a drop first.')
      return
    }

    setIsSubmitting(true)
    try {
      const parsedStock = Math.max(1, parseInt(stockUnits, 10) || 1)
      const payload = {
        title: title.trim(),
        category,
        size_label: sizeLabel,
        chest_inches: parseFloat(chestInches) || null,
        length_inches: parseFloat(lengthInches) || null,
        price_inr: parseFloat(priceInr),
        condition_score: conditionScore,
        photo_url: photoUrl.trim() || null,
        stock_units: parsedStock,
        available_units: parsedStock,
      }
      const res = await dropSellerAPI.addItem(selectedDropId, payload)
      setCreatedItem(res.data)

      // Refresh drops list to update item catalog
      const dropsRes = await dropSellerAPI.getDrops()
      setDrops(dropsRes.data)

      // Reset form fields
      setTitle('')
      setPhotoUrl('')
      setStockUnits('1')
      setShowUrlFallback(false)
    } catch (err) {
      console.error('Failed to list piece:', err)
      alert(err.response?.data?.detail || 'Failed to list piece. Please check your fields.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Are you sure you want to remove this piece from the drop?')) return
    setIsDeletingItemId(itemId)
    try {
      await dropSellerAPI.deleteItem(selectedDropId, itemId)
      const dropsRes = await dropSellerAPI.getDrops()
      setDrops(dropsRes.data)
      if (createdItem?.id === itemId) {
        setCreatedItem(null)
      }
    } catch (err) {
      console.error('Failed to delete item:', err)
      alert('Failed to remove item.')
    } finally {
      setIsDeletingItemId(null)
    }
  }

  const activeDrop = drops.find((d) => d.id.toString() === selectedDropId)
  const dropSlug = activeDrop?.slug || store?.slug || 'drop'
  const publicDropUrl = `${window.location.origin}/drop/${dropSlug}`

  const getItemUpiDetails = (item) => {
    if (!store?.upi_id) return null
    const shipping = store.flat_shipping_fee || 70
    const totalAmount = parseFloat(item.price_inr) + shipping
    const note = `Order #${item.id} - ${item.title.slice(0, 20)}`
    const uri = `upi://pay?pa=${encodeURIComponent(store.upi_id)}&pn=${encodeURIComponent(store.name)}&am=${totalAmount.toFixed(2)}&cu=INR&tn=${encodeURIComponent(note)}`
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(uri)}&size=260x260&margin=10`
    return { shipping, totalAmount, uri, qrUrl }
  }

  const downloadQrImage = async (qrUrl, itemTitle) => {
    try {
      const res = await fetch(qrUrl)
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `UPI-QR-${itemTitle.slice(0, 15).replace(/[^a-zA-Z0-9]+/g, '-')}.png`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      window.open(qrUrl, '_blank')
    }
  }

  const copyUpiLink = (uri) => {
    navigator.clipboard.writeText(uri)
    setCopiedUpi(true)
    setTimeout(() => setCopiedUpi(false), 2000)
  }

  if (loading) {
    return (
      <div style={{
        fontFamily: "'Inter', sans-serif",
        background: '#FAF9F6',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <div style={{ textAlign: 'center', color: '#888' }}>
          <div style={{
            width: 36,
            height: 36,
            border: '3px solid #e5e5e5',
            borderTopColor: '#059669',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 12px',
          }} />
          <p style={{ fontSize: 14, fontWeight: 500 }}>Loading piece lister...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  const itemsList = activeDrop?.items || []
  const createdItemUpi = createdItem ? getItemUpiDetails(createdItem) : null

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      background: '#FAF9F6',
      minHeight: '100vh',
      color: '#1a1a1a',
      paddingBottom: 80,
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* ── Top Header Navigation Bar ────────────────────────────── */}
      <header style={{
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        background: 'rgba(250, 249, 246, 0.95)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 30,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <Link
              to="/dashboard"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 14px',
                borderRadius: 9,
                background: '#fff',
                border: '1px solid #e5e5e5',
                color: '#555',
                fontSize: 13,
                fontWeight: 500,
                textDecoration: 'none',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#555' }}
            >
              <ArrowLeft style={{ width: 14, height: 14 }} />
              <span>Dashboard</span>
            </Link>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 34,
                height: 34,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #059669, #047857)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: 14,
                color: '#fff',
                boxShadow: '0 2px 6px rgba(5, 150, 105, 0.2)',
              }}>
                {store?.name ? store.name[0].toUpperCase() : 'T'}
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#0a0a0a', letterSpacing: '-0.2px' }}>
                  {store?.name || 'Your Store'}
                </div>
                <div style={{ fontSize: 12, color: '#777', fontWeight: 500 }}>
                  Item Lister & Stock Intake
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {activeDrop && (
              <a
                href={publicDropUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '7px 14px',
                  borderRadius: 9,
                  background: '#fff',
                  border: '1px solid #e5e5e5',
                  color: '#444',
                  fontSize: 13,
                  fontWeight: 500,
                  textDecoration: 'none',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#444' }}
              >
                <span>View Storefront</span>
                <ExternalLink style={{ width: 13, height: 13 }} />
              </a>
            )}
          </div>
        </div>
      </header>

      {/* ── Main Workspace ────────────────────────────────────────── */}
      <main style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '24px 24px',
      }}>
        {/* Simple Clean Drop Selector Header */}
        <div style={{
          background: '#fff',
          borderRadius: 16,
          border: '1px solid rgba(0,0,0,0.06)',
          padding: '16px 22px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 14,
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Layers style={{ width: 18, height: 18, color: '#059669' }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: '#666' }}>
              Listing items for drop:
            </span>
            <select
              value={selectedDropId}
              onChange={(e) => {
                setSelectedDropId(e.target.value)
                setCreatedItem(null)
              }}
              style={{
                padding: '8px 14px',
                borderRadius: 8,
                border: '1.5px solid #e5e5e5',
                fontSize: 14,
                fontWeight: 600,
                color: '#0a0a0a',
                background: '#FAFAF9',
                outline: 'none',
                cursor: 'pointer',
              }}
              onFocus={(e) => e.target.style.borderColor = '#059669'}
              onBlur={(e) => e.target.style.borderColor = '#e5e5e5'}
            >
              {drops.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          <div style={{ fontSize: 13, color: '#777' }}>
            <span style={{ fontWeight: 700, color: '#059669' }}>{itemsList.length}</span> {itemsList.length === 1 ? 'piece' : 'pieces'} in this drop
          </div>
        </div>

        {/* ── 2-Column Grid: Add Piece Form on Left, QR & Catalog on Right ── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 24,
          alignItems: 'start',
        }}>
          {/* ── Left Column: Add Piece Form ──────────────────────── */}
          <div style={{
            background: '#fff',
            borderRadius: 18,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 9,
                background: '#f0fdf4',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Shirt style={{ width: 16, height: 16 }} />
              </div>
              <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0, color: '#0a0a0a' }}>
                Add Piece to Drop
              </h2>
            </div>
            <p style={{ fontSize: 13, color: '#777', marginBottom: 20, lineHeight: 1.4 }}>
              Upload item photo, specify measurements, price, and stock quantity.
            </p>

            <form onSubmit={handleQuickUpload} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Photo Upload Section */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 6 }}>
                  Garment Photo *
                </label>

                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={onFileInputChange}
                  style={{ display: 'none' }}
                />

                {photoUrl ? (
                  <div style={{
                    position: 'relative',
                    borderRadius: 12,
                    overflow: 'hidden',
                    border: '1.5px solid #a7f3d0',
                    background: '#f0fdf4',
                    padding: 8,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}>
                    <img
                      src={photoUrl}
                      alt="Garment preview"
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: 8,
                        objectFit: 'cover',
                        border: '1px solid #e5e5e5',
                      }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <CheckCircle2 style={{ width: 14, height: 14, color: '#059669' }} />
                        <span style={{ fontSize: 13, fontWeight: 600, color: '#047857' }}>
                          Photo uploaded from device
                        </span>
                      </div>
                      <div style={{ fontSize: 11, color: '#666', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {photoUrl}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setPhotoUrl('')
                        if (fileInputRef.current) fileInputRef.current.value = ''
                      }}
                      style={{
                        padding: '6px 10px',
                        borderRadius: 8,
                        border: '1px solid #e5e5e5',
                        background: '#fff',
                        color: '#dc2626',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <Trash2 style={{ width: 13, height: 13 }} />
                      <span>Remove</span>
                    </button>
                  </div>
                ) : (
                  <div>
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={onDragOver}
                      onDragLeave={onDragLeave}
                      onDrop={onDropFile}
                      style={{
                        border: `2px dashed ${isDragging ? '#059669' : '#d1d5db'}`,
                        borderRadius: 12,
                        padding: '22px 16px',
                        textAlign: 'center',
                        cursor: isUploadingPhoto ? 'wait' : 'pointer',
                        background: isDragging ? '#f0fdf4' : '#FAFAF9',
                        transition: 'all 0.15s',
                      }}
                    >
                      {isUploadingPhoto ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 24,
                            height: 24,
                            border: '2px solid #e5e5e5',
                            borderTopColor: '#059669',
                            borderRadius: '50%',
                            animation: 'spin 0.8s linear infinite',
                          }} />
                          <span style={{ fontSize: 13, color: '#059669', fontWeight: 600 }}>
                            Uploading photo from device...
                          </span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                          <div style={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            background: '#e0e7ff',
                            color: '#4f46e5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 2,
                          }}>
                            <Upload style={{ width: 18, height: 18, color: '#059669' }} />
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#111' }}>
                            Click to upload photo from your device storage
                          </div>
                          <div style={{ fontSize: 11, color: '#777' }}>
                            or drag and drop here (JPG, PNG, WEBP)
                          </div>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 6 }}>
                      <button
                        type="button"
                        onClick={() => setShowUrlFallback(!showUrlFallback)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#666',
                          fontSize: 11,
                          fontWeight: 500,
                          cursor: 'pointer',
                          textDecoration: 'underline',
                          padding: 0,
                        }}
                      >
                        {showUrlFallback ? 'Hide URL input' : 'Or paste an image web URL'}
                      </button>
                    </div>

                    {showUrlFallback && (
                      <div style={{ marginTop: 8 }}>
                        <input
                          type="url"
                          placeholder="https://images.unsplash.com/... or Imgur"
                          value={photoUrl}
                          onChange={(e) => setPhotoUrl(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '9px 12px',
                            borderRadius: 8,
                            border: '1.5px solid #e5e5e5',
                            fontSize: 13,
                            background: '#fff',
                            outline: 'none',
                            boxSizing: 'border-box',
                          }}
                        />
                      </div>
                    )}

                    {uploadError && (
                      <div style={{
                        marginTop: 8,
                        fontSize: 12,
                        color: '#dc2626',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}>
                        <AlertCircle style={{ width: 14, height: 14 }} />
                        <span>{uploadError}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Garment Title */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                  Garment Title & Brand *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 1996 Washed Carhartt Detroit Jacket"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: 10,
                    border: '1.5px solid #e5e5e5',
                    fontSize: 14,
                    outline: 'none',
                    boxSizing: 'border-box',
                    background: '#FAFAF9',
                  }}
                  onFocus={(e) => { e.target.style.borderColor = '#059669'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e5e5'; e.target.style.background = '#FAFAF9' }}
                />
                <span style={{ display: 'block', fontSize: 11, color: '#888', marginTop: 4 }}>
                  ✨ AI automatically classifies aesthetic (Vintage Streetwear, Y2K, Minimalist, Grunge)
                </span>
              </div>

              {/* Price & Size */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Selling Price (₹) *
                  </label>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    border: '1.5px solid #e5e5e5',
                    borderRadius: 10,
                    background: '#FAFAF9',
                    padding: '0 12px',
                  }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#059669', marginRight: 4 }}>₹</span>
                    <input
                      type="number"
                      required
                      placeholder="1499"
                      value={priceInr}
                      onChange={(e) => setPriceInr(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 0',
                        border: 'none',
                        background: 'transparent',
                        fontSize: 14,
                        fontWeight: 700,
                        color: '#059669',
                        outline: 'none',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Size Label *
                  </label>
                  <select
                    value={sizeLabel}
                    onChange={(e) => setSizeLabel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      fontWeight: 500,
                      background: '#FAFAF9',
                      outline: 'none',
                    }}
                  >
                    <option value="XS">XS</option>
                    <option value="S">S</option>
                    <option value="M">M</option>
                    <option value="L">L</option>
                    <option value="XL">XL</option>
                    <option value="XXL">XXL</option>
                    <option value="Free Size">Free Size (Oversized)</option>
                  </select>
                </div>
              </div>

              {/* Units in Stock Quantity */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                  Units in Stock (Inventory) *
                </label>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  border: '1.5px solid #e5e5e5',
                  borderRadius: 10,
                  background: '#FAFAF9',
                  padding: '0 12px',
                }}>
                  <input
                    type="number"
                    min="1"
                    required
                    value={stockUnits}
                    onChange={(e) => setStockUnits(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 0',
                      border: 'none',
                      background: 'transparent',
                      fontSize: 14,
                      fontWeight: 700,
                      color: '#111',
                      outline: 'none',
                    }}
                  />
                  <span style={{ fontSize: 12, color: '#666', fontWeight: 600 }}>units</span>
                </div>
                <span style={{ display: 'block', fontSize: 11, color: '#059669', marginTop: 4 }}>
                  ⚡ When all units are purchased, this piece will automatically be marked <strong>SOLD OUT</strong> on the storefront.
                </span>
              </div>

              {/* Measurements */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Chest Width (Inches)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    placeholder="42"
                    value={chestInches}
                    onChange={(e) => setChestInches(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      background: '#FAFAF9',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Length (Inches)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    placeholder="28"
                    value={lengthInches}
                    onChange={(e) => setLengthInches(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      background: '#FAFAF9',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>

              {/* Category & Condition */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      fontWeight: 500,
                      background: '#FAFAF9',
                      outline: 'none',
                    }}
                  >
                    <option value="Tops">Tops & Tees</option>
                    <option value="Jackets">Jackets & Outerwear</option>
                    <option value="Hoodies">Hoodies & Sweaters</option>
                    <option value="Bottoms">Bottoms & Pants</option>
                    <option value="Dresses">Dresses & Skirts</option>
                    <option value="Accessories">Accessories</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Condition Score
                  </label>
                  <select
                    value={conditionScore}
                    onChange={(e) => setConditionScore(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      fontWeight: 500,
                      background: '#FAFAF9',
                      outline: 'none',
                    }}
                  >
                    <option value="10/10 Mint">10/10 Mint</option>
                    <option value="9.5/10 Pristine">9.5/10 Pristine</option>
                    <option value="9/10 Great">9/10 Great</option>
                    <option value="8/10 Vintage">8/10 Vintage</option>
                    <option value="Distressed">Distressed</option>
                  </select>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting || isUploadingPhoto}
                style={{
                  width: '100%',
                  marginTop: 6,
                  padding: '13px 20px',
                  borderRadius: 12,
                  border: 'none',
                  background: '#059669',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: (isSubmitting || isUploadingPhoto) ? 'not-allowed' : 'pointer',
                  opacity: (isSubmitting || isUploadingPhoto) ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => { if (!isSubmitting) e.target.style.background = '#047857' }}
                onMouseLeave={(e) => { if (!isSubmitting) e.target.style.background = '#059669' }}
              >
                {isSubmitting ? (
                  <span>Saving Piece...</span>
                ) : (
                  <>
                    <span>Add Piece to Drop & Generate Payment QR</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* ── Right Column: QR Code Result & Pieces Catalog ─────── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Newly Created Piece QR Code Preview Card */}
            {createdItem && createdItemUpi && (
              <div style={{
                background: '#fff',
                borderRadius: 18,
                border: '2px solid #a7f3d0',
                padding: '22px',
                boxShadow: '0 4px 14px rgba(5, 150, 105, 0.08)',
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: 12,
                  borderBottom: '1px solid #f0f0f0',
                  marginBottom: 14,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CheckCircle2 style={{ width: 18, height: 18, color: '#059669' }} />
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#047857' }}>
                      Piece Listed Successfully!
                    </span>
                  </div>
                  <span style={{
                    fontSize: 11,
                    fontWeight: 600,
                    background: '#f0fdf4',
                    color: '#059669',
                    border: '1px solid #bbf7d0',
                    padding: '3px 10px',
                    borderRadius: 100,
                  }}>
                    {createdItem.aesthetic}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                  <div style={{
                    background: '#fff',
                    padding: 6,
                    borderRadius: 10,
                    border: '1px solid #e5e5e5',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  }}>
                    <img
                      src={createdItemUpi.qrUrl}
                      alt={`UPI QR for ${createdItem.title}`}
                      style={{ width: 100, height: 100, objectFit: 'contain', display: 'block' }}
                    />
                  </div>

                  <div style={{ flex: 1, minWidth: 160 }}>
                    <h4 style={{ fontSize: 15, fontWeight: 700, color: '#0a0a0a', margin: '0 0 4px' }}>
                      {createdItem.title}
                    </h4>
                    <p style={{ fontSize: 12, color: '#777', margin: '0 0 8px' }}>
                      Size: {createdItem.size_label} • Stock: {createdItem.stock_units || 1} units
                    </p>

                    <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Pre-filled UPI Checkout:</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: '#059669', lineHeight: 1 }}>
                      ₹{createdItemUpi.totalAmount.toFixed(0)}
                    </div>
                    <div style={{ fontSize: 11, color: '#888', marginTop: 3 }}>
                      (₹{createdItem.price_inr} + ₹{createdItemUpi.shipping} shipping)
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 14 }}>
                  <button
                    type="button"
                    onClick={() => downloadQrImage(createdItemUpi.qrUrl, createdItem.title)}
                    style={{
                      padding: '9px',
                      borderRadius: 9,
                      border: 'none',
                      background: '#059669',
                      color: '#fff',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 6,
                    }}
                  >
                    <Download style={{ width: 14, height: 14 }} />
                    <span>Download QR</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => copyUpiLink(createdItemUpi.uri)}
                    style={{
                      padding: '9px',
                      borderRadius: 9,
                      border: '1px solid #e5e5e5',
                      background: '#fff',
                      color: '#444',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 6,
                    }}
                  >
                    {copiedUpi ? <Check style={{ width: 14, height: 14, color: '#059669' }} /> : <Copy style={{ width: 14, height: 14 }} />}
                    <span>{copiedUpi ? 'Copied' : 'Copy UPI Link'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Pieces in this Drop Catalog */}
            <div style={{
              background: '#fff',
              borderRadius: 18,
              border: '1px solid rgba(0,0,0,0.06)',
              padding: '24px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Shirt style={{ width: 18, height: 18, color: '#059669' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: '#0a0a0a' }}>
                    Pieces in this Drop ({itemsList.length})
                  </h3>
                </div>
              </div>

              {itemsList.length === 0 ? (
                <div style={{
                  padding: '40px 20px',
                  textAlign: 'center',
                  border: '1px dashed #e5e5e5',
                  borderRadius: 14,
                }}>
                  <Shirt style={{ width: 32, height: 32, color: '#ccc', margin: '0 auto 10px' }} />
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#555', marginBottom: 4 }}>
                    No pieces listed in this drop yet
                  </div>
                  <div style={{ fontSize: 12, color: '#999' }}>
                    Fill the form on the left to add garments to this drop collection!
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {itemsList.map((item) => {
                    const isSoldOut = item.status === 'sold' || (item.available_units !== undefined && item.available_units <= 0)
                    const availUnits = item.available_units !== undefined ? item.available_units : (item.stock_units || 1)

                    return (
                      <div
                        key={item.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '12px 14px',
                          borderRadius: 12,
                          background: '#FAFAF9',
                          border: '1px solid #f0f0f0',
                          gap: 12,
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                          {item.photo_url ? (
                            <img
                              src={item.photo_url}
                              alt={item.title}
                              style={{
                                width: 44,
                                height: 44,
                                borderRadius: 8,
                                objectFit: 'cover',
                                border: '1px solid #e5e5e5',
                              }}
                            />
                          ) : (
                            <div style={{
                              width: 44,
                              height: 44,
                              borderRadius: 8,
                              background: '#f0fdf4',
                              color: '#059669',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: 12,
                              fontWeight: 700,
                            }}>
                              {item.size_label}
                            </div>
                          )}

                          <div style={{ minWidth: 0 }}>
                            <div style={{ fontSize: 14, fontWeight: 600, color: '#0a0a0a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {item.title}
                            </div>
                            <div style={{ fontSize: 12, color: '#777', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2, flexWrap: 'wrap' }}>
                              <span>Size: {item.size_label}</span>
                              <span>•</span>
                              <span style={{ color: '#059669', fontWeight: 600 }}>{item.aesthetic}</span>
                              <span>•</span>
                              <span style={{
                                fontWeight: 600,
                                color: isSoldOut ? '#dc2626' : '#2563eb',
                              }}>
                                {isSoldOut ? 'Sold Out' : `${availUnits} in stock`}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
                          <div style={{ fontSize: 15, fontWeight: 700, color: '#0a0a0a' }}>
                            ₹{item.price_inr}
                          </div>

                          <button
                            type="button"
                            disabled={isDeletingItemId === item.id}
                            onClick={() => handleDeleteItem(item.id)}
                            title="Remove piece"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: '#999',
                              cursor: 'pointer',
                              padding: 6,
                              borderRadius: 6,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              transition: 'color 0.15s',
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.color = '#dc2626'}
                            onMouseLeave={(e) => e.currentTarget.style.color = '#999'}
                          >
                            <Trash2 style={{ width: 15, height: 15 }} />
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
