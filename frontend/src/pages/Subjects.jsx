import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  BookOpen,
  FileText,
  TrendingUp,
  Trash2,
  Plus,
  AlertCircle,
  Loader,
  BarChart3,
  ArrowRight,
} from 'lucide-react'
import './Subjects.css'

function getEfsColor(score) {
  if (score === null || score === undefined) return 'var(--color-text-muted)'
  if (score >= 8) return 'var(--color-efs-excellent)'
  if (score >= 6) return 'var(--color-efs-good)'
  if (score >= 4) return 'var(--color-efs-moderate)'
  if (score >= 2) return 'var(--color-efs-poor)'
  return 'var(--color-efs-critical)'
}

function getEfsBadgeClass(label) {
  if (!label) return ''
  const map = {
    excellent: 'badge-excellent',
    good: 'badge-good',
    moderate: 'badge-moderate',
    poor: 'badge-poor',
    critical: 'badge-critical',
  }
  return map[label.toLowerCase()] || ''
}

export default function Subjects() {
  const navigate = useNavigate()
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    fetchSubjects()
  }, [])

  async function fetchSubjects() {
    try {
      const response = await api.get('/subjects')
      setSubjects(response.data.subjects || [])
    } catch (err) {
      setError('Failed to load subjects.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(subjectId, subjectName) {
    if (!confirm(`Delete "${subjectName}" and all its data? This cannot be undone.`)) {
      return
    }

    setDeleting(subjectId)
    try {
      await api.delete(`/subjects/${subjectId}`)
      setSubjects((prev) => prev.filter((s) => s.subject_id !== subjectId))
    } catch (err) {
      setError('Failed to delete subject.')
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="subjects-page">
        <div className="subjects-loading">
          <Loader size={24} className="upload-spinner" color="var(--color-accent)" />
          <span>Loading subjects...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="subjects-page">
      <div className="subjects-header">
        <div>
          <h1 className="text-page-title">My Subjects</h1>
          <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
            Manage your analyzed subjects and view their EFS scores.
          </p>
        </div>
        <button
          className="btn btn-accent"
          onClick={() => navigate('/upload')}
        >
          <Plus size={18} strokeWidth={1.5} />
          New Analysis
        </button>
      </div>

      {error && (
        <div className="auth-error" style={{ marginBottom: 20 }}>
          <AlertCircle size={16} strokeWidth={1.5} />
          <span>{error}</span>
        </div>
      )}

      {subjects.length === 0 ? (
        <div className="subjects-empty card">
          <BookOpen size={48} strokeWidth={1} color="var(--color-text-muted)" />
          <h3>No subjects yet</h3>
          <p>Upload your first exam paper to create a subject and start analyzing.</p>
          <button
            className="btn btn-accent btn-sm"
            onClick={() => navigate('/upload')}
          >
            <Plus size={16} strokeWidth={1.5} />
            Upload Papers
          </button>
        </div>
      ) : (
        <div className="subjects-grid">
          {subjects.map((subject) => (
            <div key={subject.subject_id} className="subjects-card card">
              <div className="subjects-card-header">
                <div className="subjects-card-icon">
                  <BookOpen size={20} strokeWidth={1.5} />
                </div>
                <h3 className="subjects-card-name">{subject.name}</h3>
                <button
                  className="subjects-card-delete"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(subject.subject_id, subject.name)
                  }}
                  disabled={deleting === subject.subject_id}
                  title="Delete subject"
                >
                  {deleting === subject.subject_id ? (
                    <Loader size={14} className="upload-spinner" />
                  ) : (
                    <Trash2 size={14} strokeWidth={1.5} />
                  )}
                </button>
              </div>

              <div className="subjects-card-stats">
                <div className="subjects-card-stat">
                  <FileText size={14} strokeWidth={1.5} />
                  <span>{subject.papers_count} paper{subject.papers_count !== 1 ? 's' : ''}</span>
                </div>

                {subject.latest_efs !== null && subject.latest_efs !== undefined ? (
                  <div className="subjects-card-stat">
                    <BarChart3 size={14} strokeWidth={1.5} color={getEfsColor(subject.latest_efs)} />
                    <span style={{ color: getEfsColor(subject.latest_efs), fontWeight: 600 }}>
                      {subject.latest_efs.toFixed(2)}
                    </span>
                    {subject.latest_label && (
                      <span className={`badge ${getEfsBadgeClass(subject.latest_label)}`}>
                        {subject.latest_label}
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="subjects-card-stat">
                    <TrendingUp size={14} strokeWidth={1.5} color="var(--color-text-muted)" />
                    <span className="text-metadata">Not analyzed</span>
                  </div>
                )}
              </div>

              {subject.last_analyzed && (
                <p className="text-metadata" style={{ marginTop: 8 }}>
                  Last analyzed: {new Date(subject.last_analyzed).toLocaleDateString()}
                </p>
              )}

              {subject.latest_analysis_id && (
                <button
                  className="btn btn-sm btn-accent subjects-card-report"
                  onClick={() => navigate(`/report/${subject.latest_analysis_id}`)}
                >
                  View Report
                  <ArrowRight size={14} strokeWidth={1.5} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
