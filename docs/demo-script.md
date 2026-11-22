# ShopStream 口试答辩演示脚本（练习版）

> 老师要求：真实运行项目 + 展示代码并解释 + 提交 PDF 报告。
> 本脚本按“每个服务的 ①启动时 ②请求进来 ③跟别人交互”组织，练熟后再加解说词。

---

## 0. 演示前 10 分钟准备

### 0.1 启动 Docker 和项目

```powershell
# 1) 打开 Docker Desktop，等 Engine running
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 2) 确认 Docker 就绪（能输出版本号）
docker info --format "{{.ServerVersion}}"

# 3) 启动项目
cd "F:\Final Project\ShopStream"
docker compose up -d

# 4) 等 40~60 秒，确认 13 个容器都 Up
docker compose ps
```

如果刚改过代码，用 `docker compose up -d --build`。

### 0.2 预热（避免搜索为空）

Elasticsearch 是空的时候，先触发一次重新索引：

```powershell
$base = "http://localhost:3000"
$products = Invoke-RestMethod "$base/api/products"
foreach ($p in $products) {
  $body = @{
    name = $p.name; description = $p.description; category = $p.category;
    price = $p.price; stock = $p.stock
  } | ConvertTo-Json
  Invoke-RestMethod "$base/api/products/$($p.id)" -Method Put -ContentType "application/json" -Body $body | Out-Null
}
Start-Sleep -Seconds 5
Invoke-RestMethod "$base/api/search?text=Laptop&size=5" | ConvertTo-Json -Depth 4
```

### 0.3 打开这些窗口/标签页

| 窗口 | 内容 |
|---|---|
| 浏览器标签 1 | <http://localhost:3000> |
| 浏览器标签 2 | <http://localhost:8761>（Eureka 面板） |
| 浏览器标签 3 | <http://localhost:8888/product-service/default>（配置中心） |
| Postman | 导入 `docs/postman/ShopStream.postman_collection.json` |
| IDE | 打开 `F:\Final Project\ShopStream` |
| PowerShell 1 | 项目根目录，用来跑 `docker compose logs` |
| PowerShell 2 | 用来跑 Kafka / Redis / ES 命令 |

### 0.4 IDE 提前打开这些文件（演示时直接切）

- `api-gateway/src/main/resources/application.yml`
- `api-gateway/src/main/java/.../gateway/XRequestIdFilter.java`
- `config-server/src/main/resources/application.yml`
- `config-repo/product-service.yml`
- `product-service/src/main/resources/application.yml`
- `product-service/src/main/java/.../product/ProductController.java`
- `product-service/src/main/java/.../product/Product.java`
- `order-service/src/main/java/.../order/OrderService.java`
- `order-service/src/main/java/.../order/ProductClient.java`
- `order-service/src/main/java/.../order/Order.java`
- `search-service/src/main/java/.../search/SearchController.java`
- `search-service/src/main/java/.../search/ProductEventListener.java`
- `search-service/src/main/java/.../search/ProductDocument.java`
- `cart-service/src/main/java/.../cart/CartServiceApplication.java`
- `frontend/nginx.conf`、`frontend/src/App.jsx`、`frontend/src/lib/cart.js`

---

## 1. 全程演示顺序（约 14 分钟）

### 第 1 段：全景（1 分钟）

**操作**

```powershell
docker compose ps
```

**说**

> 这是 13 个容器：注册中心、配置中心、网关、4 个业务服务、2 个 MySQL、Kafka、Elasticsearch、Redis 和前端。
> 浏览器只访问 http://localhost:3000，前端 nginx 把 `/api` 转发给网关 8080，网关再通过 Eureka 找到具体服务。

**打开**：<http://localhost:8761>，指出 `PRODUCT-SERVICE / ORDER-SERVICE / SEARCH-SERVICE / CART-SERVICE / API-GATEWAY` 都在注册列表里。

---

### 第 2 段：discovery-server :8761（1 分钟）

**操作**

1. 打开 `DiscoveryServerApplication.java`，指出 `@EnableEurekaServer`。
2. 浏览器打开 <http://localhost:8761>。

**代码解释**

