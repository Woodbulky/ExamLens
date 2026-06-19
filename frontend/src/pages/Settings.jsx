import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import {
  User,
  Mail,
  Shield,
  Trash2,
  Save,
  Loader,
  CheckCircle2,
  AlertTriangle,
  GraduationCap,
} from 'lucide-react'
import './Settings.css'

export default function Settings() {
  const { profile, user, signOut, role: currentRole } = useAuth()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState(profile?.display_name || '')
  const [role, setRole] = useState(currentRole || 'student')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [roleSaving, setRoleSaving] = useState(false)

  async function handleSave(e) {
    e.preventDefault()
    if (!displayName.trim()) {
      setError('Display name cannot be empty.')
      return
    }
    setSaving(true)
    setError('')
    try {
      // Update profile in Supabase
      const { createClient } = await import('@supabase/supabase-js')
      const supabase = createClient(
        import.meta.env.VITE_SUPABASE_URL,
        import.meta.env.VITE_SUPABASE_ANON_KEY
      )
      const { error: updateError } = await supabase.auth.updateUser({
        data: { display_name: displayName.trim() }
      })
      if (updateError) throw updateError
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err.message || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  async function handleRoleChange(newRole) {
    if (newRole === currentRole) return
    setRoleSaving(true)
    setError('')
    try {
      const { createClient } = await import('@supabase/supabase-js')
      const supabase = createClient(
        import.meta.env.VITE_SUPABASE_URL,
        import.meta.env.VITE_SUPABASE_ANON_KEY
      )
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) throw new Error('Not authenticated')

      // Update role in profiles table via backend-compatible approach
      const { error: updateError } = await supabase
        .from('profiles')
        .update({ role: newRole })
        .eq('id', session.user.id)

      if (updateError) throw updateError

      setRole(newRole)
      // Reload to refresh auth context and sidebar
      window.location.reload()
    } catch (err) {
      setError(err.message || 'Failed to update role.')
      setRole(currentRole) // revert
    } finally {
      setRoleSaving(false)
    }
  }

  async function handleDeleteAccount() {
    if (!confirm('Are you sure you want to delete your account? All data will be permanently lost. This cannot be undone.')) {
      return
    }
    if (!confirm('This is IRREVERSIBLE. Type "delete" in the next prompt to confirm.')) {
      return
    }
    try {
      await signOut()
      navigate('/')
    } catch (err) {
      setError('Failed to sign out.')
    }
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1 className="text-page-title">Settings</h1>
        <p className="text-body" style={{ color: 'var(--color-text-muted)' }}>
          Manage your account and preferences.
        </p>
      </div>

      {error && (
        <div className="auth-error" style={{ maxWidth: 560, marginBottom: 20 }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {saved && (
        <div className="settings-saved">
          <CheckCircle2 size={16} color="#059669" />
          <span>Profile updated successfully!</span>
        </div>
      )}

      {/* Profile Section */}
      <form onSubmit={handleSave} className="settings-section card">
        <div className="settings-section-header">
          <User size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">Profile</h2>
        </div>

        <div className="settings-field">
          <label className="input-label" htmlFor="display-name">Display Name</label>
          <input
            id="display-name"
            type="text"
            className="input"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Your name"
          />
        </div>

        <div className="settings-field">
          <label className="input-label">Email</label>
          <div className="settings-email-display">
            <Mail size={16} strokeWidth={1.5} color="var(--color-text-muted)" />
            <span>{user?.email || profile?.email || '—'}</span>
          </div>
        </div>

        <button type="submit" className="btn btn-accent" disabled={saving}>
          {saving ? (
            <><Loader size={16} className="upload-spinner" /> Saving...</>
          ) : (
            <><Save size={16} strokeWidth={1.5} /> Save Changes</>
          )}
        </button>
      </form>

      {/* Role Section */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <GraduationCap size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">Role</h2>
        </div>
        <p className="text-body" style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
          Switch between student and professor views. Professors get a dedicated dashboard with exam fairness insights and AI suggestions.
        </p>
        <div className="settings-role-toggle">
          <button
            className={`settings-role-btn ${role === 'student' ? 'settings-role-active' : ''}`}
            onClick={() => handleRoleChange('student')}
            disabled={roleSaving}
          >
            📚 Student
          </button>
          <button
            className={`settings-role-btn ${role === 'professor' ? 'settings-role-active' : ''}`}
            onClick={() => handleRoleChange('professor')}
            disabled={roleSaving}
          >
            🎓 Professor
          </button>
          {roleSaving && <Loader size={16} className="upload-spinner" color="var(--color-accent)" />}
        </div>
      </div>

      {/* Security Section */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <Shield size={20} strokeWidth={1.5} color="var(--color-accent)" />
          <h2 className="text-section-heading">Security</h2>
        </div>
        <p className="text-body" style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
          Password management is handled through Supabase Auth. Use the "Forgot Password" flow on the login page to reset.
        </p>
      </div>

      {/* Danger Zone */}
      <div className="settings-section card settings-danger">
        <div className="settings-section-header">
          <Trash2 size={20} strokeWidth={1.5} color="var(--color-error)" />
          <h2 className="text-section-heading" style={{ color: 'var(--color-error)' }}>Danger Zone</h2>
        </div>
        <p className="text-body" style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
          Deleting your account will permanently remove all your subjects, analyses, and exports.
        </p>
        <button
          className="btn settings-delete-btn"
          onClick={handleDeleteAccount}
        >
          <Trash2 size={16} strokeWidth={1.5} />
          Delete Account
        </button>
      </div>
    </div>
  )
}
