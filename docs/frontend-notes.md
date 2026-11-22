# 前端答辩笔记 — React + Vite + nginx

## 1. 这一步做了什么

给已有的 Spring Boot 微服务后端配一个完整的购物前台：

- 商品列表 / 详情 / 分类 / 价格筛选 / 排序
- 搜索（调用 `search-service`，带本地降级）
- 购物车（浏览器 localStorage）
- 下单（`POST /api/orders`）
- 订单查询（`GET /api/orders/{id}`）

技术栈：**React 19 + Vite 8**，构建产物是纯静态文件，由 **nginx** 托管。

## 2. 为什么前端不直接调各个微服务

如果浏览器直接请求 `product-service:8081`、`order-service:8082`：

1. **CORS**：每个服务都要单独配置允许的源，容易漏配。
2. **端口暴露**：用户端要知道每个服务的地址，服务一扩容就失效。
3. **绕过网关**：限流、鉴权、日志、请求 ID 都会丢失。

所以统一走：

```
Browser ──/api/*──▶ nginx ──▶ api-gateway:8080 ──▶ Eureka 服务发现 ──▶ 具体服务
```

浏览器只认识自己的源（`localhost:3000`），**同源请求，天然没有 CORS**。
nginx 在容器网络里用服务名 `api-gateway` 访问网关。

## 3. 为什么用 React + Vite

- **组件化**：一个页面拆成 Header / Hero / Catalog / CartDrawer / Modal 等组件，
  和微服务「按职责拆分」的思想一致，答辩时很好讲。
- **Vite**：开发时毫秒级热更新；生产用 Rollup 打包，产物小（本项目的 JS gzip 后约 77 KB）。
- **部署不变**：`npm run build` 输出 `dist/`，仍然是静态文件，塞进 nginx 即可。

Dockerfile 用**多阶段构建**：

```dockerfile
FROM node:24-alpine AS build     # 阶段 1：编译 React
...
FROM nginx:alpine                # 阶段 2：只保留 dist 和 nginx
```

最终镜像里**没有 node_modules、没有源码、没有 Node**，只有静态文件和 nginx，镜像更小、攻击面更小。

## 4. 购物车为什么放在 localStorage

`cart-service` 目前只有启动类，没有 Controller（没有 `GET /carts/{userId}` 之类的接口）。
为了不阻塞前端，购物车先放在浏览器：

- 存 `[{ productId, quantity, name, price, ... }]`
- 刷新页面不丢
- 页面加载商品列表后，用**实时商品数据覆盖快照里的价格/库存**
- 下单时只把 `productId + quantity` 发给 order-service

**这一点答辩要主动说**：不是「设计成前端购物车」，而是「cart-service 的 API 还没实现，
前端做了可替换的临时实现」。等 cart-service 补上 Controller，只需要改 `src/lib/cart.js`，
UI 组件不用动。这体现了**面向接口、关注点分离**。

## 5. 搜索为什么要做本地降级

数据流是：

```
product-service ──Kafka(product-events)──▶ search-service ──▶ Elasticsearch
```

Kafka 是**异步**的。刚创建的商品可能还没进 ES，此时 `GET /api/search`
返回空数组。如果前端直接显示「没有结果」，演示时会很尴尬。

前端的处理：

1. 先调 `/api/search`；
2. 如果返回 0 条，用当前商品列表做本地过滤；
3. 在结果栏提示「search-service 暂无命中，索引可能仍在同步，已展示本地过滤结果」。

这体现了对**最终一致性**的理解，而不是把异步系统当同步系统用。

## 6. 下单流程与价格快照

前端发送：

```json
POST /api/orders
{ "items": [ { "productId": 1, "quantity": 2 } ] }
```

前端**不发送价格**。order-service 通过 Feign 调 product-service 获取当前价格，
计算总价，并把 `unitPrice` 快照写进 `order_items`。

答辩点：

- 价格由**后端**决定，前端传价格可以被篡改。
- 订单保存下单瞬间的单价，商品后续改价不会影响历史订单。
- 购物车里显示的价格只是 UI 展示，最终以订单返回的 `totalPrice` 为准。

## 7. 订单状态

下单返回 `status: PENDING`。order-service 会向 `order-events` 发消息。
目前 product-service 没有消费该事件扣减库存，所以订单会停在 `PENDING`。
前端用不同颜色展示 `PENDING / CONFIRMED / REJECTED`，为后续消费者留好接口。

