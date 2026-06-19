/**
 * StudyPlan — AI-powered day-by-day study schedule
 *
 * User inputs exam date and daily study hours,
 * the AI generates a structured study plan prioritizing
 * high-confidence predicted topics.
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Loader,
  Sparkles,
  AlertTriangle,
  BookOpen,
  Target,
  Lightbulb,
  Layers,
  CheckCircle2,
  Download,
  Check,
} from 'lucide-react'
import './StudyPlan.css'

export default function StudyPlan() {
  const { analysisId } = useParams()
  const navigate = useNavigate()

  // Form state
  const [examDate, setExamDate] = useState('')
  const [hoursPerDay, setHoursPerDay] = useState(4)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  // Calculate days until exam
  const daysUntil = examDate
    ? Math.max(0, Math.ceil((new Date(examDate) - new Date()) / (1000 * 60 * 60 * 24)))
    : 0

  async function handleGenerate(e) {
    e.preventDefault()
    setError('')

    if (!examDate) {
      setError('Please select your exam date.')
      return
    }
    if (daysUntil < 1) {
      setError('Exam date must be in the future.')
      return
    }
    if (hoursPerDay < 0.5 || hoursPerDay > 16) {
      setError('Hours per day must be between 0.5 and 16.')
      return
    }

    setGenerating(true)
    try {
      const response = await api.post(`/analysis/${analysisId}/study-plan`, {
        exam_date: examDate,
        hours_per_day: parseFloat(hoursPerDay),
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate study plan.')
    } finally {
      setGenerating(false)
    }
  }

  const plan = result?.plan

  async function handleDownloadPDF() {
    if (!result) return
    setDownloading(true)
    try {
      const response = await api.post('/export/study-plan', {
        analysis_id: analysisId,
        subject_name: result.subject_name,
        exam_date: result.exam_date,
        days_until: result.days_until,
        hours_per_day: result.hours_per_day,
        plan: result.plan,
      }, { responseType: 'blob' })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      const disposition = response.headers['content-disposition']
      let filename = `ExamLens_StudyPlan.pdf`
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/)
        if (match) filename = match[1]
      }

      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setDownloaded(true)
      setTimeout(() => setDownloaded(false), 3000)
    } catch (err) {
      setError('Failed to download study plan PDF.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="studyplan-page">
      {/* Header */}
      <div className="studyplan-header">
        <button className="report-back" onClick={() => navigate(`/predictions/${analysisId}`)}>
          <ArrowLeft size={18} strokeWidth={1.5} />
          Back to Predictions
        </button>
        <div>
          <h1 className="text-page-title">AI Study Planner</h1>
          <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
            Generate a personalized study schedule based on exam predictions.
          </p>
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleGenerate} className="studyplan-form card">
        <div className="studyplan-field">
          <label htmlFor="exam-date">
            <Calendar size={13} strokeWidth={1.5} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Exam Date
          </label>
          <input
            id="exam-date"
            type="date"
            value={examDate}
            onChange={(e) => setExamDate(e.target.value)}
            min={new Date(Date.now() + 86400000).toISOString().split('T')[0]}
            max={new Date(Date.now() + 120 * 86400000).toISOString().split('T')[0]}
          />
        </div>

        <div className="studyplan-field">
          <label htmlFor="hours-per-day">
            <Clock size={13} strokeWidth={1.5} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Hours / Day
          </label>
          <input
            id="hours-per-day"
            type="number"
            value={hoursPerDay}
            onChange={(e) => setHoursPerDay(e.target.value)}
            min="0.5"
            max="16"
            step="0.5"
            style={{ width: 100 }}
          />
        </div>

        {daysUntil > 0 && (
          <div className="studyplan-days-preview">
            <Target size={14} strokeWidth={1.5} />
            {daysUntil} days · {Math.round(daysUntil * hoursPerDay)} total hours
          </div>
        )}

        <button
          type="submit"
          className="btn btn-accent"
          disabled={generating || !examDate}
        >
          {generating ? (
            <>
              <Loader size={16} className="upload-spinner" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles size={16} strokeWidth={1.5} />
              Generate Study Plan
            </>
          )}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="auth-error" style={{ marginBottom: 20 }}>
          <AlertTriangle size={14} strokeWidth={1.5} />
          <span>{error}</span>
        </div>
      )}

      {/* Generating State */}
      {generating && !result && (
        <div className="studyplan-generating card">
          <div className="studyplan-generating-icon">
            <Loader size={24} className="upload-spinner" />
          </div>
          <h3>Creating your study plan...</h3>
          <p>
            AI is analyzing your predictions and building a day-by-day schedule.
            This may take a moment.
          </p>
        </div>
      )}

      {/* Results */}
      {plan && (
        <>
          {/* Overview Stats */}
          <div className="studyplan-overview">
            <div className="studyplan-stat card">
              <div className="studyplan-stat-value">{result.subject_name}</div>
              <div className="studyplan-stat-label">Subject</div>
            </div>
            <div className="studyplan-stat card">
              <div className="studyplan-stat-value">{plan.total_days || daysUntil}</div>
              <div className="studyplan-stat-label">Study Days</div>
            </div>
            <div className="studyplan-stat card">
              <div className="studyplan-stat-value">{plan.total_hours || Math.round(daysUntil * hoursPerDay)}</div>
              <div className="studyplan-stat-label">Total Hours</div>
            </div>
            <div className="studyplan-stat card">
              <div className="studyplan-stat-value">{result.days_until}</div>
              <div className="studyplan-stat-label">Days to Exam</div>
            </div>
          </div>

          {/* Download PDF Button */}
          <div className="studyplan-download">
            <button
              className={`btn ${downloaded ? 'btn-success' : 'btn-accent'}`}
              onClick={handleDownloadPDF}
              disabled={downloading}
            >
              {downloading ? (
                <><Loader size={16} className="upload-spinner" /> Preparing PDF...</>
              ) : downloaded ? (
                <><Check size={16} /> Downloaded!</>
              ) : (
                <><Download size={16} strokeWidth={1.5} /> Download Study Plan PDF</>
              )}
            </button>
          </div>

          {/* Phases */}
          {(plan.phases || []).map((phase, pi) => (
            <div key={pi} className="studyplan-phase">
              <div className="studyplan-phase-header">
                <div className="studyplan-phase-icon">
                  <Layers size={16} strokeWidth={1.5} />
                </div>
                <span className="studyplan-phase-name">{phase.phase_name || `Phase ${pi + 1}`}</span>
              </div>

              <div className="studyplan-days">
                {(phase.days || []).map((day, di) => {
                  const priority = (day.priority || 'Medium').toLowerCase()
                  return (
                    <div key={di} className="studyplan-day card">
                      <div className={`studyplan-day-num priority-${priority}`}>
                        D{day.day || di + 1}
                      </div>
                      <div className="studyplan-day-content">
                        <div className="studyplan-day-top">
                          <span className="studyplan-day-focus">{day.focus}</span>
                          <div className="studyplan-day-meta">
                            {day.date && (
                              <span className="studyplan-day-date">
                                {new Date(day.date + 'T00:00:00').toLocaleDateString('en-US', {
                                  weekday: 'short',
                                  month: 'short',
                                  day: 'numeric',
                                })}
                              </span>
                            )}
                            <span className="studyplan-day-hours">{day.hours}h</span>
                          </div>
                        </div>
                        {day.tasks && day.tasks.length > 0 && (
                          <div className="studyplan-day-tasks">
                            {day.tasks.map((task, ti) => (
                              <span key={ti} className="studyplan-task-chip">
                                {task}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}

          {/* Tips */}
          {plan.tips && plan.tips.length > 0 && (
            <div className="studyplan-tips card">
              <div className="studyplan-tips-header">
                <Lightbulb size={18} strokeWidth={1.5} color="var(--color-accent)" />
                Study Tips
              </div>
              <div className="studyplan-tips-list">
                {plan.tips.map((tip, i) => (
                  <div key={i} className="studyplan-tip">
                    <span className="studyplan-tip-bullet" />
                    <span>{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
