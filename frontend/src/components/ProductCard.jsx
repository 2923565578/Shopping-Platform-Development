import { money } from '../lib/format'
import { productVisual } from '../lib/visuals'

export default function ProductCard({ product, onAdd, onOpenDetail }) {
  const visual = productVisual(product.category, product.name)
  const stock = Number(product.stock) || 0
  const soldOut = stock <= 0

  return (
    <article
      className="card"
      role="button"
      tabIndex={0}
      aria-label={`View ${product.name}`}
      onClick={() => onOpenDetail(product.id)}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onOpenDetail(product.id)
        }
      }}
    >
      <div className="card-media" style={{ background: visual.gradient }}>
        <span className="cat-badge">{product.category || 'general'}</span>
        <span className={`stock-badge ${soldOut ? 'out' : ''}`}>
          {soldOut ? 'Sold out' : `${stock} in stock`}
        </span>
        <span className="media-emoji">{visual.emoji}</span>
      </div>

      <div className="card-body">
        <h3>{product.name}</h3>
        <p>{product.description || 'No description provided.'}</p>
        <div className="card-foot">
          <span className="price">{money(product.price)}</span>
          <div className="card-actions">
            <button
              className="btn btn-primary"
              disabled={soldOut}
              onClick={(event) => {
                event.stopPropagation()
                onAdd(product.id)
              }}
            >
              {soldOut ? 'Sold out' : 'Add'}
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
