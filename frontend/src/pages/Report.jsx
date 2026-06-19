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
  Brain,
  ShieldCheck,
  Copy,
} from 'lucide-react'
import './Report.css'
import { ChapterBarChart, DifficultyDonut, BloomsRadarChart, ConfidenceBadge } from '../components/ReportCharts'

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

const BLOOMS_BADGE_COLORS = {
  Remember: { bg: '#DBEAFE', color: '#2563EB' },
  Understand: { bg: '#D1FAE5', color: '#059669' },
  Apply: { bg: '#EDE9FE', color: '#7C3AED' },
  Analyze: { bg: '#FEF3C7', color: '#D97706' },
  Evaluate: { bg: '#FFEDD5', color: '#EA580C' },
  Create: { bg: '#FCE7F3', color: '#DB2777' },
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
  const hasWeightedEfs = efs.total_weighted != null
  const similarity = report.similarity_data || null
  const hasSimilarPairs = similarity && similarity.similar_pairs && similarity.similar_pairs.length > 0

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

      {/* EFS Score Card + Confidence Badge */}
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
          {/* Mark-Weighted EFS */}
          {hasWeightedEfs && (
            <div className="report-efs-weighted">
              <span className="report-efs-weighted-label">By Marks</span>
              <span
                className="report-efs-weighted-score"
                style={{ color: getEfsColor(efs.total_weighted) }}
              >
                {efs.total_weighted.toFixed(2)}
              </span>
            </div>
          )}
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
          {/* Confidence Badge inline */}
          {report.confidence_distribution && (
            <ConfidenceBadge distribution={report.confidence_distribution} />
          )}
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

      {/* Chapter Breakdown — Interactive Bar Chart */}
      <div className="report-section card">
        <div className="report-section-header">
          <BarChart3 size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">Chapter Breakdown</h2>
        </div>
        <ChapterBarChart chapterStats={report.chapter_stats || []} />
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

      {/* Repeated / Similar Questions */}
      {hasSimilarPairs && (
        <div className="report-section card">
          <div className="report-section-header">
            <Copy size={20} strokeWidth={1.5} color="var(--color-warning)" />
            <h2 className="text-section-heading">
              Repeated Questions
              <span className="report-sim-count">
                {similarity.total_pairs_found} pair{similarity.total_pairs_found !== 1 ? 's' : ''} found
              </span>
            </h2>
            <span className="report-sim-rate-badge">
              QRR: {similarity.repetition_rate}%
            </span>
          </div>
          <p className="report-sim-description">
            Questions with high text similarity across different exam years, detected using TF-IDF analysis.
            A high Question Repetition Rate (QRR) indicates professors may be reusing questions.
          </p>
          <div className="report-sim-pairs">
            {similarity.similar_pairs.map((pair, i) => (
              <div key={i} className="report-sim-card">
                <div className="report-sim-score">
                  <span className="report-sim-pct">{pair.similarity}%</span>
                  <span className="report-sim-label">match</span>
                </div>
                <div className="report-sim-questions">
                  <div className="report-sim-q">
                    <span className="report-sim-year-badge">{pair.q1_year}</span>
                    <span className="report-sim-q-num">Q{pair.q1_number}</span>
                    <span className="report-sim-q-text">
                      {pair.q1_text?.substring(0, 150)}{pair.q1_text?.length > 150 ? '…' : ''}
                    </span>
                  </div>
                  <div className="report-sim-divider" />
                  <div className="report-sim-q">
                    <span className="report-sim-year-badge">{pair.q2_year}</span>
                    <span className="report-sim-q-num">Q{pair.q2_number}</span>
                    <span className="report-sim-q-text">
                      {pair.q2_text?.substring(0, 150)}{pair.q2_text?.length > 150 ? '…' : ''}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Difficulty Distribution — Donut Chart */}
      {report.difficulty_distribution && (
        <div className="report-section card">
          <div className="report-section-header">
            <TrendingUp size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Difficulty Distribution</h2>
          </div>
          <DifficultyDonut distribution={report.difficulty_distribution} />
        </div>
      )}

      {/* Bloom's Taxonomy Analysis */}
      {report.blooms_distribution && Object.values(report.blooms_distribution).some(v => v > 0) && (
        <div className="report-section card">
          <div className="report-section-header">
            <Brain size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Bloom's Taxonomy Analysis</h2>
          </div>
          <p className="report-blooms-subtitle">
            Cognitive level distribution across all exam questions — from basic recall to creative problem solving.
          </p>
          <BloomsRadarChart distribution={report.blooms_distribution} />
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
                <th>Bloom's</th>
                <th>Marks</th>
                <th>Confidence</th>
                <th>Year</th>
              </tr>
            </thead>
            <tbody>
              {(report.questions || []).map((q, i) => {
                const bloomsStyle = BLOOMS_BADGE_COLORS[q.blooms_level] || BLOOMS_BADGE_COLORS.Understand
                return (
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
                      {q.blooms_level ? (
                        <span
                          className="badge"
                          style={{ background: bloomsStyle.bg, color: bloomsStyle.color }}
                        >
                          {q.blooms_level}
                        </span>
                      ) : (
                        <span className="text-metadata">—</span>
                      )}
                    </td>
                    <td>
                      {q.marks ? (
                        <span className="report-q-marks">{q.marks}M</span>
                      ) : (
                        <span className="text-metadata">—</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge badge-conf-${(q.confidence || 'medium').toLowerCase()}`}>
                        {q.confidence}
                      </span>
                    </td>
                    <td>{q.year || '—'}</td>
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
