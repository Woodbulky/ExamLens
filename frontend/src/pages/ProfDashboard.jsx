/**
 * ProfDashboard — Professor/Admin Dashboard
 *
 * Shows exam fairness scores, AI improvement suggestions,
 * and comparison against department averages.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'
import {
  GraduationCap,
  BarChart3,
  Loader,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  FileText,
  TrendingUp,
  Lightbulb,
  GitCompare,
  Upload,
  Plus,
} from 'lucide-react'
import './ProfDashboard.css'

function getEfsColor(score) {
  if (score === null || score === undefined) return 'var(--color-text-muted)'
  if (score >= 8) return 'var(--color-efs-excellent)'
  if (score >= 6) return 'var(--color-efs-good)'
  if (score >= 4) return 'var(--color-efs-moderate)'
  if (score >= 2) return 'var(--color-efs-poor)'
  return 'var(--color-efs-critical)'
}

export default function ProfDashboard() {
  const { isProf } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Per-exam expanded states
  const [suggestions, setSuggestions] = useState({}) // { analysisId: string }
  const [sugLoading, setSugLoading] = useState({})
  const [comparisons, setComparisons] = useState({}) // { analysisId: object }
  const [cmpLoading, setCmpLoading] = useState({})

  useEffect(() => {
    if (!isProf) {
      navigate('/dashboard')
      return
    }
    fetchDashboard()
  }, [isProf])

  async function fetchDashboard() {
    try {
      const response = await api.get('/professor/dashboard')
      setData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load professor dashboard.')
    } finally {
      setLoading(false)
    }
  }

  async function handleGetSuggestions(analysisId) {
    if (suggestions[analysisId]) {
      // Toggle off
      setSuggestions(prev => { const copy = { ...prev }; delete copy[analysisId]; return copy })
      return
    }

    setSugLoading(prev => ({ ...prev, [analysisId]: true }))
    try {
      const response = await api.post('/professor/improve', { analysis_id: analysisId })
      setSuggestions(prev => ({ ...prev, [analysisId]: response.data.suggestions }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get suggestions.')
    } finally {
      setSugLoading(prev => ({ ...prev, [analysisId]: false }))
    }
  }

  async function handleCompare(analysisId) {
    if (comparisons[analysisId]) {
      setComparisons(prev => { const copy = { ...prev }; delete copy[analysisId]; return copy })
      return
    }

    setCmpLoading(prev => ({ ...prev, [analysisId]: true }))
    try {
      const response = await api.get(`/professor/compare/${analysisId}`)
      setComparisons(prev => ({ ...prev, [analysisId]: response.data }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load comparison.')
    } finally {
      setCmpLoading(prev => ({ ...prev, [analysisId]: false }))
    }
  }

  function compareClass(current, avg) {
    if (current == null || avg == null) return 'compare-neutral'
    const diff = current - avg
    if (diff > 0.5) return 'compare-better'
    if (diff < -0.5) return 'compare-worse'
    return 'compare-neutral'
  }

  if (loading) {
    return (
      <div className="prof-page">
        <div className="prof-loading">
          <Loader size={24} className="upload-spinner" color="var(--color-accent)" />
          <span>Loading professor dashboard...</span>
        </div>
      </div>
    )
  }

  const stats = data?.stats || {}
  const exams = data?.exams || []

  return (
    <div className="prof-page">
      {/* Header */}
      <div className="prof-header">
        <h1 className="text-page-title">Professor Dashboard</h1>
        <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
          Analyze your exam fairness scores and get AI-powered improvement suggestions.
        </p>
      </div>

      {error && (
        <div className="auth-error" style={{ marginBottom: 20 }}>
          <AlertTriangle size={14} strokeWidth={1.5} />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="prof-stats">
        <div className="prof-stat card">
          <div className="prof-stat-value" style={{ color: 'var(--color-accent)' }}>
            {stats.total_exams || 0}
          </div>
          <div className="prof-stat-label">Exams Analyzed</div>
        </div>
        <div className="prof-stat card">
          <div className="prof-stat-value" style={{ color: stats.avg_efs ? getEfsColor(stats.avg_efs) : 'var(--color-text-muted)' }}>
            {stats.avg_efs ?? '—'}
          </div>
          <div className="prof-stat-label">Avg EFS Score</div>
        </div>
        <div className="prof-stat card">
          <div className="prof-stat-value" style={{ color: 'var(--color-efs-excellent)' }}>
            {stats.best_efs ?? '—'}
          </div>
          <div className="prof-stat-label">Best EFS</div>
        </div>
        <div className="prof-stat card">
          <div className="prof-stat-value" style={{ color: 'var(--color-efs-critical)' }}>
            {stats.worst_efs ?? '—'}
          </div>
          <div className="prof-stat-label">Worst EFS</div>
        </div>
        <div className="prof-stat card">
          <div className="prof-stat-value" style={{ color: 'var(--color-primary)' }}>
            {stats.total_questions || 0}
          </div>
          <div className="prof-stat-label">Total Questions</div>
        </div>
      </div>

      {/* Exams List */}
      <div className="prof-section">
        <div className="prof-section-header">
          <div className="prof-section-icon">
            <FileText size={16} strokeWidth={1.5} />
          </div>
          <h2 className="text-section-heading">Your Exams</h2>
        </div>

        {exams.length === 0 ? (
          <div className="prof-empty card">
            <GraduationCap size={48} strokeWidth={1} color="var(--color-text-muted)" />
            <h3>No exams analyzed yet</h3>
            <p>Upload exam papers to analyze their fairness and get AI improvement suggestions.</p>
            <button className="btn btn-accent btn-sm" onClick={() => navigate('/upload')}>
              <Plus size={16} strokeWidth={1.5} />
              Upload Exam
            </button>
          </div>
        ) : (
          <div className="prof-exams">
            {exams.map((exam) => (
              <div key={exam.analysis_id} className="prof-exam card">
                <div className="prof-exam-top">
                  <span className="prof-exam-name">{exam.subject_name}</span>
                  <div className="prof-exam-meta">
                    <span className="prof-exam-date">
                      {new Date(exam.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Score Chips */}
                <div className="prof-exam-scores">
                  <span className="prof-score-chip chip-efs" style={{ color: getEfsColor(exam.efs_score) }}>
                    EFS: {exam.efs_score?.toFixed(1) ?? '—'}/10
                  </span>
                  <span className="prof-score-chip">TBI: {exam.tbi_score?.toFixed(1) ?? '—'}</span>
                  <span className="prof-score-chip">SCS: {exam.scs_score?.toFixed(1) ?? '—'}</span>
                  <span className="prof-score-chip">RP: {exam.rp_score?.toFixed(1) ?? '—'}</span>
                  <span className="prof-score-chip">{exam.total_questions} Qs</span>
                  {exam.efs_label && (
                    <span className={`badge badge-${exam.efs_label.toLowerCase()}`}>
                      {exam.efs_label}
                    </span>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="prof-exam-actions">
                  <button
                    className="prof-action-btn"
                    onClick={() => navigate(`/report/${exam.analysis_id}`)}
                  >
                    <ArrowRight size={13} strokeWidth={1.5} />
                    View Report
                  </button>
                  <button
                    className="prof-action-btn"
                    onClick={() => handleGetSuggestions(exam.analysis_id)}
                    disabled={sugLoading[exam.analysis_id]}
                  >
                    {sugLoading[exam.analysis_id] ? (
                      <Loader size={13} className="upload-spinner" />
                    ) : (
                      <Lightbulb size={13} strokeWidth={1.5} />
                    )}
                    {suggestions[exam.analysis_id] ? 'Hide Suggestions' : 'AI Suggestions'}
                  </button>
                  <button
                    className="prof-action-btn"
                    onClick={() => handleCompare(exam.analysis_id)}
                    disabled={cmpLoading[exam.analysis_id]}
                  >
                    {cmpLoading[exam.analysis_id] ? (
                      <Loader size={13} className="upload-spinner" />
                    ) : (
                      <GitCompare size={13} strokeWidth={1.5} />
                    )}
                    {comparisons[exam.analysis_id] ? 'Hide Comparison' : 'Compare vs Avg'}
                  </button>
                </div>

                {/* AI Suggestions Panel */}
                {suggestions[exam.analysis_id] && (
                  <div className="prof-suggestions">
                    <div className="prof-suggestions-header">
                      <Sparkles size={14} strokeWidth={1.5} />
                      AI Improvement Suggestions
                    </div>
                    <div className="prof-suggestions-text">
                      {suggestions[exam.analysis_id]}
                    </div>
                  </div>
                )}

                {/* Comparison Panel */}
                {comparisons[exam.analysis_id] && (
                  <div className="prof-compare">
                    {comparisons[exam.analysis_id].message ? (
                      <div className="ai-highlight" style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
                        {comparisons[exam.analysis_id].message}
                      </div>
                    ) : (
                      <div className="prof-compare-grid">
                        {['efs_score', 'tbi_score', 'scs_score', 'rp_score'].map((key) => {
                          const labels = {
                            efs_score: 'EFS',
                            tbi_score: 'TBI',
                            scs_score: 'SCS',
                            rp_score: 'RP',
                          }
                          const current = comparisons[exam.analysis_id].current?.[key]
                          const avg = comparisons[exam.analysis_id].average?.[key]
                          return (
                            <div key={key} className="prof-compare-card card">
                              <div className="prof-compare-label">{labels[key]}</div>
                              <div className="prof-compare-values">
                                <div className="prof-compare-row">
                                  <span>This exam</span>
                                  <span className={compareClass(current, avg)}>
                                    {current?.toFixed(1) ?? '—'}
                                  </span>
                                </div>
                                <div className="prof-compare-row">
                                  <span>Your avg</span>
                                  <span>{avg?.toFixed(1) ?? '—'}</span>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
