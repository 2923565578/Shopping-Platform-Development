export function hasActiveFilters(filters) {
  return Boolean(
    filters.text?.trim() ||
      filters.category ||
      filters.minPrice !== '' ||
      filters.maxPrice !== '',
  )
}

export function localFilter(products, filters) {
  const query = (filters.text || '').trim().toLowerCase()
  const min = filters.minPrice === '' ? null : Number(filters.minPrice)
  const max = filters.maxPrice === '' ? null : Number(filters.maxPrice)

  return products.filter((product) => {
    if (filters.category) {
      const category = String(product.category || '').toLowerCase()
      if (category !== filters.category.toLowerCase()) return false
    }

    if (query) {
      const haystack = `${product.name || ''} ${product.description || ''}`.toLowerCase()
      if (!haystack.includes(query)) return false
    }

    const price = Number(product.price)
    if (min != null && Number.isFinite(min) && !(price >= min)) return false
    if (max != null && Number.isFinite(max) && !(price <= max)) return false
    return true
  })
}

export function sortProducts(products, sort) {
  const copy = [...products]
  switch (sort) {
    case 'price-asc':
      return copy.sort((a, b) => Number(a.price) - Number(b.price))
    case 'price-desc':
      return copy.sort((a, b) => Number(b.price) - Number(a.price))
    case 'stock-desc':
      return copy.sort((a, b) => Number(b.stock) - Number(a.stock))
    case 'name-asc':
    default:
      return copy.sort((a, b) =>
        String(a.name || '').localeCompare(String(b.name || ''), 'en', { sensitivity: 'base' }),
      )
  }
}
