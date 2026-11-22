# ShopStream Frontend

React 19 + Vite single-page storefront for the ShopStream microservices backend.

## How it talks to the backend

```
Browser ──/api/*──▶ nginx (container :80) ──▶ api-gateway:8080 ──▶ Eureka services
```

- In **production** nginx serves the built bundle and proxies `/api/` to `api-gateway:8080`.
- In **development** Vite proxies `/api/` to `http://localhost:8080`.
- The browser never calls a service directly, so there is no CORS configuration needed.

## Run with Docker (recommended)

From the repository root:

```bash
docker compose up -d --build
```

Open <http://localhost:3000>.

## Run locally (development)

Backend must be running (the gateway on `:8080`), then:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## API endpoints used

| UI feature | Request |
| --- | --- |
| Product grid | `GET /api/products` |
| Product detail | `GET /api/products/{id}` |
| Search + filters | `GET /api/search?text=&category=&minPrice=&maxPrice=&page=&size=` |
| Checkout | `POST /api/orders` with `{ "items": [{ "productId": 1, "quantity": 2 }] }` |
| Order tracking | `GET /api/orders/{id}` |
| Demo data | `POST /api/products` (button shown when the catalog is empty) |

## Notes / design decisions

- **Cart is client-side (`localStorage`).** `cart-service` currently has no REST controller,
  so the cart lives in the browser. When the cart API is added, only the cart state layer
  needs to change.
- **Search has a local fallback.** `search-service` is fed asynchronously through Kafka, so a
  freshly created product may not be indexed yet. When Elasticsearch returns no hits, the UI
  filters the catalog locally and shows a note explaining why.
- **Images are generated.** Products only have text fields, so each category is rendered as a
  gradient tile + emoji.
- **Product detail is fetched again** from `GET /api/products/{id}` (which product-service
  caches in Redis) and falls back to the catalog copy if the request fails.
- **Prices shown in the cart are display-only.** order-service recomputes the total from
  product-service and stores a `unitPrice` snapshot on each order item.

## Structure

```
frontend/
├─ src/
│  ├─ api.js                 # fetch wrapper for /api
│  ├─ App.jsx                # state orchestration
│  ├─ styles.css
│  ├─ components/            # Header, Hero, Catalog, CartDrawer, modals, toasts
│  └─ lib/                   # formatting, visuals, cart storage, filtering, demo data
├─ nginx.conf                # static serving + /api reverse proxy
├─ Dockerfile                # node build stage -> nginx runtime stage
└─ vite.config.js            # dev proxy to localhost:8080
```
