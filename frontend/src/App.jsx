import { useCallback, useEffect, useMemo, useState } from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import Catalog from './components/Catalog'
import CartDrawer from './components/CartDrawer'
import CheckoutModal from './components/CheckoutModal'
import OrderModal from './components/OrderModal'
import ProductDetailModal from './components/ProductDetailModal'
import Toasts from './components/Toasts'
import { listProducts, searchProducts } from './api'
import { hasActiveFilters, localFilter, sortProducts } from './lib/catalog'
import {
  enrichCart,
  loadCart,
  loadRecentOrders,
  saveCart,
  saveRecentOrder,
  snapshotProduct,
} from './lib/cart'
import { seedDemoProducts } from './lib/seed'

const EMPTY_FILTERS = { text: '', category: '', minPrice: '', maxPrice: '' }

export default function App() {
  const [products, setProducts] = useState([])
  const [catalogStatus, setCatalogStatus] = useState('loading')
  const [catalogError, setCatalogError] = useState('')
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [sort, setSort] = useState('name-asc')
  const [view, setView] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchNote, setSearchNote] = useState('')
  const [seeding, setSeeding] = useState(false)

  const [cart, setCart] = useState(loadCart)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [detailId, setDetailId] = useState(null)
  const [orderModal, setOrderModal] = useState(null)
  const [recentOrders, setRecentOrders] = useState(loadRecentOrders)
  const [toasts, setToasts] = useState([])

  const pushToast = useCallback((message, type = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
    setToasts((previous) => [...previous, { id, message, type }])
    setTimeout(() => {
      setToasts((previous) => previous.filter((toast) => toast.id !== id))
    }, 4000)
  }, [])

  const loadCatalog = useCallback(async () => {
    setCatalogStatus('loading')
    setCatalogError('')
    try {
      const data = await listProducts()
      setProducts(Array.isArray(data) ? data : [])
      setCatalogStatus('ready')
    } catch (error) {
      setCatalogError(error.message)
      setCatalogStatus('error')
      pushToast(`Cannot reach the API: ${error.message}`, 'error')
    }
  }, [pushToast])

  useEffect(() => {
    loadCatalog()
  }, [loadCatalog])

  useEffect(() => {
    saveCart(cart)
  }, [cart])

  useEffect(() => {
    if (drawerOpen) {
      const previous = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = previous
      }
    }
    return undefined
  }, [drawerOpen])

  // Filtering strategy: use the Elasticsearch-backed search-service whenever a
  // filter is active, but fall back to filtering the catalog locally when the
  // search index is still syncing (Kafka -> search-service is asynchronous).
  useEffect(() => {
    if (catalogStatus !== 'ready') return undefined

    if (!hasActiveFilters(filters)) {
      setView(products)
      setSearchNote('')
      setSearching(false)
      return undefined
    }

    const controller = new AbortController()
    setSearching(true)

    searchProducts(filters, controller.signal)
      .then((results) => {
        if (controller.signal.aborted) return
        const hits = Array.isArray(results) ? results : []
        if (hits.length > 0) {
          setView(hits)
          setSearchNote('')
          return
        }

        const local = localFilter(products, filters)
        setView(local)
        setSearchNote(
          local.length > 0
            ? 'search-service returned no hits — its Elasticsearch index may still be syncing. Showing local filter results instead.'
            : 'search-service returned no hits for this filter.',
        )
      })
      .catch((error) => {
        if (controller.signal.aborted) return
        setView(localFilter(products, filters))
        setSearchNote(
          `search-service unavailable (${error.message}) — showing local filter results instead.`,
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setSearching(false)
      })

    return () => controller.abort()
  }, [filters, products, catalogStatus])

  const categories = useMemo(
    () =>
      Array.from(new Set(products.map((product) => product.category).filter(Boolean))).sort((a, b) =>
        a.localeCompare(b, 'en', { sensitivity: 'base' }),
      ),
    [products],
  )

  const visibleProducts = useMemo(() => sortProducts(view, sort), [view, sort])

  const cartLines = useMemo(() => enrichCart(cart, products), [cart, products])
  const cartCount = useMemo(
    () => cart.reduce((total, item) => total + Number(item.quantity || 0), 0),
    [cart],
  )
  const cartTotal = useMemo(
    () => cartLines.reduce((total, line) => total + line.price * line.quantity, 0),
    [cartLines],
  )

  const handleFilterChange = useCallback((field, value) => {
    setFilters((previous) => ({ ...previous, [field]: value }))
  }, [])

  const handleSearch = useCallback((text) => {
    setFilters((previous) => ({ ...previous, text }))
  }, [])

  const handleReset = useCallback(() => {
    setFilters(EMPTY_FILTERS)
    setSort('name-asc')
  }, [])

  const handleHome = useCallback(() => {
    setFilters(EMPTY_FILTERS)
    setSort('name-asc')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const addToCart = useCallback(
    (id) => {
      const product = products.find((candidate) => String(candidate.id) === String(id))
      if (!product) {
        pushToast('Product not found', 'error')
        return
      }

      const stock = Number(product.stock) || 0
      if (stock <= 0) {
        pushToast(`${product.name} is out of stock`, 'error')
        return
      }

      const existing = cart.find((item) => String(item.productId) === String(product.id))
      const nextQuantity = (existing?.quantity ?? 0) + 1
      if (nextQuantity > stock) {
        pushToast(`Only ${stock} × ${product.name} available`, 'error')
        return
      }

      setCart((previous) => {
        const found = previous.find((item) => String(item.productId) === String(product.id))
        if (found) {
          return previous.map((item) =>
            item === found ? { ...item, quantity: item.quantity + 1, ...snapshotProduct(product) } : item,
          )
        }
        return [
          ...previous,
          { productId: product.id, quantity: 1, ...snapshotProduct(product) },
        ]
      })
      pushToast(`${product.name} added to cart`, 'success')
    },
    [products, cart, pushToast],
  )

  const changeQuantity = useCallback(
    (productId, delta) => {
      const line = cart.find((item) => String(item.productId) === String(productId))
      if (!line) return

      const product = products.find((candidate) => String(candidate.id) === String(productId))
      const stock = Number(product?.stock ?? line.stock) || 0
      const nextQuantity = line.quantity + delta

      if (nextQuantity <= 0) {
        setCart(cart.filter((item) => String(item.productId) !== String(productId)))
        return
      }

      if (stock > 0 && nextQuantity > stock) {
        pushToast(`Only ${stock} available for ${line.name}`, 'error')
        return
      }

      setCart(
        cart.map((item) =>
          String(item.productId) === String(productId)
            ? { ...item, quantity: nextQuantity }
            : item,
        ),
      )
    },
    [cart, products, pushToast],
  )

  const removeFromCart = useCallback(
    (productId) => {
      setCart(cart.filter((item) => String(item.productId) !== String(productId)))
    },
    [cart],
  )

  const clearCart = useCallback(() => {
    setCart([])
    pushToast('Cart cleared', 'info')
  }, [pushToast])

  const openCheckout = useCallback(() => {
    if (cartLines.length === 0) {
      pushToast('Your cart is empty', 'error')
      return
    }
    setDrawerOpen(false)
    setCheckoutOpen(true)
  }, [cartLines.length, pushToast])

  const handleOrderPlaced = useCallback((order) => {
    setCart([])
    setCheckoutOpen(false)
    setDrawerOpen(false)
    setRecentOrders(saveRecentOrder(order))
    setOrderModal({ mode: 'success', order })
  }, [])

  const handleSeed = useCallback(async () => {
    setSeeding(true)
    try {
      const created = await seedDemoProducts()
      pushToast(`${created} demo products created`, 'success')
      await loadCatalog()
    } catch (error) {
      pushToast(`Could not create demo products: ${error.message}`, 'error')
    } finally {
      setSeeding(false)
    }
  }, [loadCatalog, pushToast])

  const detailProduct = detailId
    ? products.find((product) => String(product.id) === String(detailId))
    : null

  return (
    <div className="app">
      <Header
        searchText={filters.text}
        onSearch={handleSearch}
        onHome={handleHome}
        onOpenCart={() => setDrawerOpen(true)}
        onOpenOrders={() => setOrderModal({ mode: 'lookup' })}
        cartCount={cartCount}
      />

      <main>
        <Hero productCount={products.length} categoryCount={categories.length} />
        <Catalog
          products={products}
          visibleProducts={visibleProducts}
          loading={catalogStatus === 'loading'}
          error={catalogStatus === 'error' ? catalogError : ''}
          searching={searching}
          searchNote={searchNote}
          categories={categories}
          filters={filters}
          onFilterChange={handleFilterChange}
          sort={sort}
          onSort={setSort}
          onReset={handleReset}
          onRetry={loadCatalog}
          onAdd={addToCart}
          onOpenDetail={setDetailId}
          onSeed={handleSeed}
          seeding={seeding}
        />
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <span>
            ShopStream — Development of Distributed Web Applications · University of Miskolc
          </span>
          <span className="footer-tech">Gateway :8080 · Eureka :8761 · Config :8888</span>
        </div>
      </footer>

      <div
        className={`overlay ${drawerOpen ? 'show' : ''}`}
        onClick={() => setDrawerOpen(false)}
      />

      <CartDrawer
        open={drawerOpen}
        lines={cartLines}
        total={cartTotal}
        onClose={() => setDrawerOpen(false)}
        onChangeQty={changeQuantity}
        onRemove={removeFromCart}
        onClear={clearCart}
        onCheckout={openCheckout}
      />

      {checkoutOpen && (
        <CheckoutModal
          lines={cartLines}
          total={cartTotal}
          onClose={() => setCheckoutOpen(false)}
          onPlaced={handleOrderPlaced}
          pushToast={pushToast}
        />
      )}

      {detailProduct && (
        <ProductDetailModal
          productId={detailProduct.id}
          products={products}
          onClose={() => setDetailId(null)}
          onAdd={addToCart}
        />
      )}

      {orderModal && (
        <OrderModal
          data={orderModal}
          products={products}
          recentOrders={recentOrders}
          onClose={() => setOrderModal(null)}
        />
      )}

      <Toasts toasts={toasts} />
    </div>
  )
}
