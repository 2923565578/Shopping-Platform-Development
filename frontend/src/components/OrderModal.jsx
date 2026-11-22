import { useState } from 'react'
import { getOrder } from '../api'
import { formatDate, money } from '../lib/format'
import Modal from './Modal'

function productName(products, productId) {
  return (
    products.find((product) => String(product.id) === String(productId))?.name ??
    `Product #${productId}`
  )
}

function OrderLines({ order, products }) {
  const items = Array.isArray(order.items) ? order.items : []
  return (
    <div className="summary">
      {items.map((item, index) => (
        <div className="summary-row" key={item.id ?? `${item.productId}-${index}`}>
          <span>
            {productName(products, item.productId)} × {item.quantity}
          </span>
          <span>{money(Number(item.unitPrice) * Number(item.quantity))}</span>
        </div>
      ))}
      <div className="summary-row total">
        <span>Total</span>
        <span>{money(order.totalPrice)}</span>
      </div>
    </div>
  )
}

export default function OrderModal({ data, products, recentOrders, onClose }) {
  const successOrder = data.mode === 'success' ? data.order : null
  const [showLookup, setShowLookup] = useState(data.mode === 'lookup')
  const [lookupId, setLookupId] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function lookup(id) {
    const value = String(id ?? lookupId).trim()
    if (!value) {
      setError('Enter an order ID first.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const order = await getOrder(value)
      setResult(order)
    } catch (err) {
      setError(
        err.status === 404
          ? `Order #${value} was not found.`
          : `Could not load order #${value}: ${err.message}`,
      )
    } finally {
      setLoading(false)
    }
  }

  const showSuccessPanel = successOrder && !showLookup

  return (
    <Modal onClose={onClose}>
      {showSuccessPanel ? (
        <div className="order-success">
          <div className="big-icon">✅</div>
          <h3>Order placed</h3>
          <p className="mc-sub">
            order-service created the order and published an <code>order-events</code> message.
          </p>
          <p>
            Order <span className="oid">#{successOrder.id}</span>{' '}
            <span className={`status-pill status-${successOrder.status || 'PENDING'}`}>
              {successOrder.status || 'PENDING'}
            </span>
          </p>
          <p className="mc-sub">Created {formatDate(successOrder.createdAt)}</p>
        </div>
      ) : (
        <>
          <h2 className="mc-title">Track an order</h2>
          <p className="mc-sub">
            Looks up an order through <code>GET /api/orders/{'{id}'}</code> (routed by the API
            gateway to order-service).
          </p>

          <form
            className="lookup-form"
            onSubmit={(event) => {
              event.preventDefault()
              lookup(lookupId)
            }}
          >
            <input
              type="number"
              min="1"
              placeholder="Order ID"
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
              aria-label="Order ID"
            />
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Loading…' : 'Track'}
            </button>
          </form>

          {error && <p className="mc-error">{error}</p>}
        </>
      )}

      {showSuccessPanel && <OrderLines order={successOrder} products={products} />}

      {result && (
        <div className="order-detail">
          <div className="order-detail-head">
            <span>
              Order <span className="order-code">#{result.id}</span>
            </span>
            <span className={`status-pill status-${result.status || 'PENDING'}`}>
              {result.status || 'PENDING'}
            </span>
          </div>
          <p className="mc-sub">Created {formatDate(result.createdAt)}</p>
          <OrderLines order={result} products={products} />
        </div>
      )}

      {!showSuccessPanel && recentOrders.length > 0 && !result && (
        <div>
          <p className="mc-sub">Recent orders on this device</p>
          <div className="recent-orders">
            {recentOrders.map((order) => (
              <button
                key={order.id}
                className="recent-order"
                onClick={() => {
                  setLookupId(String(order.id))
                  lookup(order.id)
                }}
              >
                <span className="order-code">#{order.id}</span>
                <span className={`status-pill status-${order.status || 'PENDING'}`}>
                  {order.status || 'PENDING'}
                </span>
                <span>{money(order.totalPrice)}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mc-actions">
        {showSuccessPanel && (
          <button
            className="btn btn-primary btn-block"
            onClick={() => {
              setShowLookup(true)
              setLookupId(String(successOrder.id))
              lookup(successOrder.id)
            }}
          >
            Check status live
          </button>
        )}
        <button className="btn btn-ghost btn-block" onClick={onClose}>
          {showSuccessPanel ? 'Continue shopping' : 'Close'}
        </button>
      </div>
    </Modal>
  )
}
