import React, { useState } from 'react'
import { TrendingUp, AlertCircle, HelpCircle, ShieldCheck, Info } from 'lucide-react'

export default function SalesForecastChart({ forecastData }) {
  const [hoveredPoint, setHoveredPoint] = useState(null)

  if (!forecastData || !forecastData.sufficient_data) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          background: 'var(--mint-soft)',
          color: 'var(--forest-green)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 0.75rem'
        }}>
          <AlertCircle size={22} />
        </div>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
          Insufficient History for Forecasting
        </h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto' }}>
          {forecastData?.message || 'More consistent sales history is needed to generate a reliable forecast. A minimum of 3 recorded months is required.'}
        </p>
      </div>
    )
  }

  const {
    forecast_period,
    forecasted_revenue,
    forecasted_revenue_formatted,
    interval_low,
    interval_low_formatted,
    interval_high,
    interval_high_formatted,
    model_name,
    evaluation,
    historical_points = [],
    forecast_points = []
  } = forecastData

  // Combined points for plotting
  const allPoints = [
    ...historical_points.map((p, idx) => ({ ...p, type: 'actual', index: idx })),
    ...forecast_points.map((p, idx) => ({ ...p, type: 'forecast', index: historical_points.length + idx }))
  ]

  // Chart dimensions & layout
  const svgWidth = 620
  const svgHeight = 220
  const padLeft = 60
  const padRight = 36
  const padTop = 24
  const padBottom = 38
  const plotWidth = svgWidth - padLeft - padRight
  const plotHeight = svgHeight - padTop - padBottom

  const maxValRaw = Math.max(
    ...historical_points.map(p => p.revenue || 0),
    interval_high || 0,
    forecasted_revenue || 0
  )
  const maxVal = maxValRaw > 0 ? Math.ceil(maxValRaw * 1.18) : 15000

  // 4 Y-axis ticks
  const yTicks = [
    0,
    Math.round(maxVal * 0.33),
    Math.round(maxVal * 0.66),
    maxVal
  ]

  const formatY = (val) => {
    if (val === 0) return '₹0'
    if (val >= 1000) return `₹${(val / 1000).toFixed(1).replace('.0', '')}K`
    return `₹${val}`
  }

  // Calculate coordinates
  const coords = allPoints.map((pt, idx) => {
    const x = padLeft + (idx / Math.max(1, allPoints.length - 1)) * plotWidth
    const y = padTop + plotHeight - ((pt.revenue || 0) / maxVal) * plotHeight
    let lowY = null
    let highY = null
    if (pt.type === 'forecast' && pt.interval_low !== undefined && pt.interval_high !== undefined) {
      lowY = padTop + plotHeight - (pt.interval_low / maxVal) * plotHeight
      highY = padTop + plotHeight - (pt.interval_high / maxVal) * plotHeight
    }
    return { ...pt, x, y, lowY, highY, plotIdx: idx }
  })

  // Historical line path
  const histCoords = coords.filter(c => c.type === 'actual')
  const forecastCoords = coords.filter(c => c.type === 'forecast')

  let histLinePath = ''
  let histAreaPath = ''
  if (histCoords.length > 0) {
    histLinePath = `M ${histCoords[0].x} ${histCoords[0].y}`
    histCoords.slice(1).forEach(pt => {
      histLinePath += ` L ${pt.x} ${pt.y}`
    })

    const yBottom = padTop + plotHeight
    histAreaPath = `M ${histCoords[0].x} ${yBottom} L ${histCoords[0].x} ${histCoords[0].y}`
    histCoords.slice(1).forEach(pt => {
      histAreaPath += ` L ${pt.x} ${pt.y}`
    })
    histAreaPath += ` L ${histCoords[histCoords.length - 1].x} ${yBottom} Z`
  }

  // Forecast dashed segment connecting last historical to forecast point
  let forecastSegmentPath = ''
  if (histCoords.length > 0 && forecastCoords.length > 0) {
    const lastHist = histCoords[histCoords.length - 1]
    const fcPt = forecastCoords[0]
    forecastSegmentPath = `M ${lastHist.x} ${lastHist.y} L ${fcPt.x} ${fcPt.y}`
  }

  const activeCoord = hoveredPoint !== null && coords[hoveredPoint] ? coords[hoveredPoint] : null

  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem', position: 'relative' }}>
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h3 style={{
              fontSize: '1.08rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              Sales Forecast: {forecast_period}
            </h3>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: 'var(--forest-green)',
              background: 'var(--mint-soft)',
              padding: '2px 9px',
              borderRadius: 'var(--radius-pill)'
            }}>
              {model_name}
            </span>
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
            Next calendar month projection derived from {historical_points.length} recorded months.
          </span>
        </div>

        {/* Forecast Metric Badge */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            Projected Revenue
          </div>
          <div style={{
            fontSize: '1.35rem',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            color: 'var(--forest-green)',
            lineHeight: 1.1
          }}>
            {forecasted_revenue_formatted}
          </div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
            80% Range: {interval_low_formatted} – {interval_high_formatted}
          </span>
        </div>
      </div>

      {/* SVG Chart Container */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
          onMouseLeave={() => setHoveredPoint(null)}
        >
          <defs>
            <linearGradient id="forecastActualGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#064E35" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#064E35" stopOpacity="0.01" />
            </linearGradient>
            <linearGradient id="forecastIntervalGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#CADCD2" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#CADCD2" stopOpacity="0.10" />
            </linearGradient>
          </defs>

          {/* Y-Axis Horizontal Grid Lines & Labels */}
          {yTicks.map((val, idx) => {
            const y = padTop + plotHeight - (val / maxVal) * plotHeight
            return (
              <g key={idx}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={padLeft + plotWidth}
                  y2={y}
                  stroke="rgba(18, 38, 28, 0.06)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padLeft - 10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="var(--text-muted)"
                  fontFamily="var(--font-sans)"
                >
                  {formatY(val)}
                </text>
              </g>
            )
          })}

          {/* Historical Area Fill */}
          {histAreaPath && (
            <path d={histAreaPath} fill="url(#forecastActualGradient)" />
          )}

          {/* Historical Actual Line */}
          {histLinePath && (
            <path
              d={histLinePath}
              fill="none"
              stroke="#064E35"
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Forecast Uncertainty Interval Vertical Bar */}
          {forecastCoords.map((pt, idx) => {
            if (pt.lowY !== null && pt.highY !== null) {
              return (
                <g key={`interval-${idx}`}>
                  {/* Vertical error bar */}
                  <line
                    x1={pt.x}
                    y1={pt.highY}
                    x2={pt.x}
                    y2={pt.lowY}
                    stroke="#CADCD2"
                    strokeWidth="12"
                    strokeLinecap="round"
                    opacity="0.75"
                  />
                  {/* Caps */}
                  <line
                    x1={pt.x - 7}
                    y1={pt.highY}
                    x2={pt.x + 7}
                    y2={pt.highY}
                    stroke="#064E35"
                    strokeWidth="2"
                  />
                  <line
                    x1={pt.x - 7}
                    y1={pt.lowY}
                    x2={pt.x + 7}
                    y2={pt.lowY}
                    stroke="#064E35"
                    strokeWidth="2"
                  />
                </g>
              )
            }
            return null
          })}

          {/* Dashed Forecast Connecting Segment */}
          {forecastSegmentPath && (
            <path
              d={forecastSegmentPath}
              fill="none"
              stroke="#064E35"
              strokeWidth="2.4"
              strokeDasharray="5 4"
              strokeLinecap="round"
            />
          )}

          {/* Data Points (Historical dots + Forecast diamond/circle) */}
          {coords.map((pt, idx) => {
            const isHovered = hoveredPoint === idx
            const isForecast = pt.type === 'forecast'
            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredPoint(idx)}
                style={{ cursor: 'pointer' }}
              >
                {/* Larger transparent hover target */}
                <circle cx={pt.x} cy={pt.y} r="18" fill="transparent" />

                {/* Point ring on hover */}
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={isForecast ? "10" : "8"}
                    fill={isForecast ? "rgba(16, 185, 129, 0.25)" : "rgba(6, 78, 53, 0.2)"}
                  />
                )}

                {/* The core dot */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isForecast ? "6" : "4.5"}
                  fill={isForecast ? "#059669" : "var(--forest-green)"}
                  stroke="#ffffff"
                  strokeWidth={isForecast ? "2.5" : "2"}
                />

                {/* X-axis Label below */}
                <text
                  x={pt.x}
                  y={padTop + plotHeight + 20}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={isForecast ? "700" : "500"}
                  fill={isForecast ? "var(--forest-green)" : "var(--text-secondary)"}
                  fontFamily="var(--font-sans)"
                >
                  {typeof pt.month === 'string' ? pt.month.replace(' 2026', '') : (pt.month || '')}
                  {isForecast && '*'}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Floating Interactive Tooltip */}
      {activeCoord && (
        <div style={{
          position: 'absolute',
          top: '3.8rem',
          left: `${Math.min(75, Math.max(15, (activeCoord.x / svgWidth) * 100))}%`,
          transform: 'translateX(-50%)',
          background: '#073B28',
          color: '#ffffff',
          padding: '0.55rem 0.85rem',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          fontSize: '0.75rem',
          pointerEvents: 'none',
          zIndex: 10,
          whiteSpace: 'nowrap'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span>{activeCoord.month}</span>
            {activeCoord.type === 'forecast' ? (
              <span style={{ fontSize: '0.65rem', background: 'var(--mint-soft)', color: 'var(--forest-green)', padding: '1px 6px', borderRadius: '4px', fontWeight: 800 }}>
                FORECAST
              </span>
            ) : (
              <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.2)', padding: '1px 6px', borderRadius: '4px' }}>
                ACTUAL
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>
            {activeCoord.revenue_formatted}
          </div>
          {activeCoord.type === 'forecast' && (
            <div style={{ fontSize: '0.68rem', color: '#CADCD2', marginTop: '2px' }}>
              80% Range: {activeCoord.interval_low_formatted} – {activeCoord.interval_high_formatted}
            </div>
          )}
        </div>
      )}

      {/* Legend & Evaluation Details */}
      <div style={{
        marginTop: '0.85rem',
        paddingTop: '0.85rem',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        fontSize: '0.74rem'
      }}>
        {/* Legend Swatches */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <div style={{ width: '12px', height: '3px', background: 'var(--forest-green)', borderRadius: '2px' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Historical Actuals</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <div style={{ width: '14px', height: '3px', borderTop: '2.5px dashed var(--forest-green)' }} />
            <span style={{ color: 'var(--forest-green)', fontWeight: 600 }}>Forecasted Revenue</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <div style={{ width: '10px', height: '10px', background: '#CADCD2', borderRadius: '2px' }} />
            <span style={{ color: 'var(--text-muted)' }}>80% Prediction Range</span>
          </div>
        </div>

        {/* Backtesting Validation Pill */}
        {evaluation && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            color: 'var(--text-secondary)',
            background: 'var(--bg-canvas)',
            padding: '3px 9px',
            borderRadius: 'var(--radius-pill)',
            fontSize: '0.7rem'
          }}>
            <ShieldCheck size={14} color="var(--forest-green)" />
            <span>
              <strong>Evaluated on {evaluation.holdout_month} holdout:</strong> MAE {evaluation.holdout_mae_formatted} ({evaluation.holdout_wape_pct}% error) vs Naive {evaluation.naive_mae_formatted}
            </span>
          </div>
        )}
      </div>

      {/* Honest Limitation / Disclaimer Note */}
      <div style={{
        marginTop: '0.65rem',
        fontSize: '0.7rem',
        color: 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem'
      }}>
        <Info size={13} style={{ flexShrink: 0 }} />
        <span>
          <strong>Decision-support notice:</strong> Forecasts are mathematical estimates derived from your recorded sales trajectory. They are not guaranteed revenue. Actual performance will depend on drop timing, product curation, and customer demand.
        </span>
      </div>
    </div>
  )
}
