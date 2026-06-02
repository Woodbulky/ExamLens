import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          padding: '80px 24px',
          textAlign: 'center',
        }}>
          <AlertTriangle size={40} strokeWidth={1.5} color="#DC2626" />
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#0F2744' }}>
            Something went wrong
          </h2>
          <p style={{ fontSize: '14px', color: '#6B7280', maxWidth: '400px' }}>
            An unexpected error occurred. Please refresh the page or try again.
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null })
              window.location.reload()
            }}
            style={{
              padding: '8px 20px',
              background: '#0D9488',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Refresh Page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
