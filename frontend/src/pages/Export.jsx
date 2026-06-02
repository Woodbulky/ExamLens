import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  FileText,
  FileSpreadsheet,
  Code2,
  PackageOpen,
  Share2,
  ArrowLeft,
  Loader,
  Check,
  Copy,
  Download,
  Clock,
  AlertTriangle,
} from 'lucide-react'
import './Export.css'

const FORMATS = [
  {
    id: 'pdf',
    name: 'PDF Report',
    desc: 'Professional formatted report with tables and EFS breakdown',
    icon: FileText,
    color: '#DC2626',
    bg: '#FEF2F2',
  },
  {
    id: 'csv',
    name: 'CSV Data',
    desc: 'Question classifications spreadsheet — opens in Excel',
    icon: FileSpreadsheet,
    color: '#059669',
    bg: '#D1FAE5',
  },
  {
    id: 'json',
    name: 'JSON Export',
    desc: 'Full analysis data in machine-readable format',
    icon: Code2,
    color: '#4F46E5',
    bg: '#EEF2FF',
  },
  {
    id: 'research_zip',
    name: 'Research Package',
    desc: 'ZIP with methodology note (IEEE format), CSV, JSON & summary',
    icon: PackageOpen,
    color: '#D97706',
    bg: '#FEF3C7',
  },
]

export default function Export() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [exporting, setExporting] = useState(null) // format id
  const [exported, setExported] = useState(new Set())
  const [shareUrl, setShareUrl] = useState('')
  const [sharing, setSharing] = useState(false)
  const [copied, setCopied] = useState(false)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchHistory()
  }, [])

  async function fetchHistory() {
    try {
      const res = await api.get('/export/history')
      setHistory(res.data.history || [])
    } catch (err) {
      // Non-critical
    } finally {
      setLoadingHistory(false)
    }
  }

  async function handleExport(format) {
    setExporting(format)
    setError('')
    try {
      const response = await api.post('/export', {
        analysis_id: analysisId,
        format,
      }, { responseType: 'blob' })

      // Download the file
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // Get filename from Content-Disposition header
      const disposition = response.headers['content-disposition']
      let filename = `ExamLens_export.${format === 'research_zip' ? 'zip' : format}`
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/)
        if (match) filename = match[1]
      }

      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setExported(prev => new Set([...prev, format]))
      fetchHistory() // Refresh history
    } catch (err) {
      setError(`Export failed: ${err.message}`)
    } finally {
      setExporting(null)
    }
  }

  async function handleShare() {
    setSharing(true)
    setError('')
    try {
      const res = await api.post('/export/share', { analysis_id: analysisId })
      const fullUrl = `${window.location.origin}${res.data.share_url}`
      setShareUrl(fullUrl)
    } catch (err) {
      setError('Failed to generate share link.')
    } finally {
      setSharing(false)
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function shareWhatsApp() {
    const text = encodeURIComponent(`Check out my ExamLens analysis report: ${shareUrl}`)
    window.open(`https://wa.me/?text=${text}`, '_blank')
  }

  return (
    <div className="export-page">
      {/* Header */}
      <div className="export-header">
        <button className="report-back" onClick={() => navigate(`/report/${analysisId}`)}>
          <ArrowLeft size={18} strokeWidth={1.5} />
          Back to Report
        </button>
        <div>
          <h1 className="text-page-title">Export & Share</h1>
          <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
            Download your analysis in multiple formats or share it publicly.
          </p>
        </div>
      </div>

      {error && (
        <div className="auth-error" style={{ maxWidth: 680, marginBottom: 20 }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Export Formats */}
      <div className="export-section">
        <h2 className="text-section-heading">Download Formats</h2>
        <div className="export-grid">
          {FORMATS.map((fmt) => {
            const Icon = fmt.icon
            const isExporting = exporting === fmt.id
            const isDone = exported.has(fmt.id)
            return (
              <button
                key={fmt.id}
                className={`export-card card ${isDone ? 'export-card-done' : ''}`}
                onClick={() => handleExport(fmt.id)}
                disabled={isExporting}
              >
                <div className="export-card-icon" style={{ background: fmt.bg, color: fmt.color }}>
                  <Icon size={24} strokeWidth={1.5} />
                </div>
                <div className="export-card-text">
                  <h3>{fmt.name}</h3>
                  <p>{fmt.desc}</p>
                </div>
                <div className="export-card-action">
                  {isExporting ? (
                    <Loader size={18} className="upload-spinner" color="var(--color-accent)" />
                  ) : isDone ? (
                    <Check size={18} color="#059669" />
                  ) : (
                    <Download size={18} color="var(--color-text-muted)" />
                  )}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Share */}
      <div className="export-section card" style={{ padding: 'var(--space-lg)' }}>
        <div className="export-share-header">
          <div className="export-share-icon">
            <Share2 size={20} strokeWidth={1.5} />
          </div>
          <div>
            <h2 className="text-section-heading" style={{ marginBottom: 2 }}>Share Report</h2>
            <p className="text-metadata">Generate a public link anyone can view without logging in.</p>
          </div>
        </div>

        {!shareUrl ? (
          <button
            className="btn btn-accent"
            onClick={handleShare}
            disabled={sharing}
            style={{ marginTop: 'var(--space-md)' }}
          >
            {sharing ? (
              <><Loader size={16} className="upload-spinner" /> Generating...</>
            ) : (
              <><Share2 size={16} strokeWidth={1.5} /> Generate Share Link</>
            )}
          </button>
        ) : (
          <div className="export-share-result">
            <div className="export-share-url">
              <input type="text" value={shareUrl} readOnly className="input" />
              <button className="btn btn-secondary btn-sm" onClick={copyToClipboard}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <div className="export-share-buttons">
              <button className="btn btn-sm" onClick={shareWhatsApp} style={{ background: '#25D366', color: '#fff', border: 'none' }}>
                WhatsApp
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Export History */}
      <div className="export-section">
        <h2 className="text-section-heading">Export History</h2>
        {loadingHistory ? (
          <div className="dashboard-loading">
            <Loader size={18} className="upload-spinner" color="var(--color-accent)" />
            <span>Loading...</span>
          </div>
        ) : history.length === 0 ? (
          <p className="text-metadata">No exports yet. Download a report above to get started.</p>
        ) : (
          <div className="export-history-list">
            {history.map((item, i) => (
              <div key={i} className="export-history-item">
                <div className="export-history-left">
                  <FileText size={16} strokeWidth={1.5} color="var(--color-accent)" />
                  <span className="export-history-name">{item.subject_name || 'Report'}</span>
                  <span className="badge" style={{ background: '#F3F4F6', color: '#6B7280' }}>
                    {item.export_type}
                  </span>
                </div>
                <div className="export-history-right">
                  <Clock size={12} strokeWidth={1.5} />
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
