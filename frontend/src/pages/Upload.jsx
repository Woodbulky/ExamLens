import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import {
  Upload as UploadIcon,
  FileText,
  X,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  ArrowRight,
  Loader,
} from 'lucide-react'
import './Upload.css'

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

export default function Upload() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  // Form state
  const [subjectName, setSubjectName] = useState('')
  const [chapters, setChapters] = useState('')
  const [files, setFiles] = useState([]) // { file, year }
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear())

  // UI state
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [success, setSuccess] = useState(null)

  // Validate a file before adding
  function validateFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are accepted.'
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Max is 20MB.`
    }
    if (file.size === 0) {
      return 'File is empty.'
    }
    return null
  }

  // Add files from input or drop
  function addFiles(newFiles) {
    setError('')
    const toAdd = []

    for (const f of newFiles) {
      const err = validateFile(f)
      if (err) {
        setError(err)
        return
      }
      // Check for duplicates
      if (files.some((existing) => existing.file.name === f.name)) {
        setError(`"${f.name}" is already added.`)
        return
      }
      toAdd.push({ file: f, year: currentYear })
    }

    setFiles((prev) => [...prev, ...toAdd])
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  function updateYear(index, year) {
    setFiles((prev) =>
      prev.map((f, i) => (i === index ? { ...f, year: parseInt(year) || 0 } : f))
    )
  }

  // Drag & Drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [files, currentYear])

  // Submit all uploads
  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!subjectName.trim()) {
      setError('Please enter a subject name.')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }
    if (!chapters.trim()) {
      setError('Please enter at least one syllabus chapter (one per line).')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }
    if (files.length === 0) {
      setError('Please add at least one PDF file.')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      // Parse chapters into array
      const chapterList = chapters
        .split('\n')
        .map((c) => c.trim())
        .filter((c) => c.length > 0)

      if (chapterList.length === 0) {
        setError('Please enter at least one syllabus chapter.')
        setUploading(false)
        return
      }

      // Upload first file with subject_id = "new" to create the subject
      let subjectId = null
      const uploadIds = []

      for (let i = 0; i < files.length; i++) {
        const { file, year } = files[i]
        const formData = new FormData()
        formData.append('file', file)
        formData.append('year', year.toString())

        if (i === 0) {
          formData.append('subject_id', 'new')
          formData.append('subject_name', subjectName.trim())
        } else {
          formData.append('subject_id', subjectId)
        }

        const response = await api.post('/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        uploadIds.push(response.data.upload_id)

        if (i === 0) {
          subjectId = response.data.subject_id

          // Save syllabus chapters
          for (const chapterName of chapterList) {
            await api.post('/syllabus', {
              subject_id: subjectId,
              chapter_name: chapterName,
            }).catch(() => {
              console.warn(`Failed to save chapter: ${chapterName}`)
            })
          }
        }

        setUploadProgress(Math.round(((i + 1) / files.length) * 50))
      }

      // === Trigger AI Analysis Pipeline ===
      setUploadProgress(60)

      const analyzeResponse = await api.post('/analyze', {
        upload_ids: uploadIds,
        subject_id: subjectId,
      })

      setUploadProgress(100)

      setSuccess({
        subjectId,
        subjectName: subjectName.trim(),
        filesCount: files.length,
        chaptersCount: chapterList.length,
        analysisId: analyzeResponse.data.analysis_id,
        efsScore: analyzeResponse.data.efs_score,
        efsLabel: analyzeResponse.data.efs_label,
      })

    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Upload failed.'
      setError(detail)
    } finally {
      setUploading(false)
    }
  }

  // Success state
  if (success) {
    return (
      <div className="upload-page">
        <div className="upload-success card-elevated">
          <CheckCircle2 size={56} color="var(--color-accent)" strokeWidth={1.5} />
          <h2>Analysis Complete!</h2>
          <p>
            <strong>{success.filesCount}</strong> paper{success.filesCount > 1 ? 's' : ''} analyzed
            for <strong>{success.subjectName}</strong> with{' '}
            <strong>{success.chaptersCount}</strong> syllabus chapter{success.chaptersCount > 1 ? 's' : ''}.
          </p>
          {success.efsScore !== undefined && (
            <div className="upload-success-efs">
              <span className="upload-success-score">{success.efsScore}</span>
              <span className="upload-success-label">/10 — {success.efsLabel}</span>
            </div>
          )}
          <div className="upload-success-actions">
            <button
              className="btn btn-accent"
              onClick={() => navigate(`/report/${success.analysisId}`)}
            >
              View Full Report
              <ArrowRight size={16} strokeWidth={1.5} />
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSuccess(null)
                setFiles([])
                setSubjectName('')
                setChapters('')
                setUploadProgress(0)
              }}
            >
              Upload More
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1 className="text-page-title">New Analysis</h1>
        <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
          Upload past exam papers, enter your syllabus, and let AI analyze them.
        </p>
      </div>

      {error && (
        <div className="auth-error" style={{ maxWidth: 680, marginBottom: 20 }}>
          <AlertCircle size={16} strokeWidth={1.5} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="upload-form">
        {/* Subject Name */}
        <div className="upload-section card">
          <div className="upload-section-header">
            <BookOpen size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Subject Details</h2>
          </div>

          <div className="upload-field">
            <label className="input-label" htmlFor="subject-name">Subject Name</label>
            <input
              id="subject-name"
              type="text"
              className="input"
              placeholder="e.g., Data Structures & Algorithms"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
            />
          </div>

          <div className="upload-field">
            <label className="input-label" htmlFor="syllabus-chapters">
              Syllabus Chapters
              <span className="upload-field-hint">(one per line)</span>
            </label>
            <textarea
              id="syllabus-chapters"
              className="input"
              placeholder={"Arrays and Linked Lists\nStacks and Queues\nTrees and Binary Trees\nSorting Algorithms\nGraph Algorithms"}
              value={chapters}
              onChange={(e) => setChapters(e.target.value)}
              rows={6}
            />
          </div>
        </div>

        {/* File Upload */}
        <div className="upload-section card">
          <div className="upload-section-header">
            <UploadIcon size={20} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-section-heading">Exam Papers</h2>
          </div>

          {/* Drop zone */}
          <div
            className={`upload-dropzone ${dragging ? 'upload-dropzone-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => {
                addFiles(Array.from(e.target.files))
                e.target.value = '' // Reset for re-selection
              }}
              style={{ display: 'none' }}
            />
            <div className="upload-dropzone-icon">
              <UploadIcon size={28} strokeWidth={1.5} />
            </div>
            <p className="upload-dropzone-text">
              <strong>Click to upload</strong> or drag and drop
            </p>
            <p className="upload-dropzone-hint">PDF files only · Max 20MB each</p>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="upload-file-list">
              {files.map((item, i) => (
                <div key={i} className="upload-file-item">
                  <div className="upload-file-icon">
                    <FileText size={18} strokeWidth={1.5} />
                  </div>
                  <div className="upload-file-info">
                    <span className="upload-file-name">{item.file.name}</span>
                    <span className="upload-file-size">
                      {(item.file.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                  <div className="upload-file-year">
                    <label className="text-metadata" htmlFor={`year-${i}`}>Year</label>
                    <input
                      id={`year-${i}`}
                      type="number"
                      className="input upload-year-input"
                      value={item.year}
                      onChange={(e) => updateYear(i, e.target.value)}
                      min={2000}
                      max={2099}
                    />
                  </div>
                  <button
                    type="button"
                    className="upload-file-remove"
                    onClick={() => removeFile(i)}
                    title="Remove file"
                  >
                    <Trash2 size={16} strokeWidth={1.5} />
                  </button>
                </div>
              ))}

              <button
                type="button"
                className="upload-add-more"
                onClick={() => fileInputRef.current?.click()}
              >
                <Plus size={16} strokeWidth={1.5} />
                Add More Papers
              </button>
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="upload-submit-section">
          {uploading && (
            <div className="upload-progress">
              <div className="upload-progress-bar">
                <div
                  className="upload-progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <span className="text-metadata">
                Uploading... {uploadProgress}%
              </span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-accent btn-lg upload-submit-btn"
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader size={18} strokeWidth={1.5} className="upload-spinner" />
                Uploading...
              </>
            ) : (
              <>
                <UploadIcon size={18} strokeWidth={1.5} />
                Upload & Analyze ({files.length} file{files.length !== 1 ? 's' : ''})
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
