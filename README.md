# ShopStream – Distributed E-Commerce Platform

ShopStream is a distributed e-commerce platform built with Spring Boot microservices. It demonstrates how Docker, Apache Kafka, Elasticsearch, Redis, and Spring Cloud work together in one system. The whole platform can be started with a single `docker compose up --build` command, and all client traffic enters through a single API Gateway.

## Architecture

- `api-gateway` – Spring Cloud Gateway, port 8080, single entry point for all client requests
- `discovery-server` – Eureka service registry, port 8761
- `config-server` – Spring Cloud Config, port 8888
- `product-service` – product CRUD, stock management, MySQL + Redis cache, port 8081
- `order-service` – order management, MySQL, port 8082
- `cart-service` – Redis shopping cart, port 8083
- `search-service` – product search with Elasticsearch, port 8084
- `notification-service` – consumes Kafka events and logs notifications, port 8085
- Infrastructure: MySQL, Redis, Elasticsearch, Kafka (KRaft)

All services register with Eureka and load their configuration from the config server.

## Quick Start

```bash
docker compose up --build -d
docker compose ps















# ShopStream 分布式电商平台

ShopStream 是一个基于 Spring Cloud 微服务架构的电商平台后端系统，实现了商品管理、订单处理、购物车、搜索等核心功能。

## 🏗️ 架构图
*(请在这里插入你用 draw.io 画的架构图，展示 Gateway、Eureka、Config 和各个微服务的关系)*

## 🚀 服务列表及端口约定
| 服务名 | 端口 | 描述 |
| :--- | :--- | :--- |
| api-gateway | 8080 | API 网关（统一入口） |
| discovery-server | 8761 | Eureka 注册中心 |
| config-server | 8888 | Spring Cloud Config 配置中心 |
| product-service | 8081 | 商品服务（MySQL + Redis 缓存） |
| order-service | 8082 | 订单服务（MySQL + Feign + Kafka） |
| cart-service | 8083 | 购物车服务（Redis） |
| search-service | 8084 | 搜索服务（Elasticsearch） |

## 💻 启动命令
整个项目基于 Docker Compose 一键启动：
```bash
docker compose up --build -d




注意：首次启动需要下载大量依赖包，请耐心等待。所有微服务都不暴露宿主机端口，统一通过 8080 网关访问。

🧪 Postman 使用说明
项目根目录下附带了 postman 文件夹，导入 ShopStream.postman_collection.json 即可测试。

商品模块: http://localhost:8080/api/products

订单模块: http://localhost:8080/api/orders

购物车模块: http://localhost:8080/api/carts

搜索模块: http://localhost:8080/api/search

🌐 容器网络说明
所有服务运行在同一个 Docker 自定义网络中。

服务间通信：使用服务名，例如 http://product-service:8081。

禁止使用：localhost（在容器内部 localhost 指向容器自身）。

🛒 购物车 TTL 选择
购物车数据存储在 Redis 中，设置了 30 分钟 (1800秒) 的 TTL（生存时间）。
设计理由：30 分钟符合大部分用户的会话（Session）超时习惯，既能保证用户短时间离开后回来数据还在，又能防止僵尸数据长期占用 Redis 内存。

❓ 常见问题 (FAQ)
服务起不来？ 检查 Docker Desktop 是否分配了足够的内存（建议 4GB 以上），因为 ES 和多个微服务很吃内存。

网关报 503 错误？ 说明后端微服务还没完全注册到 Eureka，等待 30 秒再试。
