import React, { useState } from 'react'
import {
  AlertOctagon, CheckCircle2, Zap, Copy, Check, TrendingUp,
  ArrowRight, ShieldAlert, Sparkles, MessageSquare, DollarSign,
  PackageCheck, HelpCircle
} from 'lucide-react'
import { formatCurrency, formatPercent, formatNumber } from '../../utils/formatters'
import './ExecutiveMemo.css'

export default function ExecutiveMemo({ diagnosis, loading, onAskCopilot }) {
  const [copiedId, setCopiedId] = useState(null)

  if (loading) {
    return (
      <div className="memo-container memo-loading animate-in">
        <div className="memo-pulse-badge">
          <Sparkles size={16} className="spin text-indigo" />
          <span>Synthesizing Executive Store Diagnosis…</span>
        </div>
        <div className="memo-skeleton-grid">
          <div className="memo-skeleton-card" />
          <div className="memo-skeleton-card" />
          <div className="memo-skeleton-card" />
        </div>
      </div>
    )
  }

  if (!diagnosis) {
    return null
  }

  const { headline, where_you_are_lacking, where_you_are_winning, your_three_moves_this_week, copy_actions } = diagnosis

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2500)
  }

  return (
    <div className="memo-container animate-in">
      {/* Header Bar */}
      <div className="memo-header">
        <div className="memo-header-left">
          <div className="memo-ai-badge">
            <span className="pulsing-dot" />
            <span>CHIEF FASHION ADVISOR • 60-SEC EXECUTIVE MEMO</span>
          </div>
          <h2 className="memo-title">Instant Merchant Health Diagnosis</h2>
          <p className="memo-subtitle">
            Plain-English commercial briefing on where your clothing brand is bleeding money, where you are winning, and your immediate action plan.
          </p>
        </div>

        {headline && (
          <div className="memo-quick-stats">
            <div className="stat-pill">
              <span className="stat-label">Gross Revenue</span>
              <span className="stat-value text-indigo">{formatCurrency(headline.total_revenue)}</span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Store Margin</span>
              <span className="stat-value text-emerald">{formatPercent(headline.margin_percentage)}</span>
            </div>
            {headline.discount_bleed > 0 && (
              <div className="stat-pill stat-pill--danger">
                <span className="stat-label">Discount Bleed</span>
                <span className="stat-value text-rose">-₹{Number(headline.discount_bleed).toLocaleString('en-IN')}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Grid: Cash Leaks vs Big Wins */}
      <div className="memo-grid-2">
        {/* 1. Cash Leaks & Where You Are Lacking */}
        <div className="memo-column memo-column--leaks">
          <div className="column-header">
            <div className="column-title text-rose">
              <ShieldAlert size={20} /> Where Your Business Is Lacking &amp; Bleeding Cash
            </div>
            <span className="badge badge--rose">Action Required</span>
          </div>

          <div className="leak-cards-list">
            {(where_you_are_lacking || []).map((leak, idx) => (
              <div key={idx} className="leak-card">
                <div className="leak-top">
                  <div className="leak-title-wrap">
                    <span className="leak-number">#{idx + 1}</span>
                    <strong className="leak-title">{leak.title}</strong>
                  </div>
                  {leak.impact && (
                    <span className={`leak-impact ${leak.severity === 'high' ? 'leak-impact--high' : ''}`}>
                      {leak.impact}
                    </span>
                  )}
                </div>
                <p className="leak-desc">{leak.description}</p>
                <div className="leak-footer">
                  <span className="leak-tag">{leak.tag || 'Cash Leak'}</span>
                  {onAskCopilot && (
                    <button
                      className="btn-link-ask"
                      onClick={() => onAskCopilot(`How do I fix: ${leak.title}?`)}
                    >
                      <MessageSquare size={13} /> Ask Copilot How to Fix <ArrowRight size={12} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 2. Where You Are Winning */}
        <div className="memo-column memo-column--wins">
          <div className="column-header">
            <div className="column-title text-emerald">
              <TrendingUp size={20} /> Where You Are Winning (Profit Drivers)
            </div>
            <span className="badge badge--emerald">Growth Engines</span>
          </div>

          <div className="win-cards-list">
            {(where_you_are_winning || []).map((win, idx) => (
              <div key={idx} className="win-card">
                <div className="win-top">
                  <strong className="win-title">{win.title}</strong>
                  {win.stat && <span className="win-stat-badge">{win.stat}</span>}
                </div>
                <p className="win-desc">{win.description}</p>
                <div className="win-footer">
                  <span className="badge badge--emerald">Scale This</span>
                  {onAskCopilot && (
                    <button
                      className="btn-link-ask text-emerald"
                      onClick={() => onAskCopilot(`Tell me more about our winning trend: ${win.title}`)}
                    >
                      <Sparkles size={13} /> Scale With AI <ArrowRight size={12} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. This Week's 3-Step Playbook */}
      <div className="memo-playbook-section">
        <div className="playbook-header">
          <div className="playbook-title">
            <Zap size={20} className="text-amber" />
            <span>This Week’s 3-Step Action Playbook</span>
          </div>
          <span className="text-xs text-muted">Prioritized for maximum profit impact</span>
        </div>

        <div className="playbook-steps-grid">
          {(your_three_moves_this_week || []).map((move, idx) => (
            <div key={idx} className="playbook-step-card">
              <div className="step-badge">STEP {move.step || idx + 1}</div>
              <h4 className="step-action">{move.action}</h4>
              <p className="step-details">{move.details}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Stress-Free Merchant Workflows: 1-Click Copy Drafts */}
      {copy_actions && copy_actions.length > 0 && (
        <div className="memo-actions-hub">
          <div className="actions-hub-header">
            <div className="actions-hub-title">
              <PackageCheck size={19} className="text-indigo" />
              <span>Stress-Free Merchant Workflows (1-Click Ready Drafts)</span>
            </div>
            <span className="text-xs text-muted">Copy and send directly to your team, suppliers, or WhatsApp broadcast</span>
          </div>

          <div className="copy-cards-grid">
            {copy_actions.map((act) => {
              const isCopied = copiedId === act.id
              return (
                <div key={act.id} className="copy-card">
                  <div className="copy-card-top">
                    <div>
                      <span className="copy-badge">{act.badge}</span>
                      <h4 className="copy-card-title">{act.title}</h4>
                      <p className="copy-card-subtitle">{act.subtitle}</p>
                    </div>
                    <button
                      className={`btn-copy ${isCopied ? 'btn-copied' : ''}`}
                      onClick={() => handleCopy(act.text_to_copy, act.id)}
                      title="Copy to clipboard"
                    >
                      {isCopied ? (
                        <>
                          <Check size={14} /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy size={14} /> Copy Draft
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="copy-preview-box">{act.text_to_copy}</pre>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
