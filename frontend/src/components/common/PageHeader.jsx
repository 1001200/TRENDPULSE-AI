import React from 'react'

export default function PageHeader({ title, subtitle, badge, action }) {
  return (
    <header className="page-header">
      <div className="page-title-group">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 className="page-title">{title}</h1>
          {badge && <span className="insights-badge">{badge}</span>}
        </div>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {action && <div className="page-actions">{action}</div>}
    </header>
  )
}