> 它自己不向别人注册，只提供注册表。其他服务通过 `eureka.client.service-url.defaultZone` 注册上来。

**启动证据**

```powershell
docker compose logs discovery-server --tail 30
```

找 `Started DiscoveryServerApplication`。

---

### 第 3 段：config-server :8888（1.5 分钟）

**操作**

1. 终端访问：

```powershell
Invoke-RestMethod "http://localhost:8888/product-service/default" | ConvertTo-Json -Depth 6
```

2. 打开 `config-server/src/main/resources/application.yml`，指出：

```yaml
spring.profiles.active: native
spring.cloud.config.server.native.search-locations: file:/config-repo
```

3. 打开 `config-repo/product-service.yml`。
4. 打开 `product-service/src/main/resources/application.yml`，指出：

```yaml
spring.config.import: optional:configserver:http://config-server:8888
```

**说**

> config-server 用 native 模式直接读容器里挂载的 `/config-repo`，不连 Git。
> product-service 启动时用 `spring.config.import` 把它拉下来，所以端口、数据源、Redis、Kafka 配置可以集中管理。

**注意**：配置中心返回 JSON 时，重点指出 `propertySources` 里的 `product-service.yml`。

---

### 第 4 段：product-service :8081（3 分钟）

#### ① 启动时

```powershell
docker compose logs product-service --tail 60
```

指出日志中的：

- `Fetching config from server at http://config-server:8888`
- HikariPool / MySQL 连接
- Redis、Kafka
- `Tomcat started on port 8081`
- `DiscoveryClient_PRODUCT-SERVICE ... registration status: 204`

#### ② 请求进来

Postman 或浏览器：

```powershell
Invoke-RestMethod "http://localhost:8080/api/products" | ConvertTo-Json -Depth 4
Invoke-RestMethod "http://localhost:8080/api/products/1" | ConvertTo-Json -Depth 4
```

打开 `ProductController.java`：

- `@GetMapping` → `repo.findAll()`
- `@GetMapping("/{id}")` → `@Cacheable(value = "products", key = "#id")`
- `@PostMapping` → 保存后 `sendEvent("ProductCreated", saved)`

**Redis 缓存演示**（重点）：

```powershell
# 第一次：会打印 “从数据库查询商品: 1”
Invoke-RestMethod "http://localhost:8080/api/products/1" | Out-Null
# 第二次：命中缓存，不再打印
Invoke-RestMethod "http://localhost:8080/api/products/1" | Out-Null

docker compose logs product-service --tail 50
docker exec -it redis redis-cli -a mypass KEYS "*"
```

预期 Redis 中出现 `products::1`，并且日志里只有一条 `从数据库查询商品: 1`。

**说**

> 启动类上的 `@EnableCaching` 打开缓存，`@Cacheable` 第一次查 MySQL 并把结果写进 Redis，
> 第二次同一个 id 直接返回缓存；更新和删除上有 `@CacheEvict`，避免脏数据。

#### ③ 跟别人交互（Kafka）

Postman 新建一个商品（或直接跑）：

```powershell
$body = @{
  name = "Demo Keyboard"; description = "Mechanical keyboard for the defense";
  category = "electronics"; price = 89.99; stock = 7
} | ConvertTo-Json
Invoke-RestMethod "http://localhost:8080/api/products" -Method Post -ContentType "application/json" -Body $body
```

消费 `product-events`：

```powershell
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 --topic product-events --from-beginning --max-messages 3
```

打开 `ProductController.sendEvent`：

```java
kafkaTemplate.send("product-events", product.getId().toString(), eventType + ":" + json);
```

**说**

> 商品写库成功后，把 `ProductCreated:{json}` 发到 Kafka，key 用商品 id。
> 这样 search-service 可以异步消费，商品服务不需要等索引完成，属于最终一致性。

---

### 第 5 段：search-service :8084（2 分钟）

#### ① 启动时

```powershell
docker compose logs search-service --tail 40
```

指出：连 Elasticsearch、Kafka，注册 Eureka；没有 JPA/MySQL，所以**不建表**。

#### ② 请求进来

