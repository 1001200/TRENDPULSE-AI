// Currency, percentage, and number formatting utilities for Indian Rupee

export const formatCurrency = (value) => {
  if (value == null || isNaN(value)) return '₹0'
  return '₹' + Number(value).toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })
}

export const formatPercent = (value, decimals = 1) => {
  if (value == null || isNaN(value)) return '0%'
  return Number(value).toFixed(decimals) + '%'
}

export const formatNumber = (value) => {
  if (value == null || isNaN(value)) return '0'
  return Number(value).toLocaleString('en-IN')
}

export const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export const shortenProduct = (name, maxLen = 40) => {
  if (!name) return '—'
  return name.length > maxLen ? name.slice(0, maxLen) + '…' : name
}

export const trustLevelColor = (level) => {
  const map = {
    high: 'var(--accent-emerald)',
    medium: 'var(--accent-amber)',
    low: 'var(--accent-rose)',
  }
  return map[level?.toLowerCase()] || 'var(--text-muted)'
}

export const lifecycleBadgeClass = (stage) => {
  const map = {
    new: 'badge--sky',
    emerging: 'badge--indigo',
    growing: 'badge--emerald',
    mature: 'badge--amber',
    declining: 'badge--rose',
    dead: 'badge--muted',
  }
  return map[stage?.toLowerCase()] || 'badge--muted'
}
