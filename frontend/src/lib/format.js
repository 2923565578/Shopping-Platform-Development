const eur = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
})

export function money(value) {
  const number = Number(value)
  return Number.isFinite(number) ? eur.format(number) : eur.format(0)
}

export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value).replace('T', ' ').slice(0, 19)
  }
  return date.toLocaleString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function plural(count, singular, pluralForm = `${singular}s`) {
  return `${count} ${count === 1 ? singular : pluralForm}`
}
