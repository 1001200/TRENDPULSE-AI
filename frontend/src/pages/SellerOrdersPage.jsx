import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Package,
  CheckCircle2,
  Clock,
  Download,
  Share2,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Settings,
  Phone,
  ArrowUpRight,
  ArrowLeft,
  X,
  Check,
  Truck,
  IndianRupee,
  Users,
  ShieldCheck,
  Send,
} from 'lucide-react'
import { dropSellerAPI } from '../api/client'

export default function SellerOrdersPage() {
  const navigate = useNavigate()
  const [store, setStore] = useState(null)
  const [orders, setOrders] = useState([])
  const [sourcingCard, setSourcingCard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [verifyingId, setVerifyingId] = useState(null)

  // Store Settings Modal
  const [showSettings, setShowSettings] = useState(false)
  const [storeName, setStoreName] = useState('')
  const [storeSlug, setStoreSlug] = useState('')
  const [storeUpi, setStoreUpi] = useState('')
  const [storePhone, setStorePhone] = useState('')
  const [fulfillmentType, setFulfillmentType] = useState('self')
  const [supplierPhone, setSupplierPhone] = useState('')
  const [flatShipping, setFlatShipping] = useState('70')
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [storeRes, ordersRes, sourcingRes] = await Promise.all([
        dropSellerAPI.getStore(),
        dropSellerAPI.getOrders(),
        dropSellerAPI.getSourcingCard(),
      ])
      setStore(storeRes.data)
      setOrders(ordersRes.data)
      setSourcingCard(sourcingRes.data)

      if (storeRes.data) {
        setStoreName(storeRes.data.name || '')
        setStoreSlug(storeRes.data.slug || '')
        setStoreUpi(storeRes.data.upi_id || '')
        setStorePhone(storeRes.data.phone || '')
        setFulfillmentType(storeRes.data.fulfillment_type || 'self')
        setSupplierPhone(storeRes.data.supplier_phone || '')
        setFlatShipping(storeRes.data.flat_shipping_fee?.toString() || '70')
      }
    } catch (err) {
      console.error('Error loading seller orders:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyPayment = async (orderId) => {
    setVerifyingId(orderId)
    try {
      await dropSellerAPI.verifyOrder(orderId)
      setOrders((prev) =>
        prev.map((o) => (o.id === orderId ? { ...o, payment_status: 'verified' } : o))
      )
    } catch (err) {
      alert('Failed to verify payment.')
    } finally {
      setVerifyingId(null)
    }
  }

  const handleExportShiprocket = async () => {
    try {
      const res = await dropSellerAPI.exportShiprocketCSV()
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `shiprocket_orders_${store?.slug || 'store'}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Failed to download Shiprocket CSV.')
    }
  }

  const handleSaveSettings = async (e) => {
    e.preventDefault()
    setIsSavingSettings(true)
    try {
      const res = await dropSellerAPI.updateStore({
        name: storeName,
        slug: storeSlug,
        instagram_handle: store?.instagram_handle || 'store',
        upi_id: storeUpi,
        phone: storePhone,
        fulfillment_type: fulfillmentType,
        supplier_phone: supplierPhone || null,
        flat_shipping_fee: parseFloat(flatShipping) || 70.0,
      })
      setStore(res.data)
      setShowSettings(false)
      alert('Store settings & UPI handle updated successfully!')
    } catch (err) {
      alert('Failed to update settings.')
    } finally {
      setIsSavingSettings(false)
    }
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
        <div style={{ textAlign: 'center', color: '#999' }}>
          <div style={{
            width: 36,
            height: 36,
            border: '3px solid #e5e5e5',
            borderTopColor: '#059669',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 12px',
          }} />
          <p style={{ fontSize: 14 }}>Loading orders...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  const totalRevenue = orders.reduce((sum, o) => sum + (o.total_amount_inr || 0), 0)
  const pendingCount = orders.filter((o) => o.payment_status !== 'verified').length
  const verifiedCount = orders.filter((o) => o.payment_status === 'verified').length

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
                padding: '6px 12px',
                borderRadius: 8,
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

            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#0a0a0a', letterSpacing: '-0.2px' }}>
                Orders & Shipping Operations
              </div>
              <div style={{ fontSize: 11, color: '#777', fontWeight: 500 }}>
                {store?.name || 'Seller Studio'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => setShowSettings(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 10,
                background: '#fff',
                border: '1px solid #e5e5e5',
                color: '#555',
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.color = '#059669' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; e.currentTarget.style.color = '#555' }}
            >
              <Settings style={{ width: 14, height: 14 }} />
              <span>Store Settings & UPI</span>
            </button>

            <Link
              to="/seller/lister"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                borderRadius: 10,
                background: '#059669',
                color: '#fff',
                fontSize: 13,
                fontWeight: 600,
                textDecoration: 'none',
                boxShadow: '0 2px 6px rgba(5, 150, 105, 0.25)',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#047857'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#059669'}
            >
              <Package style={{ width: 14, height: 14 }} />
              <span>+ Add Pieces to Drop</span>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Main Container ────────────────────────────────────────── */}
      <main style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '28px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}>
        {/* Metrics Overview Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
        }}>
          <div style={{
            background: '#fff',
            borderRadius: 16,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
          }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>
              Total Orders
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: '#0a0a0a' }}>
              {orders.length}
            </div>
            <div style={{ fontSize: 12, color: '#059669', fontWeight: 600, marginTop: 4 }}>
              {verifiedCount} payments verified
            </div>
          </div>

          <div style={{
            background: '#fff',
            borderRadius: 16,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
          }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>
              Total GMV
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: '#059669' }}>
              ₹{totalRevenue.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
              Direct P2P UPI transfers
            </div>
          </div>

          <div style={{
            background: '#fff',
            borderRadius: 16,
            border: '1px solid rgba(0,0,0,0.06)',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
          }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>
              Pending Verification
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: pendingCount > 0 ? '#d97706' : '#059669' }}>
              {pendingCount}
            </div>
            <div style={{ fontSize: 12, color: pendingCount > 0 ? '#d97706' : '#888', marginTop: 4 }}>
              {pendingCount > 0 ? 'Awaiting payment confirmation' : 'All orders clear!'}
            </div>
          </div>
        </div>

        {/* Live Sourcing Intelligence Card */}
        {sourcingCard && (
          <div style={{
            background: '#fffbeb',
            border: '1px solid #fed7aa',
            borderRadius: 18,
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 16,
          }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              shrink: 0,
            }}>
              <Sparkles style={{ width: 18, height: 18 }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#92400e', marginBottom: 4 }}>
                Sourcing Intelligence: What to Thrift Next
              </div>
              <p style={{ fontSize: 13, color: '#78350f', lineHeight: 1.5, margin: '0 0 10px' }}>
                {sourcingCard.action_advice}
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: '#fff',
                  border: '1px solid #fde68a',
                  color: '#92400e',
                  padding: '3px 10px',
                  borderRadius: 100,
                }}>
                  Top Aesthetic: {sourcingCard.top_aesthetic}
                </span>
                <span style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: '#fff',
                  border: '1px solid #fde68a',
                  color: '#92400e',
                  padding: '3px 10px',
                  borderRadius: 100,
                }}>
                  Top Size: {sourcingCard.top_size}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Fulfillment Engine Bar */}
        <div style={{
          background: '#fff',
          borderRadius: 18,
          border: '1px solid rgba(0,0,0,0.06)',
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#0a0a0a', marginBottom: 2 }}>
              Fulfillment & Dispatch Engine
            </div>
            <div style={{ fontSize: 13, color: '#666' }}>
              Mode: <strong style={{ color: '#059669' }}>{store?.fulfillment_type === 'supplier' ? 'Supplier Dropshipping' : 'Self-Packed (Shiprocket / India Post)'}</strong>
              {store?.flat_shipping_fee && ` • Flat Shipping: ₹${store.flat_shipping_fee}`}
            </div>
          </div>

          <button
            onClick={handleExportShiprocket}
            disabled={orders.length === 0}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '11px 18px',
              borderRadius: 10,
              border: 'none',
              background: orders.length === 0 ? '#e5e5e5' : '#059669',
              color: '#fff',
              fontSize: 13,
              fontWeight: 600,
              cursor: orders.length === 0 ? 'not-allowed' : 'pointer',
              boxShadow: orders.length === 0 ? 'none' : '0 2px 6px rgba(5, 150, 105, 0.25)',
              transition: 'all 0.15s',
            }}
          >
            <Download style={{ width: 15, height: 15 }} />
            <span>Export Shiprocket CSV ({orders.length})</span>
          </button>
        </div>

        {/* Orders Table & Cards */}
        <div style={{
          background: '#fff',
          borderRadius: 20,
          border: '1px solid rgba(0,0,0,0.06)',
          overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{
            padding: '20px 24px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, margin: 0, color: '#0a0a0a' }}>
              Incoming Customer Orders ({orders.length})
            </h3>
          </div>

          {orders.length === 0 ? (
            <div style={{ padding: '60px 24px', textAlign: 'center' }}>
              <Package style={{ width: 36, height: 36, color: '#ccc', margin: '0 auto 12px' }} />
              <div style={{ fontSize: 15, fontWeight: 600, color: '#555', marginBottom: 4 }}>
                No orders received yet
              </div>
              <div style={{ fontSize: 13, color: '#999' }}>
                Share your drop link on Instagram Reels or stories to receive your first order!
              </div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#FAFAF9', borderBottom: '1px solid #f0f0f0' }}>
                    {['Order ID', 'Buyer & IG', 'Item Claimed', 'Amount', 'Payment Status', 'Shipping Address', 'Action'].map(
                      (h) => (
                        <th
                          key={h}
                          style={{
                            padding: '12px 18px',
                            textAlign: 'left',
                            fontWeight: 600,
                            color: '#777',
                            fontSize: 11,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o, idx) => {
                    const isVerified = o.payment_status === 'verified'
                    const isCod = o.payment_status === 'cod' || o.utr_reference === 'COD'
                    return (
                      <tr
                        key={o.id}
                        style={{
                          borderBottom: idx < orders.length - 1 ? '1px solid #f5f5f4' : 'none',
                        }}
                      >
                        <td style={{ padding: '16px 18px', fontWeight: 600, color: '#555', fontFamily: 'monospace' }}>
                          #ORD-{o.id}
                          <div style={{ fontSize: 11, color: '#999', fontWeight: 400, marginTop: 2 }}>
                            {new Date(o.created_at).toLocaleDateString('en-IN', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </td>

                        <td style={{ padding: '16px 18px' }}>
                          <div style={{ fontWeight: 600, color: '#0a0a0a' }}>{o.buyer_name}</div>
                          <div style={{ fontSize: 12, color: '#059669', fontWeight: 500, marginTop: 2 }}>
                            @{o.buyer_ig.replace(/^@/, '')}
                          </div>
                          <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>
                            {o.buyer_phone}
                          </div>
                        </td>

                        <td style={{ padding: '16px 18px' }}>
                          <div style={{ fontWeight: 600, color: '#0a0a0a' }}>{o.item_title}</div>
                        </td>

                        <td style={{ padding: '16px 18px' }}>
                          <div style={{ fontSize: 15, fontWeight: 700, color: '#059669' }}>
                            ₹{o.total_amount_inr}
                          </div>
                          <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>
                            (₹{o.shipping_fee_inr} ship)
                          </div>
                        </td>

                        <td style={{ padding: '16px 18px' }}>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            fontSize: 11,
                            fontWeight: 600,
                            padding: '3px 10px',
                            borderRadius: 100,
                            background: isVerified ? '#f0fdf4' : isCod ? '#eff6ff' : '#fffbeb',
                            color: isVerified ? '#059669' : isCod ? '#2563eb' : '#d97706',
                            border: `1px solid ${isVerified ? '#bbf7d0' : isCod ? '#bfdbfe' : '#fed7aa'}`,
                          }}>
                            {isVerified ? (
                              <><CheckCircle2 style={{ width: 12, height: 12 }} /> Verified</>
                            ) : isCod ? (
                              <><Truck style={{ width: 12, height: 12 }} /> Cash on Delivery</>
                            ) : (
                              <><Clock style={{ width: 12, height: 12 }} /> Pending</>
                            )}
                          </span>
                        </td>

                        <td style={{ padding: '16px 18px', maxWidth: 220 }}>
                          <div style={{ fontSize: 12, color: '#555', lineHeight: 1.4 }}>
                            {o.address_line}, {o.city}, {o.state} - {o.pincode}
                          </div>
                        </td>

                        <td style={{ padding: '16px 18px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {!isVerified ? (
                              <button
                                onClick={() => handleVerifyPayment(o.id)}
                                disabled={verifyingId === o.id}
                                style={{
                                  padding: '7px 12px',
                                  borderRadius: 8,
                                  border: 'none',
                                  background: '#059669',
                                  color: '#fff',
                                  fontSize: 12,
                                  fontWeight: 600,
                                  cursor: verifyingId === o.id ? 'not-allowed' : 'pointer',
                                  whiteSpace: 'nowrap',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                }}
                              >
                                <Check style={{ width: 12, height: 12 }} />
                                <span>{verifyingId === o.id ? 'Verifying...' : 'Verify Payment'}</span>
                              </button>
                            ) : (
                              <span style={{ fontSize: 12, color: '#059669', fontWeight: 600 }}>
                                ✓ Ready to Dispatch
                              </span>
                            )}

                            {o.whatsapp_supplier_url && (
                              <a
                                href={o.whatsapp_supplier_url}
                                target="_blank"
                                rel="noreferrer"
                                style={{
                                  padding: '7px 12px',
                                  borderRadius: 8,
                                  border: '1px solid #bbf7d0',
                                  background: '#f0fdf4',
                                  color: '#059669',
                                  fontSize: 11,
                                  fontWeight: 600,
                                  textDecoration: 'none',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                }}
                              >
                                <Send style={{ width: 11, height: 11 }} />
                                <span>Forward Supplier</span>
                              </a>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* ── Settings Modal ────────────────────────────────────────── */}
      {showSettings && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.45)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          zIndex: 100,
        }}>
          <div style={{
            background: '#fff',
            borderRadius: 20,
            width: '100%',
            maxWidth: 480,
            padding: 28,
            boxShadow: '0 20px 40px rgba(0,0,0,0.12)',
            border: '1px solid rgba(0,0,0,0.06)',
            position: 'relative',
          }}>
            <button
              onClick={() => setShowSettings(false)}
              style={{
                position: 'absolute',
                top: 20,
                right: 20,
                background: '#f5f5f4',
                border: 'none',
                borderRadius: '50%',
                width: 30,
                height: 30,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: '#666',
              }}
            >
              <X style={{ width: 14, height: 14 }} />
            </button>

            <h3 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 6px', color: '#0a0a0a' }}>
              Store & Payment Settings
            </h3>
            <p style={{ fontSize: 13, color: '#777', margin: '0 0 20px', lineHeight: 1.4 }}>
              Update your direct UPI ID and fulfillment configurations.
            </p>

            <form onSubmit={handleSaveSettings} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                  Store / Brand Name
                </label>
                <input
                  type="text"
                  required
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 10,
                    border: '1.5px solid #e5e5e5',
                    fontSize: 14,
                    background: '#FAFAF9',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                  Direct Payee UPI ID *
                </label>
                <input
                  type="text"
                  required
                  value={storeUpi}
                  onChange={(e) => setStoreUpi(e.target.value)}
                  placeholder="name@okaxis"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 10,
                    border: '1.5px solid #e5e5e5',
                    fontSize: 14,
                    background: '#FAFAF9',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Flat Shipping Fee (₹)
                  </label>
                  <input
                    type="number"
                    value={flatShipping}
                    onChange={(e) => setFlatShipping(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 14,
                      background: '#FAFAF9',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#333', marginBottom: 5 }}>
                    Fulfillment Mode
                  </label>
                  <select
                    value={fulfillmentType}
                    onChange={(e) => setFulfillmentType(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1.5px solid #e5e5e5',
                      fontSize: 13,
                      background: '#FAFAF9',
                      outline: 'none',
                    }}
                  >
                    <option value="self">Self-Packed</option>
                    <option value="supplier">Supplier Dropship</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowSettings(false)}
                  style={{
                    flex: 1,
                    padding: '11px',
                    borderRadius: 10,
                    border: '1px solid #e5e5e5',
                    background: '#fff',
                    color: '#666',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingSettings}
                  style={{
                    flex: 1,
                    padding: '11px',
                    borderRadius: 10,
                    border: 'none',
                    background: '#059669',
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: isSavingSettings ? 'not-allowed' : 'pointer',
                    boxShadow: '0 2px 6px rgba(5, 150, 105, 0.25)',
                  }}
                >
                  {isSavingSettings ? 'Saving...' : 'Save Settings'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
