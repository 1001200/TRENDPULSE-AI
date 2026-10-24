import React, { useState, useRef, useEffect } from 'react'
import {
  Send, Sparkles, Bot, User, CornerDownLeft, RotateCcw,
  TrendingDown, Package, Tag, Compass, Users, FileText,
  AlertCircle, ChevronDown, ChevronUp, Copy, Check
} from 'lucide-react'
import { aiAPI } from '../../api/client'
import './AICopilot.css'

const QUICK_PROMPTS = [
  { icon: TrendingDown, text: 'Where am I losing money?', color: '#f43f5e' },
  { icon: Package, text: 'What should I restock right now?', color: '#38bdf8' },
  { icon: Tag, text: 'Which items need a discount or clearance?', color: '#f59e0b' },
  { icon: Compass, text: 'What aesthetic should I drop next?', color: '#a855f7' },
  { icon: Users, text: 'Who are my top customers and how to retain them?', color: '#10b981' },
]

export default function AICopilot({ datasetId, initialPrompt = null }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: `👋 **Welcome to your AI Fashion Copilot!**\n\nI have synthesized your actual sales orders, gross margins, size run stockouts, and TikTok/Instagram aesthetic velocities.\n\nYou can ask me anything about your business in plain English—no complicated dashboards or technical jargon needed.`,
      suggested_followups: [
        'Where am I losing money?',
        'What should I restock right now?',
        'What aesthetic should I drop next?'
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedIndex, setCopiedIndex] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Handle incoming initial prompt trigger (e.g. from ExecutiveMemo buttons)
  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSend(initialPrompt)
    }
  }, [initialPrompt])

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputValue
    if (!textToSend || !textToSend.trim() || loading) return

    const userMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    if (!queryText) setInputValue('')
    setLoading(true)

    try {
      const res = await aiAPI.chat(datasetId, textToSend.trim())
      const data = res.data || {}
      
      const aiResponse = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.answer || "I reviewed your store numbers, but couldn't find a direct answer. Try asking about cash leaks, restocks, or aesthetics!",
        suggested_followups: data.suggested_followups || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, aiResponse])
    } catch (err) {
      console.error('AI chat error:', err)
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'ai',
          text: `⚠️ **Oops! Couldn't reach the AI Advisor.**\n${err.response?.data?.detail || err.message || 'Please verify the backend server is running.'}`,
          suggested_followups: ['Where am I losing money?'],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleReset = () => {
    setMessages([
      {
        id: 'welcome-reset',
        sender: 'ai',
        text: `Conversation reset! What question can I answer about your apparel sales or inventory?`,
        suggested_followups: [
          'Where am I losing money?',
          'What should I restock right now?',
          'Which items need a discount or clearance?'
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ])
  }

  const handleCopyMessage = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  // Format simple markdown into clean HTML preview
  const formatMarkdown = (content) => {
    return content.split('\n').map((line, i) => {
      // Bold text replacement
      let formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Code tags
      formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>')
      // Italic text
      formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>')

      // Bullet points
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return (
          <li key={i} className="chat-bullet" dangerouslySetInnerHTML={{ __html: formatted.replace(/^[•-]\s*/, '') }} />
        )
      }
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={i} className="chat-numbered-line" dangerouslySetInnerHTML={{ __html: formatted }} />
        )
      }
      if (line.trim() === '') {
        return <div key={i} style={{ height: '8px' }} />
      }
      return (
        <p key={i} className="chat-paragraph" dangerouslySetInnerHTML={{ __html: formatted }} />
      )
    })
  }

  return (
    <div className="copilot-card animate-in">
      {/* Top Copilot Bar */}
      <div className="copilot-header">
        <div className="copilot-title-wrap">
          <div className="copilot-avatar">
            <Sparkles size={18} className="copilot-avatar-icon" />
          </div>
          <div>
            <div className="copilot-title">
              Chief Fashion Copilot <span className="badge badge--emerald">ACTIVE</span>
            </div>
            <div className="copilot-desc">ChatGPT-style conversational business intelligence tailored to your clothing brand</div>
          </div>
        </div>
        <button className="btn-copilot-reset" onClick={handleReset} title="Clear & Restart Chat">
          <RotateCcw size={13} /> Reset Chat
        </button>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="quick-prompts-bar">
        <span className="quick-prompts-label">Quick Inquiries:</span>
        <div className="quick-prompts-scroll">
          {QUICK_PROMPTS.map((qp, idx) => {
            const Icon = qp.icon
            return (
              <button
                key={idx}
                className="chip-prompt"
                onClick={() => handleSend(qp.text)}
                disabled={loading}
              >
                <Icon size={12} style={{ color: qp.color }} />
                <span>{qp.text}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Chat Messages Feed */}
      <div className="copilot-feed">
        {messages.map((m, idx) => {
          const isUser = m.sender === 'user'
          const isCopied = copiedIndex === idx

          return (
            <div key={m.id || idx} className={`chat-row ${isUser ? 'chat-row--user' : 'chat-row--ai'}`}>
              <div className="chat-avatar">
                {isUser ? <User size={15} /> : <Bot size={16} className="text-indigo" />}
              </div>

              <div className="chat-bubble-wrap">
                <div className="chat-bubble">
                  {formatMarkdown(m.text)}

                  {!isUser && (
                    <div className="chat-bubble-actions">
                      <button
                        className="btn-chat-action"
                        onClick={() => handleCopyMessage(m.text, idx)}
                        title="Copy text"
                      >
                        {isCopied ? <Check size={12} className="text-emerald" /> : <Copy size={12} />}
                        <span>{isCopied ? 'Copied' : 'Copy'}</span>
                      </button>
                      <span className="chat-timestamp">{m.timestamp}</span>
                    </div>
                  )}
                </div>

                {/* Follow-up Prompts below AI message */}
                {!isUser && m.suggested_followups && m.suggested_followups.length > 0 && (
                  <div className="chat-followups">
                    <span className="text-xs text-muted" style={{ marginRight: 6 }}>Suggested Follow-up:</span>
                    {m.suggested_followups.map((f, fIdx) => (
                      <button
                        key={fIdx}
                        className="chip-followup"
                        onClick={() => handleSend(f)}
                        disabled={loading}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        })}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div className="chat-row chat-row--ai">
            <div className="chat-avatar">
              <Bot size={16} className="text-indigo spin" />
            </div>
            <div className="chat-bubble chat-bubble--typing">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
              <span className="text-xs text-muted">Analyzing your actual sales data &amp; numbers…</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="copilot-input-area">
        <textarea
          ref={inputRef}
          className="copilot-input"
          rows={1}
          placeholder="Ask anything about your store (e.g. 'Where am I bleeding money?', 'What should I reorder?')..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="btn-send-copilot"
          onClick={() => handleSend()}
          disabled={!inputValue.trim() || loading}
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  )
}
