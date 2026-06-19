/**
 * ChatBot — AI Chat Assistant ("Ask ExamLens")
 *
 * Floating chatbot that appears on all authenticated pages.
 * Context-aware: detects analysis_id from the current URL
 * and injects relevant exam data into the AI conversation.
 */

import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'
import {
  Sparkles,
  X,
  Send,
  MessageCircle,
  BookOpen,
  ArrowRight,
  Bot,
  User,
  Zap,
} from 'lucide-react'
import './ChatBot.css'

const SUGGESTED_PROMPTS = [
  { text: 'Which chapters were never tested?', icon: BookOpen },
  { text: 'How has difficulty changed over years?', icon: Zap },
  { text: 'Generate 5 hard practice questions', icon: Sparkles },
  { text: 'Summarize my exam analysis', icon: MessageCircle },
]

export default function ChatBot() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([]) // { role: 'user'|'ai', text: string }
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // Extract analysis_id from URL if on report/predictions/export pages
  const analysisId = extractAnalysisId(location.pathname)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [isOpen])

  // Don't render if not authenticated
  if (!isAuthenticated) return null

  async function handleSend(text) {
    const msg = (text || input).trim()
    if (!msg || loading) return

    // Add user message
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setInput('')
    setLoading(true)

    try {
      const response = await api.post('/chat', {
        message: msg,
        analysis_id: analysisId || null,
      })
      setMessages(prev => [...prev, { role: 'ai', text: response.data.reply }])
    } catch (err) {
      const detail = err.response?.data?.detail || 'Sorry, something went wrong. Please try again.'
      setMessages(prev => [...prev, { role: 'ai', text: `⚠️ ${detail}` }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          className="chatbot-fab"
          onClick={() => setIsOpen(true)}
          title="Ask ExamLens AI"
          id="chatbot-fab"
        >
          <span className="chatbot-fab-pulse" />
          <Sparkles size={24} strokeWidth={1.5} />
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className="chatbot-panel" id="chatbot-panel">
          {/* Header */}
          <div className="chatbot-header">
            <div className="chatbot-header-icon">
              <Bot size={18} strokeWidth={1.5} />
            </div>
            <div className="chatbot-header-info">
              <div className="chatbot-header-title">Ask ExamLens</div>
              <div className="chatbot-header-subtitle">AI-powered exam assistant</div>
            </div>
            <button
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              title="Close chat"
            >
              <X size={18} strokeWidth={1.5} />
            </button>
          </div>

          {/* Context Badge */}
          {analysisId && (
            <div className="chatbot-context">
              <BookOpen size={12} strokeWidth={1.5} />
              <span>Using current analysis as context</span>
            </div>
          )}

          {/* Messages */}
          <div className="chatbot-messages">
            {messages.length === 0 && !loading ? (
              <div className="chatbot-welcome">
                <div className="chatbot-welcome-icon">
                  <Sparkles size={24} strokeWidth={1.5} />
                </div>
                <h3>How can I help?</h3>
                <p>
                  Ask me anything about your exam analyses — chapter coverage,
                  difficulty trends, or practice questions.
                </p>
                <div className="chatbot-suggestions">
                  {SUGGESTED_PROMPTS.map((prompt, i) => (
                    <button
                      key={i}
                      className="chatbot-suggestion"
                      onClick={() => handleSend(prompt.text)}
                    >
                      <prompt.icon size={14} strokeWidth={1.5} />
                      {prompt.text}
                      <ArrowRight size={12} strokeWidth={1.5} style={{ marginLeft: 'auto', opacity: 0.4 }} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`chatbot-msg chatbot-msg-${msg.role === 'user' ? 'user' : 'ai'}`}
                  >
                    <div className="chatbot-msg-avatar">
                      {msg.role === 'user' ? (
                        <User size={14} strokeWidth={2} />
                      ) : (
                        <Bot size={14} strokeWidth={2} />
                      )}
                    </div>
                    <div className="chatbot-msg-bubble">
                      {msg.role === 'ai' ? formatAIText(msg.text) : msg.text}
                    </div>
                  </div>
                ))}

                {/* Typing Indicator */}
                {loading && (
                  <div className="chatbot-typing">
                    <div className="chatbot-msg-avatar" style={{ background: 'var(--color-primary)', color: 'white' }}>
                      <Bot size={14} strokeWidth={2} />
                    </div>
                    <div className="chatbot-typing-dots">
                      <span className="chatbot-typing-dot" />
                      <span className="chatbot-typing-dot" />
                      <span className="chatbot-typing-dot" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="chatbot-input-area">
            <textarea
              ref={inputRef}
              className="chatbot-input"
              placeholder="Ask anything about your exams..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              className="chatbot-send"
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              title="Send message"
            >
              <Send size={18} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      )}
    </>
  )
}

/**
 * Extract analysis_id from the current URL path.
 * Matches /report/:id, /predictions/:id, /export/:id
 */
function extractAnalysisId(pathname) {
  const match = pathname.match(/\/(report|predictions|export|study-plan)\/([a-f0-9-]+)/i)
  return match ? match[2] : null
}

/**
 * Strip any remaining markdown artifacts from AI responses
 * so the chat bubble displays clean, readable plain text.
 */
function formatAIText(text) {
  if (!text) return text
  return text
    // Remove bold markers ** and __
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    // Remove italic markers * and _
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    // Remove heading markers ###, ##, #
    .replace(/^#{1,3}\s+/gm, '')
    // Remove code backticks
    .replace(/```[\s\S]*?```/g, (match) => match.replace(/```/g, ''))
    .replace(/`([^`]+)`/g, '$1')
    // Clean up excessive blank lines
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
