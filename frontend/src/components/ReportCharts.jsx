/**
 * Report Charts — Interactive Recharts components for the Report page
 *
 * ChapterBarChart: Horizontal grouped bar chart (actual vs expected questions)
 * DifficultyDonut: Donut/Pie chart for difficulty distribution
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

/* ========================================
   Custom Tooltip
   ======================================== */
function ChapterTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontSize: 12,
      lineHeight: 1.6,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4, color: 'var(--color-text)' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 500 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  )
}

function DiffTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value, percent } = payload[0].payload
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontSize: 12,
    }}>
      <div style={{ fontWeight: 700, color: 'var(--color-text)' }}>{name}</div>
      <div style={{ color: 'var(--color-text-secondary)' }}>
        {value} questions ({percent}%)
      </div>
    </div>
  )
}

/* ========================================
   Chapter Bar Chart
   ======================================== */
export function ChapterBarChart({ chapterStats }) {
  if (!chapterStats || chapterStats.length === 0) return null

  const data = chapterStats.map((ch) => ({
    name: ch.chapter_name.length > 18
      ? ch.chapter_name.substring(0, 18) + '…'
      : ch.chapter_name,
    fullName: ch.chapter_name,
    Actual: ch.questions_asked,
    Expected: Math.round(ch.expected_questions * 10) / 10,
    status: ch.status || 'Fair',
  }))

  return (
    <div style={{ width: '100%', height: Math.max(280, data.length * 40) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
          barGap={2}
          barCategoryGap="25%"
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={false}
            stroke="var(--color-border)"
          />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<ChapterTooltip />} cursor={{ fill: 'var(--color-surface-dim)', opacity: 0.5 }} />
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            iconType="circle"
            iconSize={8}
          />
          <Bar
            dataKey="Actual"
            fill="var(--color-accent)"
            radius={[0, 4, 4, 0]}
            animationDuration={800}
          />
          <Bar
            dataKey="Expected"
            fill="var(--color-border-hover)"
            radius={[0, 4, 4, 0]}
            animationDuration={800}
            animationBegin={200}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ========================================
   Difficulty Donut Chart
   ======================================== */
const DIFF_COLORS = {
  Easy: '#34D399',
  Medium: '#FBBF24',
  Hard: '#F87171',
}

export function DifficultyDonut({ distribution }) {
  if (!distribution) return null

  const total = Object.values(distribution).reduce((a, b) => a + b, 0)
  if (total === 0) return null

  const data = ['Easy', 'Medium', 'Hard'].map((level) => {
    const count = distribution[level] || 0
    return {
      name: level,
      value: count,
      percent: total > 0 ? Math.round((count / total) * 100) : 0,
    }
  })

  return (
    <div style={{ width: '100%', height: 260, position: 'relative' }}>
      {/* Center label */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
        pointerEvents: 'none',
        zIndex: 1,
      }}>
        <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.02em' }}>
          {total}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>
          Questions
        </div>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            animationDuration={800}
            stroke="var(--color-surface)"
            strokeWidth={2}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={DIFF_COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip content={<DiffTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 4 }}
            iconType="circle"
            iconSize={8}
            formatter={(value, entry) => {
              const item = data.find(d => d.name === value)
              return `${value} (${item?.value || 0})`
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ========================================
   Bloom's Taxonomy Radar Chart
   ======================================== */
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts'

const BLOOMS_COLORS = {
  Remember: '#60A5FA',
  Understand: '#34D399',
  Apply: '#A78BFA',
  Analyze: '#FBBF24',
  Evaluate: '#FB923C',
  Create: '#F472B6',
}

const BLOOMS_ORDER = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']

function BloomsTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { level, count, percent } = payload[0].payload
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontSize: 12,
    }}>
      <div style={{ fontWeight: 700, color: BLOOMS_COLORS[level] || 'var(--color-text)' }}>{level}</div>
      <div style={{ color: 'var(--color-text-secondary)' }}>
        {count} questions ({percent}%)
      </div>
    </div>
  )
}

export function BloomsRadarChart({ distribution }) {
  if (!distribution) return null

  const total = Object.values(distribution).reduce((a, b) => a + b, 0)
  if (total === 0) return null

  const data = BLOOMS_ORDER.map((level) => ({
    level,
    count: distribution[level] || 0,
    percent: total > 0 ? Math.round(((distribution[level] || 0) / total) * 100) : 0,
    fullMark: Math.max(...Object.values(distribution), 1),
  }))

  return (
    <div className="blooms-chart-container">
      <div className="blooms-radar-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="var(--color-border)" />
            <PolarAngleAxis
              dataKey="level"
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)', fontWeight: 500 }}
            />
            <PolarRadiusAxis
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              axisLine={false}
              tickCount={4}
            />
            <Tooltip content={<BloomsTooltip />} />
            <Radar
              name="Questions"
              dataKey="count"
              stroke="var(--color-accent)"
              fill="var(--color-accent)"
              fillOpacity={0.25}
              strokeWidth={2}
              animationDuration={800}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="blooms-legend">
        {data.map((d) => (
          <div key={d.level} className="blooms-legend-item">
            <span
              className="blooms-legend-dot"
              style={{ background: BLOOMS_COLORS[d.level] }}
            />
            <span className="blooms-legend-label">{d.level}</span>
            <span className="blooms-legend-count">{d.count}</span>
            <span className="blooms-legend-pct">{d.percent}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ========================================
   Confidence Quality Badge
   ======================================== */
export function ConfidenceBadge({ distribution }) {
  if (!distribution) return null

  const total = (distribution.High || 0) + (distribution.Medium || 0) + (distribution.Low || 0)
  if (total === 0) return null

  const highPct = Math.round(((distribution.High || 0) / total) * 100)
  const medPct = Math.round(((distribution.Medium || 0) / total) * 100)
  const lowPct = Math.round(((distribution.Low || 0) / total) * 100)

  let quality, qualityColor
  if (highPct >= 70) { quality = 'High'; qualityColor = '#059669' }
  else if (highPct + medPct >= 70) { quality = 'Moderate'; qualityColor = '#D97706' }
  else { quality = 'Low'; qualityColor = '#DC2626' }

  return (
    <div className="confidence-badge-container">
      <div className="confidence-badge-header">
        <span className="confidence-badge-label">AI Confidence</span>
        <span className="confidence-badge-quality" style={{ color: qualityColor }}>
          {quality}
        </span>
      </div>
      <div className="confidence-badge-bar-track">
        <div
          className="confidence-badge-bar-segment"
          style={{ width: `${highPct}%`, background: '#34D399' }}
          title={`High: ${distribution.High || 0}`}
        />
        <div
          className="confidence-badge-bar-segment"
          style={{ width: `${medPct}%`, background: '#FBBF24' }}
          title={`Medium: ${distribution.Medium || 0}`}
        />
        <div
          className="confidence-badge-bar-segment"
          style={{ width: `${lowPct}%`, background: '#F87171' }}
          title={`Low: ${distribution.Low || 0}`}
        />
      </div>
      <div className="confidence-badge-labels">
        <span style={{ color: '#059669' }}>High {highPct}%</span>
        <span style={{ color: '#D97706' }}>Med {medPct}%</span>
        <span style={{ color: '#DC2626' }}>Low {lowPct}%</span>
      </div>
    </div>
  )
}