```powershell
Invoke-RestMethod "http://localhost:8080/api/search?text=Keyboard&size=10" | ConvertTo-Json -Depth 4
Invoke-RestMethod "http://localhost:8080/api/search?category=electronics&minPrice=50&maxPrice=150&size=10" | ConvertTo-Json -Depth 4
```

打开 `SearchController.java`，解释：

```java
BoolQuery.Builder boolQuery = new BoolQuery.Builder();
if (text != null) boolQuery.must(m -> m.multiMatch(...fields("name","description")...));
if (category != null) boolQuery.filter(f -> f.term(...));
if (minPrice != null || maxPrice != null) boolQuery.filter(f -> f.range(...));
```

**说**

> text 用 `must + multiMatch` 做全文检索；category 和价格用 `filter`，因为过滤条件不参与打分，性能更好。

#### ③ 跟别人交互

```powershell
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 --topic product-events --from-beginning --max-messages 3
```

打开 `ProductEventListener.java`：

```java
@KafkaListener(topics = "product-events")
...
if (value.startsWith("ProductCreated:") || value.startsWith("ProductUpdated:")) {
    searchRepository.save(doc);
}
```

直接查 ES：

```powershell
curl.exe "http://localhost:9200/products/_search?pretty&size=3"
```

**说**

> 监听 product-events，把 JSON 转成 ProductDocument 写入 ES；删除事件则 `deleteById`。
> 所以搜索的数据不是从 MySQL 查的，而是 Kafka 同步过来的索引。

---

### 第 6 段：order-service :8082（2.5 分钟）

#### ① 启动时

```powershell
docker compose logs order-service --tail 60
```

指出 MySQL、Kafka、Eureka 注册、Tomcat 8082。

#### ② 请求进来

Postman：`POST /api/orders`

```json
{
  "items": [
    { "productId": 1, "quantity": 2 }
  ]
}
```

或 PowerShell：

```powershell
$order = Invoke-RestMethod "http://localhost:8080/api/orders" -Method Post `
  -ContentType "application/json" `
  -Body '{"items":[{"productId":1,"quantity":2}]}'
$order | ConvertTo-Json -Depth 6
```

返回包含 `id / status=PENDING / totalPrice / items[].unitPrice`。

#### ③ 跟别人交互（Feign + Kafka）

打开 `OrderService.java`：

```java
ProductDto product = productClient.getProduct(itemReq.productId());
...
item.setUnitPrice(product.price());
total = total.add(product.price().multiply(BigDecimal.valueOf(itemReq.quantity())));
...
kafkaTemplate.send("order-events", savedOrder.getId().toString(), "OrderPlaced");
```

打开 `ProductClient.java`：

```java
@FeignClient(name = "product-service")
public interface ProductClient {
    @GetMapping("/products/{id}")
    ProductDto getProduct(@PathVariable("id") Long id);
}
```

**说**

> order-service 不直接读 product 表，而是通过 Feign 调 product-service 的接口拿价格。
> 前端传的是 productId 和数量，价格由后端决定，防止篡改；下单时把 unitPrice 快照进 order_items，商品改价不影响历史订单。
> 订单保存后向 `order-events` 发 `OrderPlaced`。

消费 `order-events`：

```powershell
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 --topic order-events --from-beginning --max-messages 3
```

查订单：

```powershell
Invoke-RestMethod "http://localhost:8080/api/orders/$($order.id)" | ConvertTo-Json -Depth 6
```

看数据库快照：

```powershell
docker exec -it order-mysql mysql -uorder -porder-pw orderdb `
  -e "SELECT id,status,total_price FROM orders; SELECT order_id,product_id,quantity,unit_price FROM order_items;"