## 8. 演示顺序（建议）

1. `docker compose ps`：展示 gateway、Eureka、Config、各业务服务、MySQL、Kafka、ES、Redis、frontend。
2. 打开 `http://localhost:3000`：商品页加载成功（说明 nginx → gateway → Eureka → product-service 全链路通）。
3. 点分类 / 输入价格区间：说明请求走的是 search-service。
4. 点商品卡片：`GET /api/products/{id}`，说明 Redis 缓存。
5. 加购、改数量：说明 localStorage。
6. 下单：Network 面板展示 `POST /api/orders` 请求体只有 id + quantity，响应含 totalPrice。
7. 点「Check status live」：再发一次 `GET /api/orders/{id}`。
8. 停掉 search-service（`docker compose stop search-service`），再搜索：
   前端提示 search-service 不可用并展示本地结果 —— 展示**优雅降级**。

## 9. 可能被问到

**Q：为什么不用 Next.js / SSR？**
A：这是后台管理系统式的电商前台，不需要 SEO 和服务端渲染；静态 SPA + nginx 部署最简单，
也最符合「前端只是微服务的一个消费者」这个定位。

**Q：前端如何知道后端服务地址？**
A：不需要知道。前端只请求同源 `/api`，由 nginx 转发到网关，网关再通过 Eureka 做负载均衡。
服务扩容、换端口，前端零改动。

**Q：为什么购物车不加到后端？**
A：cart-service 还没有 API。硬加会引入新的数据库/接口设计，超出当前步骤范围。
现在的实现是**可替换的适配层**，不是架构终点。

**Q：前端怎么做错误处理？**
A：`api.js` 统一封装 fetch：非 2xx 抛出带状态码的 `ApiError`；UI 用 toast + 空状态 +
重试按钮呈现；搜索失败自动降级到本地过滤。

**Q：为什么用 localStorage 而不是 sessionStorage / cookie？**
A：购物车需要跨标签页、跨会话保留，localStorage 最合适；不涉及敏感凭证，不需要 httpOnly cookie。

---

## 10. 实际验证结果（2026-11-06）

环境：Windows + Docker Desktop，全部容器通过 `docker compose up -d --build` 启动。

### 基础设施
- `http://localhost:3000` 返回 200，React 挂载成功（`<div id="root">`）。
- 静态资源 `/assets/index-*.js`、`/assets/index-*.css` 均返回 200。
- Eureka 注册列表：`SEARCH-SERVICE, API-GATEWAY, CART-SERVICE, ORDER-SERVICE, CONFIG-SERVER, PRODUCT-SERVICE`。

### API 链路（全部经 nginx 同源代理）
| 测试 | 结果 |
| --- | --- |
| `GET /api/products` | 10 条商品 |
| `POST /api/products` | 新建成功，id=13 |
| Kafka → Elasticsearch → `GET /api/search?text=Smoke Test` | 1 条命中 |
| `GET /api/search?category=test&minPrice=10&maxPrice=20` | 1 条命中 |
| `POST /api/orders` | 返回 id、`PENDING`、`totalPrice`、订单明细 |
| `GET /api/orders/{id}` | 返回同样的订单数据 |

### 浏览器交互（Playwright + 系统 Edge，无头）
- 首屏渲染 10 张商品卡片。
- 搜索 `laptop`：命中 4 条（本地降级），页面提示
  “search-service returned no hits — its Elasticsearch index may still be syncing.”
- 加购后购物车角标变为 1，抽屉显示总价 €50.00。
- 结算：填写姓名/邮箱/地址 → `POST /api/orders` → 显示 `Order #5 / PENDING`。
- 点击 “Check status live” → `GET /api/orders/5` → 展示明细与总价。
- 浏览器控制台 **0 错误**。

截图：

- `docs/screenshots/storefront.png`
- `docs/screenshots/order-placed.png`
- `docs/screenshots/order-tracking.png`

### 顺手修复的编排问题
`search-service` 启动时 Elasticsearch 还没就绪，会因 `Connection refused` 直接退出。
已在 `docker-compose.yml` 为 `elasticsearch` 增加 healthcheck，并把 `search-service`
的依赖改为 `condition: service_healthy`，避免冷启动偶发 503。

