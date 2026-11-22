import { useEffect } from 'react'

export default function Modal({ onClose, children, cardClassName = '' }) {
  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = previousOverflow
    }
  }, [onClose])

  return (
    <div
      className="modal open"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className={`modal-card ${cardClassName}`.trim()}>
        <button className="modal-close" onClick={onClose} aria-label="Close dialog">
          ✕
        </button>
        {children}
      </div>
    </div>
  )
}
