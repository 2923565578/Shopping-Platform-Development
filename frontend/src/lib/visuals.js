// The backend only stores text fields for products (no image URLs), so each
// category is rendered as a deterministic gradient tile + emoji.

const CATEGORY_STYLES = [
  {
    keywords: ['electronic', 'phone', 'laptop', 'computer', 'tech', 'audio', 'headphone', 'camera'],
    emoji: '💻',
    gradient: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
  },
  {
    keywords: ['book', 'paper', 'novel', 'literature', 'education'],
    emoji: '📚',
    gradient: 'linear-gradient(135deg, #0f766e, #14b8a6)',
  },
  {
    keywords: ['home', 'kitchen', 'furniture', 'decor', 'garden'],
    emoji: '🏠',
    gradient: 'linear-gradient(135deg, #b45309, #f59e0b)',
  },
  {
    keywords: ['sport', 'fitness', 'yoga', 'outdoor', 'bike'],
    emoji: '🏃',
    gradient: 'linear-gradient(135deg, #15803d, #22c55e)',
  },
  {
    keywords: ['fashion', 'cloth', 'shoe', 'wear', 'bag'],
    emoji: '👟',
    gradient: 'linear-gradient(135deg, #be123c, #fb7185)',
  },
  {
    keywords: ['toy', 'game', 'console', 'arcade', 'kids'],
    emoji: '🎮',
    gradient: 'linear-gradient(135deg, #7e22ce, #ec4899)',
  },
  {
    keywords: ['beauty', 'health', 'care', 'cosmetic'],
    emoji: '💄',
    gradient: 'linear-gradient(135deg, #a21caf, #f472b6)',
  },
  {
    keywords: ['food', 'drink', 'coffee', 'tea', 'snack'],
    emoji: '☕',
    gradient: 'linear-gradient(135deg, #78350f, #d97706)',
  },
]

const FALLBACK_GRADIENTS = [
  'linear-gradient(135deg, #6d28d9, #4f46e5)',
  'linear-gradient(135deg, #0e7490, #2563eb)',
  'linear-gradient(135deg, #9a3412, #db2777)',
  'linear-gradient(135deg, #166534, #0891b2)',
]

export function productVisual(category, name = '') {
  const haystack = `${category || ''} ${name || ''}`.toLowerCase()
  const match = CATEGORY_STYLES.find((style) =>
    style.keywords.some((keyword) => haystack.includes(keyword)),
  )
  if (match) return match

  let hash = 0
  for (const character of haystack) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0
  }
  return {
    emoji: '📦',
    gradient: FALLBACK_GRADIENTS[hash % FALLBACK_GRADIENTS.length],
  }
}
