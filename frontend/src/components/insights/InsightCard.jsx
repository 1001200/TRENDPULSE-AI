import React, { useState } from 'react'
import { ChevronDown, Zap } from 'lucide-react'

/**
 * InsightCard — Renders a single Core Question's insight.
 * 
 * Props:
 *   questionNumber: 1-5
 *   question: string
 *   icon: React component
 *   keyTakeaway: string
 *   metrics: Array of { label, value }
 *   action: { what, why, expected_impact }
 *   children: optional expanded detail content
 */
export default function InsightCard({
  questionNumber,
  question,
  icon: Icon,
  keyTakeaway,
  metrics = [],
  action,
  children,
  className = '',
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={`insight-card stagger-${questionNumber} ${className}`}
      data-question={questionNumber}
    >
      {/* Header */}
      <div className="insight-card-header">
        <div className="insight-icon-box">
          {Icon && <Icon size={22} />}
        </div>
        <div>
          <div className="insight-question-label">Question {questionNumber}</div>
          <h3 className="insight-question-title">{question}</h3>
        </div>
      </div>

      {/* Key Takeaway */}
      <p className="insight-takeaway">{keyTakeaway}</p>

      {/* Metrics Grid */}
      {metrics.length > 0 && (
        <div className="insight-metrics-grid">
          {metrics.map((m, i) => (
            <div key={i} className="metric-tile">
              <span className="metric-tile-label">{m.label}</span>
              <span className={`metric-tile-value ${String(m.value).length > 8 ? 'small' : ''}`}>
                {m.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Action Recommendation */}
      {action && action.what && (
        <div className="insight-action">
          <div className="action-icon">
            <Zap size={14} />
          </div>
          <div className="action-content">
            <span className="action-label">Recommended Action</span>
            <span className="action-text">{action.what}</span>
            {action.why && <span className="action-rationale">{action.why}</span>}
          </div>
        </div>
      )}

      {/* Expandable Details */}
      {children && (
        <>
          <div className={`insight-details ${expanded ? 'expanded' : ''}`}>
            {children}
          </div>
          <button
            className={`insight-toggle ${expanded ? 'expanded' : ''}`}
            onClick={() => setExpanded(!expanded)}
          >
            <span>{expanded ? 'Hide Details' : 'Show Details'}</span>
            <ChevronDown size={14} />
          </button>
        </>
      )}
    </div>
  )
}
