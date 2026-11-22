import { useEffect, useState } from 'react'

export default function Header({ searchText, onSearch, onHome, onOpenCart, onOpenOrders, cartCount }) {
  const [query, setQuery] = useState(searchText)

  useEffect(() => {
    setQuery(searchText)
  }, [searchText])

  // Live search with a small debounce — the submit button still works for instant search.
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query !== searchText) onSearch(query)
    }, 400)
    return () => clearTimeout(timer)
  }, [query, searchText, onSearch])

  return (
    <header className="site-header">
      <div className="container header-inner">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault()
            onHome()
          }}
        >
          <span className="brand-mark">◆</span>
          <span className="brand-text">
            Shop<span>Stream</span>
          </span>
        </a>

        <form
          className="search-form"
          onSubmit={(event) => {
            event.preventDefault()
            onSearch(query)
          }}
        >
          <span className="search-icon">⌕</span>
          <input
            type="search"
            value={query}
            placeholder="Search products by name or description…"
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search products"
          />
          <button type="submit" className="btn btn-primary btn-sm">
            Search
          </button>
        </form>

        <div className="header-actions">
          <button className="icon-btn" onClick={onOpenOrders} title="Track an order">
            <span className="icon">▤</span>
            <span className="icon-label">Orders</span>
          </button>
          <button className="icon-btn cart-btn" onClick={onOpenCart} title="Open cart">
            <span className="icon">🛒</span>
            <span className="cart-badge">{cartCount}</span>
          </button>
        </div>
      </div>
    </header>
  )
}
