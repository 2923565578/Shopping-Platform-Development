import { createProduct } from '../api'

// Demo catalogue used by the "Load demo products" button when the database is empty.
export const DEMO_PRODUCTS = [
  {
    name: 'Aurora 14" Ultrabook',
    description:
      'A thin 14-inch laptop with a 2.8K display, 16 GB RAM and an all-day battery — built for developers on the move.',
    category: 'electronics',
    price: 899.0,
    stock: 12,
  },
  {
    name: 'Nimbus Noise-Cancelling Headphones',
    description:
      'Over-ear wireless headphones with adaptive noise cancelling and 40 hours of playback.',
    category: 'electronics',
    price: 199.9,
    stock: 25,
  },
  {
    name: 'Clean Code (Paperback)',
    description:
      'A handbook of agile software craftsmanship by Robert C. Martin — the classic guide to writing readable code.',
    category: 'books',
    price: 34.5,
    stock: 40,
  },
  {
    name: 'Distributed Systems Explained',
    description:
      'From CAP theorem to event-driven architecture: a practical tour of the ideas behind modern microservices.',
    category: 'books',
    price: 42.0,
    stock: 18,
  },
  {
    name: 'BrewMaster Pour-Over Kettle',
    description:
      'Gooseneck kettle with precise temperature control and a 60-minute keep-warm mode for slow coffee.',
    category: 'home',
    price: 59.9,
    stock: 15,
  },
  {
    name: 'Terra Ceramic Vase',
    description:
      'Hand-glazed stoneware vase in a warm terracotta finish. A calm accent for any shelf or table.',
    category: 'home',
    price: 24.0,
    stock: 30,
  },
  {
    name: 'FlexGrip Yoga Mat',
    description:
      'Non-slip 6 mm mat made from natural rubber, with alignment lines and a carry strap.',
    category: 'sports',
    price: 29.9,
    stock: 22,
  },
  {
    name: 'Retro Arcade Mini Console',
    description:
      'A palm-sized console with 64 classic arcade games, HDMI output and two wireless controllers.',
    category: 'toys',
    price: 79.99,
    stock: 8,
  },
]

export async function seedDemoProducts() {
  let created = 0
  for (const product of DEMO_PRODUCTS) {
    await createProduct(product)
    created += 1
  }
  return created
}
