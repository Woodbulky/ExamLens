import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  BarChart3,
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
} from 'lucide-react'
import './Sidebar.css'

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/upload', icon: Upload, label: 'New Analysis' },
  { path: '/subjects', icon: BookOpen, label: 'My Subjects' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { profile, signOut } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

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
            <BarChart3 size={18} strokeWidth={1.5} color="#0D9488" />
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
                  {profile?.email || ''}
                </span>
              </div>
            )}
          </div>

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
