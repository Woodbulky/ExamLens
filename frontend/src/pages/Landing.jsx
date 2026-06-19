import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Shield,
  TrendingUp,
  FileText,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Zap,
  BookOpen,
  Target,
} from 'lucide-react'
import ExamLensLogo from '../components/ExamLensLogo'
import './Landing.css'

const features = [
  {
    icon: <Sparkles size={24} strokeWidth={1.5} />,
    title: 'AI-Powered Classification',
    description: 'Claude AI classifies every exam question into syllabus chapters with confidence scoring.',
  },
  {
    icon: <BarChart3 size={24} strokeWidth={1.5} />,
    title: 'EFS Score™',
    description: 'Proprietary Examination Fairness Score quantifies topic bias on a 0–10 scale.',
  },
  {
    icon: <TrendingUp size={24} strokeWidth={1.5} />,
    title: 'Topic Predictions',
    description: 'Predict likely exam topics based on historical frequency analysis across years.',
  },
  {
    icon: <FileText size={24} strokeWidth={1.5} />,
    title: 'Research-Ready Exports',
    description: 'Export PDF reports, CSV data, and IEEE-formatted research methodology packages.',
  },
]

const stats = [
  { value: '10', label: 'EFS Score Scale', suffix: '' },
  { value: '4', label: 'AI Analysis Points', suffix: '' },
  { value: '3', label: 'Score Components', suffix: '' },
  { value: '100', label: 'Questions per Paper', suffix: '+' },
]