```

**代码点**：`Order.java` 的 `@OneToMany(..., fetch = FetchType.EAGER)`——解释为什么订单查询要能把明细一起返回（避免懒加载异常）。

---

### 第 7 段：cart-service :8083（1 分钟，诚实说明）

**操作**

```powershell
curl.exe -i "http://localhost:8080/api/carts/1"
```

预期 **404**。

打开 `CartServiceApplication.java`：只有启动类，没有 Controller。

**说**

> cart-service 目前只完成了“启动 + 连 Redis + 注册 Eureka”，Controller 还没实现，所以网关转发过来是 404。
> 设计上会用 Redis Hash：key 是 `cart:{userId}`，field 是 productId，value 是数量；
> 提供 GET/POST/DELETE `/carts/{userId}`，下单时由 cart-service 调 order-service。
> 前端目前用 localStorage 临时实现购物车，等这个 API 完成后再替换。

> 不要假装它能用。老师更看重你是否知道它缺什么、下一步怎么补。

---

### 第 8 段：api-gateway :8080（1.5 分钟）

**操作 1：路由配置**

打开 `api-gateway/src/main/resources/application.yml`，指出：

```yaml
- id: product-route
  uri: lb://product-service
  predicates: [ Path=/api/products/** ]
  filters: [ StripPrefix=1 ]
```

**说**

> 浏览器请求 `/api/products`，`StripPrefix=1` 去掉第一段 `/api`，变成 `/products`，再通过 `lb://product-service` 从 Eureka 选实例。

**操作 2：GlobalFilter**

打开 `XRequestIdFilter.java`，指出：

```java
String requestId = ...getFirst("X-Request-Id");
if (requestId == null) requestId = UUID.randomUUID().toString();
log.info("Gateway Request ID: {} | Path: {}", requestId, path);
```

**演示**

```powershell
curl.exe -i -H "X-Request-Id: demo-123" "http://localhost:8080/api/products" | Select-Object -First 15
docker compose logs api-gateway --tail 100 | Select-String "demo-123"
```

日志里应出现：

```
Gateway Request ID: demo-123 | Path: /api/products
```

如果没看到，说明请求太多被刷掉了，改用：

```powershell
docker compose logs api-gateway --since 2m | Select-String "demo-123"
```

**说**

> 每个请求都带一个 request id，方便在多个微服务日志里串起同一次调用；没传就自动生成 UUID。

---

### 第 9 段：前端 :3000（2 分钟）

**浏览器操作**

1. 打开 <http://localhost:3000>
2. 搜索 `laptop`
3. 点商品 → 详情
4. 加入购物车 → 打开购物车 → 改数量
5. Checkout → 填表单 → 下单
6. 点 `Check status live` 查订单

**代码点**

- `frontend/nginx.conf`：`location /api/ { proxy_pass http://api-gateway:8080/api/; }`
- `frontend/src/api.js`：所有请求走 `/api`
- `frontend/src/lib/cart.js`：localStorage 购物车
- `frontend/src/App.jsx`：搜索用 search-service，失败时本地过滤降级

**说**

> 前端不直接访问 8081/8082，只访问同源 `/api`，由 nginx 转发给网关，避免 CORS。
> 购物车暂存 localStorage，因为 cart-service 还没实现；后续只需要替换 `cart.js`。

---

### 第 10 段：收尾（30 秒）

```powershell
docker compose ps
```

> 整套系统由 Docker Compose 编排，一条命令启动；服务之间通过 Eureka 发现、HTTP/Feign 调用、Kafka 异步事件协作，数据各自独立。

---

## 2. 故障处理（演示前背下来）

| 现象 | 原因 | 处理 |
|---|---|---|
| 页面 502/503 | 网关还没拿到 Eureka 实例 | 等 30~60 秒，刷新；`docker compose ps` 看服务是否 Up |
| 搜索返回 0 | ES 索引为空 | 跑 0.2 的重新索引脚本，等 5 秒 |
| `docker` 连不上 | Docker Desktop 没开 | 启动 Docker Desktop，等 Engine running |
| 端口被占用 | 旧容器还在 | `docker compose down --remove-orphans` 后重新 up |
| 订单 500 | 商品 id 不存在 / 服务没起来 | 先 `GET /api/products` 确认 id，再下单 |
| `npm` 找不到 | 终端 PATH 旧 | 重开 PowerShell，或用 `npm.cmd` |

---

## 3. 练习方法（按你说的：先操作，后演说）

### 第 1 轮：纯操作，不说话（目标 8~10 分钟）

- 只看本文件的命令和“操作”，把整套流程点一遍
- 卡住就记下来，不追求速度
- 目标：形成肌肉记忆，知道每个窗口放什么

### 第 2 轮：操作 + 一句话解说（目标 12~15 分钟）

- 每个动作只配 1~2 句话，不要背长段落
- 重点练 5 个“必须能讲”的点：
  1. 网关 `StripPrefix`
  2. Feign 取价 + 价格快照
  3. Kafka `product-events` → ES
  4. Redis `@Cacheable`
  5. `spring.config.import` 拉配置
- 用手机录一遍，回看哪里卡顿

### 第 3 轮：模拟提问（目标：任意打断都能应对）

让同学/自己随机问：

- “如果 product-service 挂了，下单会怎样？”
- “为什么订单状态一直是 PENDING？”
- “Kafka 挂了商品还能创建吗？”
- “为什么不用两个服务共用一个数据库？”
- “cart-service 为什么是 404？”

答不出来就回到代码里找，不要背答案。

---

## 4. 老师最可能追问的问题（简短版）

**Q1：为什么每个服务一个数据库？**
> 服务独享数据，禁止跨库读表，避免分布式单体；可以独立演进、扩容、故障隔离。

**Q2：order 为什么存 unitPrice？**
> 价格会变，订单要保存下单瞬间的价格快照，否则历史订单金额会被改价影响。

**Q3：Kafka 在项目里起什么作用？**
> 解耦 + 异步：product-service 发 `product-events`，search-service 消费建索引；order-service 发 `order-events`。生产者不需要等消费者。

**Q4：为什么订单一直是 PENDING？**
> 目前没有库存/支付消费者去更新状态。`order-events` 已经发出，后续可以加一个消费者扣库存并改成 CONFIRMED/REJECTED。

**Q5：Redis 缓存会不会脏？**
> 更新和删除接口有 `@CacheEvict`；读接口 `@Cacheable`。缓存 key 是商品 id，过期策略可以再加 TTL。

**Q6：网关的作用？**
> 统一入口、路由、`StripPrefix`、负载均衡、请求 ID；前端不需要知道每个服务的地址，也避免 CORS。

**Q7：Eureka 和 config-server 的区别？**
> Eureka 管“服务在哪里”，config-server 管“服务用什么配置”。

**Q8：search-service 为什么没有数据库？**
> 它的数据源是 Elasticsearch，通过 Kafka 事件同步，不持久化到 MySQL，也不需要 JPA 建表。

**Q9：cart-service 为什么没做完？**
> 只完成了基础设施接入；Controller 和 Redis Hash 结构还没实现，前端用 localStorage 做了可替换的临时方案。下一步是补 `GET/POST/DELETE /carts/{userId}`。

**Q10：怎么保证接口失败时的体验？**
> 网关/服务返回标准错误；前端 `api.js` 统一抛错，UI 有 toast、错误空状态和重试；搜索失败会降级到本地过滤。

---

## 5. PDF 报告目录建议

1. **封面**：项目名、姓名、学号、课程、日期
2. **项目目标与架构图**（贴 README 里那张）
3. **技术栈**：Spring Boot、Spring Cloud Gateway、Eureka、Config、MySQL、Redis、Kafka、Elasticsearch、React
4. **服务职责表**（就是你表格的内容，补充端口与存储）
5. **关键流程**
   - 启动顺序与配置加载
   - 商品查询（Redis 缓存）
   - 下单（Feign + 价格快照 + Kafka）
   - 搜索（Kafka → ES → BoolQuery）
6. **前端设计**：nginx 同源代理、SPA、localStorage 购物车、搜索降级
7. **演示截图**：`docs/screenshots/` 里的图 + Eureka 面板 + Postman + Kafka 消费 + ES 查询
8. **遇到的问题与解决**
   - MySQL 容器内 localhost 连不上 → 用服务名
   - search-service 比 ES 先启动导致崩溃 → healthcheck + service_healthy
   - `GET /orders/{id}` 懒加载 500 → EAGER / `@EntityGraph`
   - 搜索索引异步 → 前端降级
9. **未完成部分与改进方向**：cart-service、order 状态消费者、鉴权、监控
10. **总结**
