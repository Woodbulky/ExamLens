import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  TrendingUp,
  ArrowLeft,
  Loader,
  AlertTriangle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Target,
  Zap,
  HelpCircle,
  XCircle,
} from 'lucide-react'
import './Predictions.css'

const labelConfig = {
  'Very Likely': { color: '#059669', bg: '#D1FAE5', icon: Zap },
  'Likely': { color: '#0D9488', bg: '#CCFBF1', icon: Target },
  'Possible': { color: '#D97706', bg: '#FEF3C7', icon: HelpCircle },
  'Unlikely': { color: '#9CA3AF', bg: '#F3F4F6', icon: XCircle },
}

export default function Predictions() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [practiceQuestions, setPracticeQuestions] = useState(null)
  const [generatingPQ, setGeneratingPQ] = useState(false)
  const [showPQ, setShowPQ] = useState(false)

  useEffect(() => {
    fetchPredictions()
  }, [analysisId])

  async function fetchPredictions() {
    try {
      const response = await api.get(`/analysis/${analysisId}/predictions`)
      setData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load predictions.')
    } finally {
      setLoading(false)
    }
  }

  async function handleGeneratePractice() {
    setGeneratingPQ(true)
    try {
      const response = await api.post(`/analysis/${analysisId}/practice-questions`)
      setPracticeQuestions(response.data.questions || [])
      setShowPQ(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate practice questions.')
    } finally {
      setGeneratingPQ(false)
    }
  }

  if (loading) {
    return (
      <div className="predictions-page">
        <div className="predictions-loading">
          <Loader size={24} className="upload-spinner" color="var(--color-accent)" />
          <span>Loading predictions...</span>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="predictions-page">
        <div className="report-error card">
          <AlertTriangle size={32} color="var(--color-error)" />
          <h3>Error</h3>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} /> Go Back
          </button>
        </div>
      </div>
    )
  }

  const predictions = data?.predictions || []
  const trendData = data?.trend_data || { years: [], chapters: [] }

  return (
    <div className="predictions-page">
      {/* Header */}
      <div className="predictions-header">
        <button className="report-back" onClick={() => navigate(`/report/${analysisId}`)}>
          <ArrowLeft size={18} strokeWidth={1.5} />
          Back to Report
        </button>
        <div>
          <h1 className="text-page-title">Topic Predictions</h1>
          <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
            AI-predicted topics based on historical exam patterns.
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="predictions-disclaimer">
        <AlertTriangle size={14} strokeWidth={1.5} />
        <span>
          Predictions are based on historical patterns and are not guarantees.
          Use as a study guide alongside full syllabus preparation.
        </span>
      </div>

      {/* Prediction Cards */}
      <div className="predictions-section">
        <h2 className="text-section-heading">Ranked Topics</h2>
        <div className="predictions-list">
          {predictions.map((pred) => {
            const config = labelConfig[pred.label] || labelConfig['Possible']
            const IconComp = config.icon
            return (
              <div key={pred.rank} className="prediction-card card">
                <div className="prediction-rank">#{pred.rank}</div>
                <div className="prediction-main">
                  <div className="prediction-header">
                    <h3 className="prediction-chapter">{pred.chapter_name}</h3>
                    <span
                      className="prediction-label"
                      style={{ background: config.bg, color: config.color }}
                    >
                      <IconComp size={12} strokeWidth={2} />
                      {pred.label}
                    </span>
                  </div>
                  <div className="prediction-bar-row">
                    <div className="prediction-bar-track">
                      <div
                        className="prediction-bar-fill"
                        style={{
                          width: `${pred.confidence * 100}%`,
                          background: config.color,
                        }}
                      />
                    </div>
                    <span className="prediction-confidence">{Math.round(pred.confidence * 100)}%</span>
                  </div>
                  <div className="prediction-meta">
                    <span>{pred.total_questions} questions total</span>
                    <span>·</span>
                    <span>{pred.avg_questions_per_year}/yr avg</span>
                    <span>·</span>
                    <span>Appeared in {pred.appearance_rate}% of years</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Year-on-Year Trend */}
      {trendData.years.length > 0 && trendData.chapters.length > 0 && (
        <div className="predictions-section card" style={{ padding: 'var(--space-lg)' }}>
          <div className="report-section-header" style={{ marginBottom: 'var(--space-lg)' }}>
            <TrendingUp size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Year-on-Year Trends</h2>
          </div>
          <div className="trend-table-wrap">
            <table className="trend-table">
              <thead>
                <tr>
                  <th>Chapter</th>
                  {trendData.years.map((y) => (
                    <th key={y}>{y}</th>
                  ))}
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {trendData.chapters.map((ch, i) => (
                  <tr key={i}>
                    <td className="trend-chapter-name">{ch.chapter_name}</td>
                    {ch.counts.map((count, j) => (
                      <td key={j}>
                        <span className={`trend-cell ${count === 0 ? 'trend-zero' : ''}`}>
                          {count}
                        </span>
                      </td>
                    ))}
                    <td>
                      <span className="trend-total">{ch.counts.reduce((a, b) => a + b, 0)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Practice Questions */}
      <div className="predictions-section">
        <div className="predictions-practice-header">
          <h2 className="text-section-heading">Practice Questions</h2>
          <button
            className="btn btn-accent"
            onClick={handleGeneratePractice}
            disabled={generatingPQ}
          >
            {generatingPQ ? (
              <>
                <Loader size={16} className="upload-spinner" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={16} strokeWidth={1.5} />
                {practiceQuestions ? 'Regenerate' : 'Generate Practice Questions'}
              </>
            )}
          </button>
        </div>

        {error && practiceQuestions === null && (
          <div className="auth-error" style={{ marginTop: 12 }}>
            <AlertTriangle size={14} /> {error}
          </div>
        )}

        {showPQ && practiceQuestions && (
          <div className="practice-questions-list">
            {practiceQuestions.map((pq, i) => (
              <div key={i} className="practice-question card">
                <div className="pq-header">
                  <span className="pq-number">Q{i + 1}</span>
                  <div className="pq-badges">
                    <span className={`badge badge-${(pq.difficulty || 'medium').toLowerCase()}`}>
                      {pq.difficulty}
                    </span>
                    <span className="badge" style={{ background: '#EEF2FF', color: '#4F46E5' }}>
                      {pq.marks || '?'} marks
                    </span>
                    <span className="badge" style={{ background: '#F3F4F6', color: '#6B7280' }}>
                      {pq.type || 'Theory'}
                    </span>
                  </div>
                </div>
                <p className="pq-text">{pq.question}</p>
                <p className="pq-chapter">{pq.chapter}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
