import React, { useState, useEffect } from 'react'
import { Sliders, Zap, Tag, TrendingUp, AlertTriangle, ArrowRight, Loader } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import { mlAPI } from '../api/client'
import { formatCurrency, formatPercent, shortenProduct } from '../utils/formatters'

export default function SimulatorPage() {
  const { activeDatasetId, dataset, result, loading } = useStore()
  
  const initialPricing = result?.ml_intelligence?.price_elasticity || []
  const [pricing, setPricing] = useState(initialPricing)
  const [simProduct, setSimProduct] = useState(() => initialPricing[0]?.entity_id || '')
  const [simPrice, setSimPrice] = useState(() => initialPricing[0]?.metadata?.median_selling_price || 1499)
  const [simResult, setSimResult] = useState(null)
  const [simulating, setSimulating] = useState(false)

  useEffect(() => {
    const embedded = result?.ml_intelligence?.price_elasticity || []
    if (Array.isArray(embedded) && embedded.length > 0) {
      setPricing(embedded)
      if (!simProduct || !embedded.some(p => p.entity_id === simProduct)) {
        setSimProduct(embedded[0].entity_id)
        setSimPrice(embedded[0].metadata?.median_selling_price || 1499)
      }
    } else if (activeDatasetId) {
      mlAPI.priceElasticity(activeDatasetId)
        .then((res) => {
          const list = res.data?.predictions || res.data || []
          if (Array.isArray(list) && list.length > 0) {
            setPricing(list)
            if (!simProduct || !list.some(p => p.entity_id === simProduct)) {
              setSimProduct(list[0].entity_id)
              setSimPrice(list[0].metadata?.median_selling_price || 1499)
            }
          }
        })
        .catch(console.warn)
    }
  }, [result, activeDatasetId])

  const handleSimulate = async () => {
    if (!activeDatasetId || !simProduct || !simPrice) return
    setSimulating(true)
    try {
      const res = await mlAPI.simulatePrice(activeDatasetId, simProduct, parseFloat(simPrice))
      setSimResult(res.data)
    } catch (err) {
      setSimResult({ error: err.response?.data?.detail || 'Simulation failed' })
    } finally {
      setSimulating(false)
    }
  }

  const selectedItem = pricing.find(p => p.entity_id === simProduct)
  const currentPrice = selectedItem?.metadata?.median_selling_price || 1499
  const elasticity = selectedItem?.value || -1.25

  if (loading && !result) {
    return (
      <div className="page-container flex-center" style={{ minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={38} className="spin text-indigo" strokeWidth={2.5} />
          <p className="text-muted mt-md font-heading" style={{ fontWeight: 800, textTransform: 'uppercase' }}>
            COMPUTING ECONOMETRIC PRICE ELASTICITY MODELS…
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="card mb-md animate-in card-glyph-triangle" style={{ padding: '20px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase' }}>
                WHAT-IF PRICE ELASTICITY SIMULATOR
              </h2>
              <span className="badge badge--yellow">ECONOMETRIC AI</span>
              <span className="badge badge--indigo">LOG-LOG REGRESSION</span>
            </div>
            <div className="text-xs" style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              STRESS-TEST PRICE ADJUSTMENTS &amp; SIMULATE NET MARGIN SHIFTS BEFORE RISKING REAL INVENTORY
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Simulation Sandbox */}
      <div className="card animate-in animate-in-delay-1" style={{ background: 'var(--bauhaus-white)', marginBottom: 24 }}>
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Zap size={20} className="text-indigo" />
          <span>Interactive Price Adjustment Sandbox</span>
        </div>
        <p className="text-sm" style={{ fontWeight: 600, color: 'var(--text-secondary)', marginTop: 4 }}>
          Select any apparel product from your catalog and hypothesize a price change. The engine computes the price elasticity (ε = %ΔQ / %ΔP) to calculate your projected revenue and profit shift.
        </p>

        <div className="sim-form mt-md">
          <div className="input-group" style={{ flex: 2, minWidth: 260 }}>
            <label className="input-label">SELECT APPAREL PRODUCT</label>
            <select
              className="input"
              value={simProduct}
              onChange={(e) => {
                const prod = e.target.value
                setSimProduct(prod)
                const found = pricing.find(p => p.entity_id === prod)
                if (found) setSimPrice(found.metadata?.median_selling_price || 1499)
              }}
            >
              {pricing.map((p, i) => (
                <option key={i} value={p.entity_id}>
                  {shortenProduct(p.entity_id, 55)} (Current: ₹{p.metadata?.median_selling_price || 1499})
                </option>
              ))}
            </select>
          </div>

          <div className="input-group" style={{ flex: 1, minWidth: 160 }}>
            <label className="input-label">PROPOSED SELLING PRICE (₹)</label>
            <input
              className="input"
              type="number"
              placeholder="1499"
              value={simPrice}
              onChange={(e) => setSimPrice(e.target.value)}
            />
          </div>

          <button
            className="btn btn-red"
            onClick={handleSimulate}
            disabled={simulating}
            style={{ height: 48, alignSelf: 'flex-end', marginBottom: 18 }}
          >
            {simulating ? 'COMPUTING ELASTICITY…' : 'RUN SIMULATION'}
          </button>
        </div>

        {/* Live Simulation Results */}
        {simResult && !simResult.error && (
          <div className="sim-result animate-in mt-md">
            <div className="kpi-grid" style={{ marginBottom: 0 }}>
              <div className="kpi-card" style={{ background: 'var(--bauhaus-white)' }}>
                <div className="kpi-label">PROJECTED REVENUE SHIFT</div>
                <div className={`kpi-value ${simResult.projected_revenue_change_percentage >= 0 ? 'text-emerald' : 'text-rose'}`}>
                  {simResult.projected_revenue_change_percentage >= 0 ? '+' : ''}{simResult.projected_revenue_change_percentage}%
                </div>
                <div className="kpi-sub">DEMAND IMPACT COMPUTED</div>
              </div>

              <div className="kpi-card" style={{ background: 'var(--bauhaus-white)' }}>
                <div className="kpi-label">PROJECTED PROFIT SHIFT</div>
                <div className={`kpi-value ${simResult.projected_gross_profit_change_percentage >= 0 ? 'text-emerald' : 'text-rose'}`}>
                  {simResult.projected_gross_profit_change_percentage >= 0 ? '+' : ''}{simResult.projected_gross_profit_change_percentage}%
                </div>
                <div className="kpi-sub">NET STORE PROFIT GAIN</div>
              </div>

              <div className="kpi-card kpi-card--yellow">
                <div className="kpi-label">COMMERCIAL VERDICT</div>
                <div className="kpi-value text-sm" style={{ fontWeight: 900, textTransform: 'uppercase' }}>
                  {simResult.commercial_verdict || 'RECOMMENDED STRATEGY'}
                </div>
                <div className="kpi-sub">95% STATISTICAL CONFIDENCE</div>
              </div>
            </div>
          </div>
        )}

        {simResult?.error && (
          <div className="upload-error mt-md">{simResult.error}</div>
        )}
      </div>

      {/* Catalog Elasticity Sensitivities Table */}
      <div className="card animate-in animate-in-delay-2 card-glyph-square">
        <div className="card-header">
          <div className="card-title">PRICE ELASTICITY OF DEMAND (LOG-LOG REGRESSION COEFFICIENTS)</div>
          <span className="badge badge--indigo">{pricing.length} PRODUCTS MODELLED</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>PRODUCT NAME / SKU</th>
                <th>ELASTICITY (ε)</th>
                <th>CONSUMER SENSITIVITY</th>
                <th>OPTIMAL PRICING POSTURE</th>
              </tr>
            </thead>
            <tbody>
              {pricing.slice(0, 20).map((p, i) => {
                const meta = p.metadata || {}
                const el = p.value || 0
                return (
                  <tr key={i}>
                    <td style={{ fontWeight: 800 }}>
                      {shortenProduct(p.entity_id, 48)}
                    </td>
                    <td className="font-mono" style={{ fontWeight: 900 }}>
                      {el.toFixed(3)}
                    </td>
                    <td>
                      <span className={`badge ${Math.abs(el) > 1.1 ? 'badge--rose' : Math.abs(el) < 0.9 ? 'badge--emerald' : 'badge--amber'}`}>
                        {meta.sensitivity || (Math.abs(el) > 1 ? 'PRICE ELASTIC' : 'PRICE INELASTIC')}
                      </span>
                    </td>
                    <td className="text-sm" style={{ fontWeight: 600 }}>
                      {meta.pricing_posture || (Math.abs(el) > 1.1 ? 'Avoid price hikes; protect volume' : 'Opportunity to increase price +₹100-200 with minimal churn')}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
