import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'
import {
  FileText,
  Upload,
  TrendingUp,
  BarChart3,
  ArrowRight,
  Sparkles,
  Loader,
  BookOpen,
  Clock,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

function getEfsColor(score) {
  if (score >= 8.5) return '#059669'
  if (score >= 7) return '#0D9488'
  if (score >= 5) return '#D97706'
  if (score >= 3) return '#EA580C'
  return '#DC2626'
}

export default function Dashboard() {
  const { profile } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)

  const firstName = profile?.display_name?.split(' ')[0] || 'there'

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const [statsRes, recentRes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/dashboard/recent'),
        ])
        setStats(statsRes.data)
        setRecent(recentRes.data.recent || [])
      } catch (err) {
        console.error('Dashboard fetch error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [])

  return (
    <div className="dashboard">
      {/* Welcome Header */}
      <div className="dashboard-welcome">
        <div>
          <h1 className="text-page-title">Welcome back, {firstName} 👋</h1>
          <p className="text-body" style={{ color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Here's an overview of your exam analysis activity.
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="dashboard-stats">
        {[
          {
            icon: FileText,
            label: 'Papers Uploaded',
            value: loading ? '...' : (stats?.papers_uploaded ?? 0),
            color: 'var(--color-primary)',
          },
          {
            icon: BarChart3,
            label: 'Analyses Complete',
            value: loading ? '...' : (stats?.analyses_complete ?? 0),
            color: 'var(--color-accent)',
          },
          {
            icon: TrendingUp,
            label: 'Avg. EFS Score',
            value: loading ? '...' : (stats?.avg_efs_score != null ? stats.avg_efs_score.toFixed(1) : '—'),
            color: stats?.avg_efs_score != null ? getEfsColor(stats.avg_efs_score) : 'var(--color-warning)',
          },
          {
            icon: BookOpen,
            label: 'Subjects',
            value: loading ? '...' : (stats?.subjects_count ?? 0),
            color: '#8B5CF6',
          },
        ].map((stat, i) => (
          <div key={i} className="dashboard-stat-card card">
            <div className="dashboard-stat-icon" style={{ background: `${stat.color}12`, color: stat.color }}>
              <stat.icon size={20} strokeWidth={1.5} />
            </div>
            <div className="dashboard-stat-info">
              <span className="dashboard-stat-value">{stat.value}</span>
              <span className="dashboard-stat-label">{stat.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <h2 className="text-section-heading">Quick Actions</h2>
        <div className="dashboard-actions-grid">
          <button className="dashboard-action-card card" onClick={() => navigate('/upload')}>
            <div className="dashboard-action-icon">
              <Upload size={24} strokeWidth={1.5} />
            </div>
            <div className="dashboard-action-text">
              <h3>New Analysis</h3>
              <p>Upload past papers and get AI insights</p>
            </div>
            <ArrowRight size={18} strokeWidth={1.5} className="dashboard-action-arrow" />
          </button>

          <button className="dashboard-action-card card" onClick={() => navigate('/subjects')}>
            <div className="dashboard-action-icon" style={{ background: 'var(--color-accent-light)', color: 'var(--color-accent)' }}>
              <Sparkles size={24} strokeWidth={1.5} />
            </div>
            <div className="dashboard-action-text">
              <h3>My Subjects</h3>
              <p>View and manage analyzed subjects</p>
            </div>
            <ArrowRight size={18} strokeWidth={1.5} className="dashboard-action-arrow" />
          </button>
        </div>
      </div>

      {/* Recent Analyses */}
      <div className="dashboard-section">
        <h2 className="text-section-heading">Recent Analyses</h2>

        {loading ? (
          <div className="dashboard-loading">
            <Loader size={20} className="upload-spinner" color="var(--color-accent)" />
            <span>Loading...</span>
          </div>
        ) : recent.length === 0 ? (
          <div className="dashboard-empty card">
            <BarChart3 size={40} strokeWidth={1} color="var(--color-text-muted)" />
            <h3>No analyses yet</h3>
            <p>Upload your first exam paper to get started with AI-powered analysis.</p>
            <button className="btn btn-accent btn-sm" onClick={() => navigate('/upload')}>
              <Upload size={16} strokeWidth={1.5} />
              Start First Analysis
            </button>
          </div>
        ) : (
          <div className="dashboard-recent-list">
            {recent.map((item) => (
              <button
                key={item.analysis_id}
                className="dashboard-recent-card card"
                onClick={() => navigate(`/report/${item.analysis_id}`)}
              >
                <div className="dashboard-recent-left">
                  <BookOpen size={18} strokeWidth={1.5} color="var(--color-accent)" />
                  <div className="dashboard-recent-info">
                    <span className="dashboard-recent-name">{item.subject_name}</span>
                    <span className="dashboard-recent-meta">
                      <Clock size={12} strokeWidth={1.5} />
                      {new Date(item.created_at).toLocaleDateString()} · {item.total_questions || 0} questions
                    </span>
                  </div>
                </div>
                <div className="dashboard-recent-right">
                  {item.status === 'done' && item.efs_score != null ? (
                    <div className="dashboard-recent-efs">
                      <span
                        className="dashboard-recent-score"
                        style={{ color: getEfsColor(item.efs_score) }}
                      >
                        {item.efs_score.toFixed(1)}
                      </span>
                      <span className="dashboard-recent-label">{item.efs_label}</span>
                    </div>
                  ) : (
                    <span className={`badge badge-${item.status}`}>
                      {item.status}
                    </span>
                  )}
                  <ArrowRight size={16} strokeWidth={1.5} color="var(--color-text-muted)" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
