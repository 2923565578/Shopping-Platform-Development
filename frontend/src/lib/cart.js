const CART_KEY = 'shopstream.cart.v1'
const ORDERS_KEY = 'shopstream.orders.v1'

export function loadCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY) || '[]')
    if (!Array.isArray(raw)) return []
    return raw
      .filter((item) => item && item.productId != null && Number(item.quantity) > 0)
      .map((item) => ({
        productId: item.productId,
        quantity: Math.floor(Number(item.quantity)),
        name: item.name,
        price: Number(item.price),
        category: item.category,
        stock: Number(item.stock),
      }))
  } catch {
    return []
  }
}

export function saveCart(cart) {
  try {
    localStorage.setItem(CART_KEY, JSON.stringify(cart))
  } catch {
    // localStorage may be unavailable (private mode) — cart just won't persist
  }
}

export function snapshotProduct(product) {
  return {
    name: product.name,
    price: Number(product.price),
    category: product.category,
    stock: Number(product.stock),
  }
}

// Merge stored cart snapshots with the live catalog, so prices/names stay fresh
// when the page is reloaded or a product is updated.
export function enrichCart(cart, products) {
  return cart.map((item) => {
    const product = products.find((candidate) => String(candidate.id) === String(item.productId))
    return {
      ...item,
      name: product?.name ?? item.name ?? `Product #${item.productId}`,
      price: Number(product?.price ?? item.price) || 0,
      category: product?.category ?? item.category ?? '',
      stock: Number(product?.stock ?? item.stock) || 0,
      available: Boolean(product),
    }
  })
}

export function loadRecentOrders() {
  try {
    const raw = JSON.parse(localStorage.getItem(ORDERS_KEY) || '[]')
    return Array.isArray(raw) ? raw.slice(0, 8) : []
  } catch {
    return []
  }
}

export function saveRecentOrder(order) {
  const entry = {
    id: order.id,
    status: order.status,
    totalPrice: Number(order.totalPrice),
    createdAt: order.createdAt,
  }
  const next = [
    entry,
    ...loadRecentOrders().filter((item) => String(item.id) !== String(order.id)),
  ].slice(0, 8)
  try {
    localStorage.setItem(ORDERS_KEY, JSON.stringify(next))
  } catch {
    // ignore
  }
  return next
}
