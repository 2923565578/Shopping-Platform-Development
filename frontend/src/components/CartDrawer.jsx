import { money } from '../lib/format'
import { productVisual } from '../lib/visuals'

export default function CartDrawer({
  open,
  lines,
  total,
  onClose,
  onChangeQty,
  onRemove,
  onClear,
  onCheckout,
}) {
  return (
    <aside className={`drawer ${open ? 'open' : ''}`} aria-hidden={!open}>
      <div className="drawer-head">
        <h2>Your cart</h2>
        <button className="icon-btn" onClick={onClose} aria-label="Close cart">
          ✕
        </button>
      </div>

      <div className="drawer-body">
        {lines.length === 0 && (
          <div className="cart-empty">
            Your cart is empty.
            <br />
            Add something from the catalog.
          </div>
        )}

        {lines.map((line) => {
          const visual = productVisual(line.category, line.name)
          return (
            <div className="cart-item" key={line.productId}>
              <div className="cart-thumb" style={{ background: visual.gradient }}>
                {visual.emoji}
              </div>
              <div>
                <h4>{line.name}</h4>
                <span className="unit">
                  {money(line.price)} each
                  {line.stock > 0 ? ` · ${line.stock} in stock` : ''}
                </span>
                <div className="qty">
                  <button onClick={() => onChangeQty(line.productId, -1)} aria-label="Decrease quantity">
                    −
                  </button>
                  <span>{line.quantity}</span>
                  <button onClick={() => onChangeQty(line.productId, 1)} aria-label="Increase quantity">
                    +
                  </button>
                </div>
              </div>
              <div>
                <div className="line-total">{money(line.price * line.quantity)}</div>
                <button
                  className="cart-remove"
                  onClick={() => onRemove(line.productId)}
                  aria-label={`Remove ${line.name}`}
                >
                  ✕
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <div className="drawer-foot">
        <div className="cart-total-row">
          <span>Total</span>
          <strong>{money(total)}</strong>
        </div>
        <button className="btn btn-primary btn-block" onClick={onCheckout} disabled={lines.length === 0}>
          Checkout
        </button>
        <button className="btn btn-ghost btn-block btn-sm" onClick={onClear} disabled={lines.length === 0}>
          Clear cart
        </button>
      </div>
    </aside>
  )
}
