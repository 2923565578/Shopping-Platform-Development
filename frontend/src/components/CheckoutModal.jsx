import { useState } from 'react'
import { createOrder } from '../api'
import { money } from '../lib/format'
import Modal from './Modal'

export default function CheckoutModal({ lines, total, onClose, onPlaced, pushToast }) {
  const [form, setForm] = useState({ name: '', email: '', address: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  function update(field, value) {
    setForm((previous) => ({ ...previous, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const order = await createOrder(
        lines.map((line) => ({
          productId: Number(line.productId),
          quantity: Number(line.quantity),
        })),
      )
      onPlaced(order)
    } catch (err) {
      setError(err.message)
      pushToast(`Order failed: ${err.message}`, 'error')
      setSubmitting(false)
    }
  }

  return (
    <Modal onClose={onClose}>
      <h2 className="mc-title">Checkout</h2>
      <p className="mc-sub">
        order-service will price each item from product-service and publish an{' '}
        <code>order-events</code> message to Kafka.
      </p>

      <div className="summary">
        {lines.map((line) => (
          <div className="summary-row" key={line.productId}>
            <span>
              {line.name} × {line.quantity}
            </span>
            <span>{money(line.price * line.quantity)}</span>
          </div>
        ))}
        <div className="summary-row total">
          <span>Total</span>
          <span>{money(total)}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="co-name">Full name</label>
          <input
            id="co-name"
            required
            maxLength={80}
            value={form.name}
            onChange={(event) => update('name', event.target.value)}
            placeholder="Anna Kovács"
          />
        </div>
        <div className="field">
          <label htmlFor="co-email">Email</label>
          <input
            id="co-email"
            type="email"
            required
            value={form.email}
            onChange={(event) => update('email', event.target.value)}
            placeholder="anna@example.com"
          />
        </div>
        <div className="field">
          <label htmlFor="co-address">Shipping address</label>
          <input
            id="co-address"
            required
            value={form.address}
            onChange={(event) => update('address', event.target.value)}
            placeholder="3515 Miskolc, Egyetem út 1."
          />
        </div>

        <p className="mc-note">
          Demo note: the current order-service API accepts <strong>items only</strong>. The fields
          above are validated in the UI to keep the checkout flow realistic.
        </p>

        {error && <p className="mc-error">Order failed: {error}</p>}

        <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
          {submitting ? 'Placing order…' : `Place order · ${money(total)}`}
        </button>
      </form>
    </Modal>
  )
}
