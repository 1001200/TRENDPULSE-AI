import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  BarChart2,
  ShoppingBag,
  Tag,
  Users,
  Flame,
  UploadCloud,
  Settings,
  Sparkles
} from 'lucide-react'

const navGroups = [
  {
    title: 'MENU',
    items: [
      { path: '/', label: 'Overview', icon: LayoutDashboard },
      { path: '/sales', label: 'Sales Performance', icon: BarChart2 },
      { path: '/products', label: 'Products', icon: ShoppingBag },
      { path: '/sizes-pricing', label: 'Sizes & Pricing', icon: Tag },
      { path: '/customers', label: 'Customers', icon: Users },
      { path: '/trends', label: 'Trends', icon: Flame },
    ]
  },
  {
    title: 'TOOLS',
    items: [
      { path: '/upload', label: 'Upload Data', icon: UploadCloud },
      { path: '/settings', label: 'Settings', icon: Settings },
    ]
  }
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-logo-icon">
          <Sparkles size={18} strokeWidth={2.2} />
        </div>
        <div className="brand-title-wrap">
          <span className="brand-title">TrendPulse</span>
          <span className="brand-tag">RETAIL INTELLIGENCE</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="sidebar-nav">
        {navGroups.map((group, idx) => (
          <div key={idx} className="nav-group-section">
            <div className="nav-section-label">{group.title}</div>
            {group.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                  end={item.path === '/'}
                >
                  <Icon className="nav-icon" size={17} strokeWidth={1.9} />
                  <span className="nav-label">{item.label}</span>
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Sidebar Footer with Live Status */}
      <div className="sidebar-footer">
        <div className="sidebar-status-pill">
          <span className="sidebar-status-dot" />
          <span className="sidebar-status-text">Fashion BI Engine</span>
        </div>
      </div>
    </aside>
  )
}
