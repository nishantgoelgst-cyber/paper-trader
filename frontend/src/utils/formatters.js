export function formatINR(amount) {
  if (amount == null) return '-'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatNumber(num, decimals = 2) {
  if (num == null) return '-'
  return Number(num).toFixed(decimals)
}

export function formatPct(num) {
  if (num == null) return '-'
  return `${Number(num).toFixed(2)}%`
}

export function formatTime(isoString) {
  if (!isoString) return '-'
  const d = new Date(isoString)
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function pnlClass(value) {
  if (value == null || value === 0) return ''
  return value > 0 ? 'profit' : 'loss'
}
