import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import AppLayout from './components/AppLayout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import ProfDashboard from './pages/ProfDashboard'
import Upload from './pages/Upload'
import Subjects from './pages/Subjects'
import Report from './pages/Report'
import Predictions from './pages/Predictions'
import StudyPlan from './pages/StudyPlan'
import Export from './pages/Export'
import Settings from './pages/Settings'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected routes (with sidebar layout) */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/prof-dashboard" element={<ProfDashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/subjects" element={<Subjects />} />
            <Route path="/report/:analysisId" element={<Report />} />
            <Route path="/predictions/:analysisId" element={<Predictions />} />
            <Route path="/study-plan/:analysisId" element={<StudyPlan />} />
            <Route path="/export/:analysisId" element={<Export />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
