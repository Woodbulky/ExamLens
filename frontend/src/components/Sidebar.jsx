import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import ExamLensLogo from './ExamLensLogo'
import {
  LayoutDashboard,
  Upload,
  FileText,
  TrendingUp,
  Download,
  BookOpen,
  Settings,
  LogOut,
  ChevronLeft,
  Menu,
  GraduationCap,
  Sun,
  Moon,
} from 'lucide-react'
import './Sidebar.css'

const studentNav = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/upload', icon: Upload, label: 'New Analysis' },
  { path: '/subjects', icon: BookOpen, label: 'My Subjects' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

const professorNav = [
  { path: '/prof-dashboard', icon: GraduationCap, label: 'Prof Dashboard' },
  { path: '/upload', icon: Upload, label: 'New Analysis' },
  { path: '/subjects', icon: BookOpen, label: 'My Exams' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { profile, signOut, isProf } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const navItems = isProf ? professorNav : studentNav

  async function handleLogout() {
    try {
      await signOut()
      navigate('/login')
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="sidebar-mobile-toggle"
        onClick={() => setMobileOpen(true)}
        aria-label="Open menu"
      >
        <Menu size={22} strokeWidth={1.5} />
      </button>

      {/* Backdrop for mobile */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <ExamLensLogo size={22} />
          </div>
          {!collapsed && <span className="sidebar-logo-text">ExamLens</span>}
        </div>

        {/* Nav Items */}
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `sidebar-nav-item ${isActive ? 'sidebar-nav-item-active' : ''}`
              }
              onClick={() => setMobileOpen(false)}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={20} strokeWidth={1.5} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom Section */}
        <div className="sidebar-bottom">
          {/* User Info */}
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {(profile?.display_name || 'U').charAt(0).toUpperCase()}
            </div>
            {!collapsed && (
              <div className="sidebar-user-info">
                <span className="sidebar-user-name">
                  {profile?.display_name || 'User'}
                </span>
                <span className="sidebar-user-email">
                  {isProf ? '🎓 Professor' : profile?.email || ''}
                </span>
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button
            className="sidebar-nav-item sidebar-theme-toggle"
            onClick={toggleTheme}
            title={collapsed ? (theme === 'dark' ? 'Light Mode' : 'Dark Mode') : undefined}
          >
            {theme === 'dark' ? (
              <Sun size={20} strokeWidth={1.5} />
            ) : (
              <Moon size={20} strokeWidth={1.5} />
            )}
            {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
          </button>

          {/* Logout */}
          <button
            className="sidebar-nav-item sidebar-logout"
            onClick={handleLogout}
            title={collapsed ? 'Log Out' : undefined}
          >
            <LogOut size={20} strokeWidth={1.5} />
            {!collapsed && <span>Log Out</span>}
          </button>

          {/* Collapse Toggle */}
          <button
            className="sidebar-collapse-btn hide-mobile"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            <ChevronLeft
              size={18}
              strokeWidth={1.5}
              style={{
                transform: collapsed ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.2s ease',
              }}
            />
          </button>
        </div>
      </aside>
    </>
  )
}
