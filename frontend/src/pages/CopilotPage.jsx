import React from 'react'
import { useLocation } from 'react-router-dom'
import { MessageSquare, Sparkles, Bot, ShieldCheck } from 'lucide-react'
import { useStore } from '../context/StoreContext'
import AICopilot from '../components/ai/AICopilot'

export default function CopilotPage() {
  const location = useLocation()
  const { activeDatasetId, dataset } = useStore()
  const initialPrompt = location.state?.initialPrompt || null

  return (
    <div className="page-container">
      {/* Header Banner */}
      <div className="card mb-md animate-in card-glyph-square" style={{ padding: '18px 24px', background: 'var(--bauhaus-white)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 900, textTransform: 'uppercase' }}>
                CHIEF FASHION COPILOT
              </h2>
              <span className="badge badge--indigo">CONVERSATIONAL AI</span>
              <span className="badge badge--emerald">STORE CONTEXT ACTIVE</span>
            </div>
            <div className="text-xs" style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              REASONING OVER {dataset?.filename || 'STORE DATASET'} • ASK ANYTHING ABOUT CASH LEAKS, SIZES, DISCOUNTS, OR SUPPLIERS
            </div>
          </div>
          <div className="badge badge--amber" style={{ padding: '6px 12px', fontSize: '0.78rem' }}>
            <Sparkles size={14} strokeWidth={2.5} /> REAL-TIME ADVISORY
          </div>
        </div>
      </div>

      {/* Dedicated Full-Height Copilot */}
      <AICopilot datasetId={activeDatasetId} initialPrompt={initialPrompt} />
    </div>
  )
}
