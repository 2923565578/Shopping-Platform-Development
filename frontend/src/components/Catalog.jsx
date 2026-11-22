import { hasActiveFilters } from '../lib/catalog'
import ProductCard from './ProductCard'

export default function Catalog({
  products,
  visibleProducts,
  loading,
  error,
  searching,
  searchNote,
  categories,
  filters,
  onFilterChange,
  sort,
  onSort,
  onReset,
  onRetry,
  onAdd,
  onOpenDetail,
  onSeed,
  seeding,
}) {
  const total = products.length
  const shown = visibleProducts.length
  const filtersActive = hasActiveFilters(filters)

  return (
    <section className="container catalog">
      <div className="toolbar">
        <div className="chips">
          <button
            className={`chip ${!filters.category ? 'is-active' : ''}`}
            onClick={() => onFilterChange('category', '')}
          >
            All
          </button>
          {categories.map((category) => (
            <button
              key={category}
              className={`chip ${filters.category === category ? 'is-active' : ''}`}
              onClick={() => onFilterChange('category', category)}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="toolbar-right">
          <div className="price-range">
            <input
              type="number"
              min="0"
              step="1"
              placeholder="Min €"
              value={filters.minPrice}
              onChange={(event) => onFilterChange('minPrice', event.target.value)}
              aria-label="Minimum price"
            />
            <span>–</span>
            <input
              type="number"
              min="0"
              step="1"
              placeholder="Max €"
              value={filters.maxPrice}
              onChange={(event) => onFilterChange('maxPrice', event.target.value)}
              aria-label="Maximum price"
            />
          </div>

          <select value={sort} onChange={(event) => onSort(event.target.value)} aria-label="Sort products">
            <option value="name-asc">Name A–Z</option>
            <option value="price-asc">Price: low → high</option>
            <option value="price-desc">Price: high → low</option>
            <option value="stock-desc">Stock: high → low</option>
          </select>

          <button className="btn btn-ghost btn-sm" onClick={onReset}>
            Reset
          </button>
        </div>
      </div>

      <div className="result-meta">
        <span>
          {loading
            ? 'Loading products…'
            : `${shown} of ${total} product${total === 1 ? '' : 's'}${
                filtersActive ? ' matching your filters' : ''
              }`}
        </span>
        {searching && <span className="search-pending">Searching…</span>}
        {!searching && searchNote && <span className="search-note">{searchNote}</span>}
      </div>

      {loading && (
        <div className="empty-state">
          <div className="empty-icon">⏳</div>
          <h3>Contacting the API gateway</h3>
          <p>Products are being loaded from product-service via /api/products…</p>
        </div>
      )}

      {!loading && error && (
        <div className="empty-state">
          <div className="empty-icon">🔌</div>
          <h3>Cannot reach the API</h3>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && shown > 0 && (
        <div className="product-grid">
          {visibleProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onAdd={onAdd}
              onOpenDetail={onOpenDetail}
            />
          ))}
        </div>
      )}

      {!loading && !error && shown === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📦</div>
          {total === 0 ? (
            <>
              <h3>No products yet</h3>
              <p>The catalog is empty. Load a few demo products to explore the storefront.</p>
              <button className="btn btn-primary" onClick={onSeed} disabled={seeding}>
                {seeding ? 'Creating products…' : 'Load demo products'}
              </button>
            </>
          ) : (
            <>
              <h3>No products match</h3>
              <p>Try clearing the filters or searching for a different term.</p>
              <button className="btn btn-ghost" onClick={onReset}>
                Clear filters
              </button>
            </>
          )}
        </div>
      )}
    </section>
  )
}
