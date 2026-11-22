import { useEffect, useState } from 'react'
import { getProduct } from '../api'
import { money } from '../lib/format'
import { productVisual } from '../lib/visuals'
import Modal from './Modal'

export default function ProductDetailModal({ productId, products, onClose, onAdd }) {
  const fallback = products.find((product) => String(product.id) === String(productId))
  const [product, setProduct] = useState(fallback || null)
  const [loading, setLoading] = useState(!fallback)

  useEffect(() => {
    let active = true
    setProduct(fallback || null)
    setLoading(!fallback)

    getProduct(productId)
      .then((fresh) => {
        if (active && fresh) setProduct(fresh)
      })
      .catch(() => {
        // keep the catalog copy if the detail request fails
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId])

  if (loading && !product) {
    return (
      <Modal onClose={onClose} cardClassName="product-modal-card">
        <div className="pd-info">
          <p className="mc-sub">Loading product…</p>
        </div>
      </Modal>
    )
  }

  if (!product) {
    return (
      <Modal onClose={onClose} cardClassName="product-modal-card">
        <div className="pd-info">
          <h2>Product not found</h2>
          <p className="mc-sub">It may have been deleted from product-service.</p>
        </div>
      </Modal>
    )
  }

  const visual = productVisual(product.category, product.name)
  const stock = Number(product.stock) || 0
  const soldOut = stock <= 0

  return (
    <Modal onClose={onClose} cardClassName="product-modal-card">
      <div className="pd-grid">
        <div className="pd-media" style={{ background: visual.gradient }}>
          {visual.emoji}
        </div>
        <div className="pd-info">
          <div className="cat">{product.category || 'general'}</div>
          <h2>{product.name}</h2>
          <p className="desc">{product.description || 'No description provided.'}</p>
          <div className="pd-price-row">
            <span className="price">{money(product.price)}</span>
            <span className="pd-stock">
              {soldOut ? 'Out of stock' : `${stock} in stock`}
            </span>
          </div>
          <div className="pd-actions">
            <button
              className="btn btn-primary"
              disabled={soldOut}
              onClick={() => {
                onAdd(product.id)
                onClose()
              }}
            >
              {soldOut ? 'Sold out' : 'Add to cart'}
            </button>
            <button className="btn btn-ghost" onClick={onClose}>
              Keep browsing
            </button>
          </div>
        </div>
      </div>
    </Modal>
  )
}
