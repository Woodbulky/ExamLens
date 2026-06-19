import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ExamLensLogo from '../components/ExamLensLogo'
import { Eye, EyeOff, UserPlus, AlertCircle, CheckCircle2 } from 'lucide-react'
import './Auth.css'

export default function Signup() {
  const navigate = useNavigate()
  const { signUp } = useAuth()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!displayName || !email || !password) {
      setError('Please fill in all fields.')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    try {
      const data = await signUp({ email, password, displayName })

      // If email confirmation is required
      if (data?.user?.identities?.length === 0) {
        setError('An account with this email already exists.')
      } else if (data?.user && !data?.session) {
        setSuccess(true)
      } else {
        // Auto-confirmed — go to dashboard
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.message || 'Failed to create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-bg">
          <div className="auth-bg-gradient" />
        </div>
        <div className="auth-container">
          <div className="auth-card">
            <div className="auth-success">
              <CheckCircle2 size={48} color="var(--color-accent)" strokeWidth={1.5} />
              <h2>Check Your Email</h2>
              <p>
                We sent a confirmation link to <strong>{email}</strong>.
                Click the link to activate your account.
              </p>
              <button
                className="btn btn-secondary"
                onClick={() => navigate('/login')}
              >
                Back to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-bg">
        <div className="auth-bg-gradient" />
        <div className="auth-bg-grid" />
      </div>

      <div className="auth-container">
        <div className="auth-card">
          {/* Logo */}
          <div className="auth-logo" onClick={() => navigate('/')}>
            <div className="landing-logo-icon">
              <ExamLensLogo size={24} />
            </div>
            <span className="landing-logo-text">ExamLens</span>
          </div>

          {/* Header */}
          <div className="auth-header">
            <h1>Create your account</h1>
            <p>Start analyzing exams with AI-powered insights</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="auth-error">
              <AlertCircle size={16} strokeWidth={1.5} />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-field">
              <label className="input-label" htmlFor="signup-name">Display Name</label>
              <input
                id="signup-name"
                type="text"
                className="input"
                placeholder="Harsh"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                autoComplete="name"
                autoFocus
              />
            </div>

            <div className="auth-field">
              <label className="input-label" htmlFor="signup-email">Email</label>
              <input
                id="signup-email"
                type="email"
                className="input"
                placeholder="you@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label className="input-label" htmlFor="signup-password">Password</label>
              <div className="auth-password-wrapper">
                <input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  className="input"
                  placeholder="At least 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-accent auth-submit"
              disabled={loading}
            >
              {loading ? (
                <span className="auth-loading-text">Creating account...</span>
              ) : (
                <>
                  <UserPlus size={18} strokeWidth={1.5} />
                  Create Account
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
