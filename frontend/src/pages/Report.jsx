import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  BarChart3,
  TrendingUp,
  BookOpen,
  AlertTriangle,
  FileText,
  ArrowLeft,
  Loader,
  Sparkles,
  Target,
  Download,
} from 'lucide-react'
import './Report.css'

function getEfsColor(score) {
  if (score >= 8.5) return '#059669'
  if (score >= 7) return '#0D9488'
  if (score >= 5) return '#D97706'
  if (score >= 3) return '#EA580C'
  return '#DC2626'
}

function getStatusClass(status) {
  const map = {
    'Over-tested': 'status-over',
    'Under-tested': 'status-under',
    'Never tested': 'status-never',
    'Fair': 'status-fair',
  }
  return map[status] || ''
}

export default function Report() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchReport()
  }, [analysisId])

  async function fetchReport() {
    try {
      const response = await api.get(`/analysis/${analysisId}`)
      setReport(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load report.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="report-page">
        <div className="report-loading">
          <Loader size={24} className="upload-spinner" color="var(--color-accent)" />
          <span>Loading report...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="report-page">
        <div className="report-error card">
          <AlertTriangle size={32} color="var(--color-error)" />
          <h3>Error Loading Report</h3>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={() => navigate('/subjects')}>
            <ArrowLeft size={16} /> Back to Subjects
          </button>
        </div>
      </div>
    )
  }

  if (!report) return null

  const efs = report.efs_score || {}
  const maxQuestions = Math.max(...(report.chapter_stats || []).map(c => c.questions_asked), 1)

  return (
    <div className="report-page">
      {/* Header */}
      <div className="report-header">
        <button className="report-back" onClick={() => navigate('/subjects')}>
          <ArrowLeft size={18} strokeWidth={1.5} />
          Back
        </button>
        <div>
          <h1 className="text-page-title">{report.subject_name}</h1>
          <p className="text-metadata">
            {report.years_analyzed?.join(', ')} · {report.questions?.length || 0} questions analyzed
          </p>
        </div>
        <button
          className="btn btn-accent"
          onClick={() => navigate(`/predictions/${analysisId}`)}
          style={{ marginLeft: 'auto' }}
        >
          <Target size={16} strokeWidth={1.5} />
          Predictions
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => navigate(`/export/${analysisId}`)}
        >
          <Download size={16} strokeWidth={1.5} />
          Export
        </button>
      </div>

      {/* EFS Score Card */}
      <div className="report-efs-card card-elevated">
        <div className="report-efs-main">
          <div className="report-efs-score-wrap">
            <span
              className="report-efs-score"
              style={{ color: getEfsColor(efs.total || 0) }}
            >
              {(efs.total || 0).toFixed(2)}
            </span>
            <span className="report-efs-out-of">/10</span>
          </div>
          <span
            className="report-efs-label"
            style={{ color: getEfsColor(efs.total || 0) }}
          >
            {efs.label || 'N/A'}
          </span>
        </div>

        <div className="report-efs-breakdown">
          {[
            { name: 'Topic Bias Index', key: 'tbi_score', abbr: 'TBI', weight: '40%' },
            { name: 'Syllabus Coverage', key: 'scs_score', abbr: 'SCS', weight: '35%' },
            { name: 'Recurrence Penalty', key: 'rp_score', abbr: 'RP', weight: '25%' },
          ].map((comp) => (
            <div key={comp.key} className="report-efs-component">
              <div className="report-efs-component-header">
                <span className="report-efs-component-name">{comp.name}</span>
                <span className="report-efs-component-weight">{comp.weight}</span>
              </div>
              <div className="report-efs-bar-track">
                <div
                  className="report-efs-bar-fill"
                  style={{ width: `${((efs[comp.key] || 0) / 10) * 100}%` }}
                />
              </div>
              <span className="report-efs-component-value">{(efs[comp.key] || 0).toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Summary */}
      {report.ai_summary && (
        <div className="report-section card">
          <div className="report-section-header">
            <Sparkles size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">AI Analysis Summary</h2>
          </div>
          <p className="report-summary-text">{report.ai_summary}</p>
        </div>
      )}

      {/* Chapter Breakdown */}
      <div className="report-section card">
        <div className="report-section-header">
          <BarChart3 size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">Chapter Breakdown</h2>
        </div>
        <div className="report-chapters">
          {(report.chapter_stats || []).map((ch, i) => (
            <div key={i} className="report-chapter-row">
              <div className="report-chapter-info">
                <span className="report-chapter-name">{ch.chapter_name}</span>
                <span className={`report-chapter-status ${getStatusClass(ch.status || 'Fair')}`}>
                  {ch.status || 'Fair'}
                </span>
              </div>
              <div className="report-chapter-bar-area">
                <div className="report-chapter-bar-track">
                  <div
                    className="report-chapter-bar-fill"
                    style={{
                      width: `${(ch.questions_asked / maxQuestions) * 100}%`,
                      background: ch.questions_asked === 0 ? 'var(--color-error)' :
                        ch.bias_score > 1.5 ? 'var(--color-warning)' :
                        ch.bias_score < 0.5 && ch.questions_asked > 0 ? '#F59E0B' :
                        'var(--color-accent)',
                    }}
                  />
                  {/* Expected line */}
                  <div
                    className="report-chapter-expected-line"
                    style={{ left: `${(ch.expected_questions / maxQuestions) * 100}%` }}
                    title={`Expected: ${ch.expected_questions}`}
                  />
                </div>
                <span className="report-chapter-count">{ch.questions_asked}</span>
              </div>
            </div>
          ))}
          <div className="report-chapter-legend">
            <span><span className="report-legend-bar" style={{ background: 'var(--color-accent)' }} /> Actual</span>
            <span><span className="report-legend-line" /> Expected</span>
          </div>
        </div>
      </div>

      {/* Never Tested */}
      {report.never_tested?.length > 0 && (
        <div className="report-section card">
          <div className="report-section-header">
            <AlertTriangle size={20} strokeWidth={1.5} color="var(--color-warning)" />
            <h2 className="text-section-heading">Never Tested Topics</h2>
          </div>
          <div className="report-never-tested">
            {report.never_tested.map((topic, i) => (
              <span key={i} className="report-never-tag">{topic}</span>
            ))}
          </div>
        </div>
      )}

      {/* Difficulty Distribution */}
      {report.difficulty_distribution && (
        <div className="report-section card">
          <div className="report-section-header">
            <TrendingUp size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Difficulty Distribution</h2>
          </div>
          <div className="report-difficulty">
            {['Easy', 'Medium', 'Hard'].map((level) => {
              const count = report.difficulty_distribution[level] || 0
              const total = Object.values(report.difficulty_distribution).reduce((a, b) => a + b, 0)
              const pct = total > 0 ? Math.round((count / total) * 100) : 0
              return (
                <div key={level} className="report-diff-item">
                  <div className="report-diff-header">
                    <span className="report-diff-label">{level}</span>
                    <span className="report-diff-value">{count} ({pct}%)</span>
                  </div>
                  <div className="report-diff-bar-track">
                    <div
                      className={`report-diff-bar-fill report-diff-${level.toLowerCase()}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Questions Table */}
      <div className="report-section card">
        <div className="report-section-header">
          <FileText size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">
            Question Classifications ({report.questions?.length || 0})
          </h2>
        </div>
        <div className="report-questions-table-wrap">
          <table className="report-questions-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Question</th>
                <th>Chapter</th>
                <th>Difficulty</th>
                <th>Confidence</th>
                <th>Year</th>
              </tr>
            </thead>
            <tbody>
              {(report.questions || []).map((q, i) => (
                <tr key={i}>
                  <td>{q.question_number}</td>
                  <td className="report-q-text" title={q.question_text}>
                    {q.question_text?.substring(0, 120)}{q.question_text?.length > 120 ? '...' : ''}
                  </td>
                  <td><span className="report-q-chapter">{q.assigned_chapter}</span></td>
                  <td>
                    <span className={`badge badge-${(q.difficulty || 'medium').toLowerCase()}`}>
                      {q.difficulty}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-conf-${(q.confidence || 'medium').toLowerCase()}`}>
                      {q.confidence}
                    </span>
                  </td>
                  <td>{q.year || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
