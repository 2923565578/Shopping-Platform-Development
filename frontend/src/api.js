// Thin client for the API gateway. Every request goes to /api/... which is
// proxied to http://api-gateway:8080 by nginx (and to localhost:8080 by Vite in dev).

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest(path, { signal, headers, ...options } = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal,
      headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError(`network error — cannot reach ${API_BASE}`, 0)
  }

  if (!response.ok) {
    let detail = ''
    try {
      const text = await response.text()
      if (text) detail = text.replace(/\s+/g, ' ').slice(0, 200)
    } catch {
      // ignore body read errors
    }
    throw new ApiError(detail || `${response.status} ${response.statusText}`, response.status)
  }

  if (response.status === 204) return null
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export const listProducts = () => apiRequest('/products')

export const getProduct = (id) => apiRequest(`/products/${id}`)

export const createProduct = (product) =>
  apiRequest('/products', { method: 'POST', body: JSON.stringify(product) })

export function searchProducts(filters, signal) {
  const params = new URLSearchParams()
  if (filters.text?.trim()) params.set('text', filters.text.trim())
  if (filters.category) params.set('category', filters.category)
  if (filters.minPrice !== '' && filters.minPrice != null) params.set('minPrice', filters.minPrice)
  if (filters.maxPrice !== '' && filters.maxPrice != null) params.set('maxPrice', filters.maxPrice)
  params.set('page', '0')
  params.set('size', '60')
  return apiRequest(`/search?${params.toString()}`, { signal })
}

export const createOrder = (items) =>
  apiRequest('/orders', { method: 'POST', body: JSON.stringify({ items }) })

export const getOrder = (id) => apiRequest(`/orders/${id}`)