const steps = [
  {
    icon: <FileText size={20} strokeWidth={1.5} />,
    title: 'Upload Past Papers',
    description: 'Upload PDF exam papers from multiple years for any subject.',
  },
  {
    icon: <BookOpen size={20} strokeWidth={1.5} />,
    title: 'Enter Syllabus',
    description: 'List your syllabus chapters — the AI maps questions to these topics.',
  },
  {
    icon: <Zap size={20} strokeWidth={1.5} />,
    title: 'AI Analysis',
    description: 'Claude classifies questions, calculates EFS, and generates insights.',
  },
  {
    icon: <Target size={20} strokeWidth={1.5} />,
    title: 'Get Predictions',
    description: 'See which topics will likely appear and practice with AI-generated questions.',
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const [animatedStats, setAnimatedStats] = useState(stats.map(() => 0))

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedStats(stats.map((s) => parseInt(s.value)))
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-nav-inner container">
          <div className="landing-logo">
            <div className="landing-logo-icon">
              <ExamLensLogo size={24} />
            </div>
            <span className="landing-logo-text">ExamLens</span>
          </div>
          <div className="landing-nav-actions">
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => navigate('/login')}
            >
              Log In
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate('/signup')}
            >
              Get Started
              <ArrowRight size={16} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-bg">
          <div className="landing-hero-gradient" />
          <div className="landing-hero-grid" />
        </div>
        <div className="container landing-hero-content">
          <div className="landing-hero-badge animate-fade-in">
            <Sparkles size={14} strokeWidth={1.5} />
            <span>AI-Powered Exam Analysis</span>
          </div>
          <h1 className="landing-hero-title animate-slide-up">
            Measure Exam Fairness.
            <br />
            <span className="landing-hero-accent">Predict What's Next.</span>
          </h1>
          <p className="landing-hero-subtitle animate-slide-up" style={{ animationDelay: '0.1s' }}>
            ExamLens uses AI to analyze university past papers, detect topic bias,
            and predict likely questions — built for students and researchers.
          </p>
          <div className="landing-hero-actions animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <button
              className="btn btn-accent btn-lg"
              onClick={() => navigate('/signup')}
            >
              Start Analyzing
              <ArrowRight size={18} strokeWidth={1.5} />
            </button>
            <button
              className="btn btn-secondary btn-lg"
              onClick={() => {
                document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              How It Works
            </button>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="landing-stats">
        <div className="container">
          <div className="landing-stats-grid">
            {stats.map((stat, i) => (
              <div key={i} className="landing-stat-item">
                <span className="landing-stat-value">
                  {animatedStats[i]}{stat.suffix}
                </span>
                <span className="landing-stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="landing-features">
        <div className="container">
          <div className="landing-section-header">
            <span className="text-label" style={{ color: 'var(--color-accent)' }}>CAPABILITIES</span>
            <h2 className="text-page-title">Everything You Need to Analyze Exams</h2>
            <p className="text-body" style={{ color: 'var(--color-text-secondary)', maxWidth: '600px' }}>
              From PDF upload to AI-powered insights, ExamLens handles the entire analysis pipeline.
            </p>
          </div>
          <div className="landing-features-grid">
            {features.map((feature, i) => (
              <div
                key={i}
                className="landing-feature-card card"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="landing-feature-icon">{feature.icon}</div>
                <h3 className="text-section-heading">{feature.title}</h3>
                <p className="text-body" style={{ color: 'var(--color-text-secondary)' }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="landing-how-it-works" id="how-it-works">
        <div className="container">
          <div className="landing-section-header">
            <span className="text-label" style={{ color: 'var(--color-accent)' }}>HOW IT WORKS</span>
            <h2 className="text-page-title">Four Steps to Exam Intelligence</h2>
          </div>
          <div className="landing-steps-grid">
            {steps.map((step, i) => (
              <div key={i} className="landing-step">
                <div className="landing-step-number">{i + 1}</div>
                <div className="landing-step-icon">{step.icon}</div>
                <h3 className="text-body-semi">{step.title}</h3>
                <p className="text-metadata">{step.description}</p>
                {i < steps.length - 1 && <div className="landing-step-connector" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* EFS Score Explainer */}
      <section className="landing-efs">
        <div className="container">
          <div className="landing-efs-card">
            <div className="landing-efs-left">
              <span className="text-label" style={{ color: 'var(--color-accent)' }}>THE EFS SCORE™</span>
              <h2 className="text-page-title" style={{ color: 'var(--color-text-inverse)' }}>
                Examination Fairness Score
              </h2>
              <p style={{ color: 'rgba(255,255,255,0.75)', lineHeight: 1.6 }}>
                The EFS Score combines three components to measure how fairly an exam covers the syllabus — Topic Bias Index, Syllabus Coverage Score, and Recurrence Penalty.
              </p>
              <div className="landing-efs-components">
                {[
                  { label: 'TBI', weight: '40%', desc: 'Topic Bias Index' },
                  { label: 'SCS', weight: '35%', desc: 'Syllabus Coverage' },
                  { label: 'RP', weight: '25%', desc: 'Recurrence Penalty' },
                ].map((comp, i) => (
                  <div key={i} className="landing-efs-component">
                    <div className="landing-efs-comp-header">
                      <span className="landing-efs-comp-label">{comp.label}</span>
                      <span className="landing-efs-comp-weight">{comp.weight}</span>
                    </div>
                    <span className="landing-efs-comp-desc">{comp.desc}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="landing-efs-right">
              <div className="landing-efs-score-display">
                <div className="landing-efs-score-ring">
                  <span className="landing-efs-score-number">6.35</span>
                  <span className="landing-efs-score-label">/ 10</span>
                </div>
                <span className="badge badge-moderate" style={{ fontSize: '14px', padding: '4px 16px' }}>
                  Moderate
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="landing-cta">
        <div className="container">
          <div className="landing-cta-inner">
            <CheckCircle2 size={32} strokeWidth={1.5} color="var(--color-accent)" />
            <h2 className="text-page-title">Ready to Analyze Your Exams?</h2>
            <p className="text-body" style={{ color: 'var(--color-text-secondary)', maxWidth: '500px' }}>
              Upload your past papers, enter your syllabus, and get AI-powered insights in under 90 seconds.
            </p>
            <button
              className="btn btn-accent btn-lg"
              onClick={() => navigate('/signup')}
            >
              Get Started Free
              <ArrowRight size={18} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container landing-footer-inner">
          <div className="landing-footer-brand">
            <div className="landing-logo">
              <div className="landing-logo-icon">
                <ExamLensLogo size={20} />
              </div>
              <span className="landing-logo-text" style={{ fontSize: '16px' }}>ExamLens</span>
            </div>
            <p className="text-metadata">AI-powered examination analysis for students and researchers.</p>
          </div>
          <p className="text-metadata">
            Built for IEEE TALE / EDUCON research publication · © 2025 ExamLens
          </p>
        </div>
      </footer>
    </div>
  )
}
