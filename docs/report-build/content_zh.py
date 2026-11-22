"""Chinese content of the ShopStream final report (personal reference copy)."""
from reportlab.lib.units import cm

SERVICE_W = [3.0 * cm, 1.15 * cm, 4.7 * cm, 7.95 * cm]
CAP_W = [4.3 * cm, 4.2 * cm, 4.35 * cm, 4.35 * cm]


def blocks():
    B = []
    B.append((
        "titlepage",
        "ShopStream 分布式电商平台",
        "期末项目 · 实验报告（中文自存版）",
        [
            "学生：徐浩杰（Neptun 学号：DTR5N0）",
            "米什科尔茨大学 · 信息技术学院",
            "课程：Web / 分布式系统 — 期末项目",
            "授课教师：Atallah Fadi",
            "日期：2026 年 11 月 22 日 · 提交截止：12 月 4 日",
            "口试答辩：12 月 9 日",
            "说明：本文件与提交给老师的英文版内容一一对应，仅作个人复盘与复用参考。",
        ],
    ))

    B.append(("h1", "目录"))
    for line in [
        "1. 系统是什么——总体架构",
        "2. Docker——整个平台如何容器化",
        "3. Spring Cloud——配置中心、注册中心、API 网关",
        "4. Kafka——事件驱动的下单流程",
        "5. Elasticsearch——索引、同步与搜索查询",
        "6. Redis——商品缓存与购物车",
        "7. 运行结果——一次完整链路",
        "8. 遇到的问题与解决办法",
        "9. 如何启动项目",
        "10. 附录 A——注解速查表",
        "11. 附录 B——口试演示脚本",
    ]:
        B.append(("p", line))
    B.append(("break",))

    # ------------------------------------------------------------------ 1
    B.append(("h1", "1. 系统是什么——总体架构"))
    B.append(("p",
              "ShopStream 是一个由 8 个 Spring Boot 应用组成的在线商店，运行时是 14 个 Docker 容器。"
              "客户端只访问一个地址——8080 端口的 API 网关；网关去 Eureka 里查目标服务再转发。"
              "服务之间不写死 IP：靠服务名互相发现（Eureka + Feign），靠 Kafka 交换业务事件，"
              "靠 Redis 存快速变化的临时数据。前端只是一个由 nginx 托管的小 React 演示页面；"
              "这个项目里我自己做的是后端：各个服务、事件流和基础设施。"))

    B.append(("h2", "1.1 服务与职责"))
    B.append(("table", [
        ["服务", "端口", "存储 / 技术", "职责"],
        ["api-gateway", "8080", "Spring Cloud Gateway", "唯一入口，按路径路由，加 X-Request-Id 过滤器"],
        ["discovery-server", "8761", "Eureka Server", "注册中心，其他服务都往这里注册"],
        ["config-server", "8888", "Spring Cloud Config（native）", "把 config-repo 里的 YAML 配置发给各服务"],
        ["product-service", "8081", "MySQL + Redis 缓存 + Kafka", "商品增删改查、预留库存、发 product-events"],
        ["order-service", "8082", "MySQL + Kafka + Feign", "创建订单，用 Feign 取价格，维护订单状态"],
        ["cart-service", "8083", "Redis", "每个用户一个购物车，TTL 1 小时；结算时用 Feign 调 order-service"],
        ["search-service", "8084", "Elasticsearch + Kafka", "消费 product-events 写索引，提供 /search"],
        ["notification-service", "8085", "只有 Kafka，无数据库", "消费订单/库存事件，打印“邮件通知”日志"],
        ["frontend", "3000", "React 构建产物 + nginx", "演示页面，把 /api 反向代理到网关"],
    ], SERVICE_W))

    B.append(("h2", "1.2 两条关键链路"))
    B.append(("p",
              "读链路：浏览器 → 网关 8080 → Eureka 查到实例 → product-service 8081 → MySQL，"
              "单商品接口前面还有一层 Redis 缓存。"))
    B.append(("p",
              "下单链路：POST /api/orders → order-service（用 Feign 调 product-service 取价格）→ "
              "订单以 PENDING 落库 → 往 Kafka 发 OrderPlaced → product-service 原子扣库存并回发 "
              "StockReserved → order-service 把订单改成 CONFIRMED 并广播 OrderConfirmed → "
              "notification-service 打印邮件日志。同时商品的每次变更都会发到 product-events，"
              "由 search-service 同步进 Elasticsearch。"))

    B.append(("img", "02-eureka.png",
              "图 1 — Eureka 面板（http://localhost:8761）。7 个应用全部 UP：API-GATEWAY 8080、"
              "CART-SERVICE 8083、CONFIG-SERVER 8888、NOTIFICATION-SERVICE 8085、ORDER-SERVICE 8082、"
              "PRODUCT-SERVICE 8081、SEARCH-SERVICE 8084。"))

    # ------------------------------------------------------------------ 2
    B.append(("break",))
    B.append(("h1", "2. Docker——整个平台如何容器化"))
    B.append(("p",
              "项目需要的东西全部是容器：7 个服务、网关、前端、两个 MySQL、Kafka、Elasticsearch、Redis。"
              "这也是整个系统能在另一台电脑上一条命令起来、不用手动装环境的原因。"))

    B.append(("h2", "2.1 我写了什么，为什么这么写"))
    B.append(("table", [
        ["文件 / 配置", "它做了什么", "为什么用"],
        ["docker-compose.yml",
         "定义 14 个容器：构建上下文、镜像、端口、环境变量、数据卷、健康检查、启动顺序。",
         "一个文件描述整个系统，老师或同学执行 docker compose up -d 就能复现我的运行环境。"],
        ["每个服务的 Dockerfile（多阶段构建）",
         "第一阶段用 maven:3.9.9-eclipse-temurin-21 打出 jar；第二阶段只把这个 jar 拷到 "
         "eclipse-temurin:21-jre 里。",
         "构建在容器内完成，本机不需要装 Maven 和 JDK；运行时镜像很小，因为源码和 Maven 仓库不会进去。"],
        ["environment: SPRING_DATASOURCE_URL = jdbc:mysql://product-mysql:3306/productdb",
         "以环境变量把数据库地址传给服务。",
         "主机名就是容器名，Docker DNS 会自动解析，代码里不出现任何 IP，同一个镜像在哪台机器都能跑。"],
        ["healthcheck（mysqladmin ping、curl /_cluster/health）",
         "Docker 反复执行一个小命令，直到数据库或 ES 真正就绪。",
         "Hibernate 和 ES 客户端不能对着还在初始化的数据库启动；健康检查让启动过程变得确定。"],
        ["depends_on + condition: service_healthy / service_started",
         "product-service 等 product-mysql（healthy）、kafka、redis、config-server；"
         "search-service 等 elasticsearch（healthy）。",
         "这里启动顺序是真实依赖：消费者比 Kafka 先起来会丢第一批消息，MySQL 没好 JPA 会直接失败。"],
        ["volumes: product-mysql-data、order-mysql-data、./config-repo:/config-repo",
         "命名卷保存数据库文件；绑定挂载把配置文件交给 config-server。",
         "数据必须在 docker compose down 之后还在；配置要能在宿主上直接改，不用重建镜像。"],
        ["ports：只发布 8080、8761、8888、9200、16379、9092、3000",
         "product（8081）、order（8082）、cart（8083）、search（8084）、notification（8085）"
         "只在 Docker 网络内部可见。",
         "网关是唯一对外入口，内部服务不应该从外面直接访问，这也是真实部署的样子。"],
    ], CAP_W))

    B.append(("h2", "2.2 运行结果"))
    B.append(("img", "01-containers.png",
              "图 2 — 在 F:\\Final Project\\ShopStream 下执行 docker compose ps。14 个容器全部 Up，"
              "两个 MySQL 和 Elasticsearch 显示 (healthy)；PORT 一列正好体现了 2.1 的策略：只暴露基础设施。"))
    B.append(("p",
              "镜像只构建一次，之后每次测试开场都是 docker compose up -d，大约 1 分钟整套栈就起来了。"))

    # ------------------------------------------------------------------ 3
    B.append(("break",))
    B.append(("h1", "3. Spring Cloud——配置中心、注册中心、API 网关"))
    B.append(("p",
              "三个 Spring Cloud 组件让服务彼此不依赖对方的地址和配置。"))

    B.append(("h2", "3.1 配置中心：配置只放一份"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "具体值", "为什么"],
        ["ConfigServerApplication",
         "@SpringBootApplication + @EnableConfigServer",
         "server.port: 8888",
         "@EnableConfigServer 把应用变成配置服务器，对外提供 GET /{application}/{profile}。"],
        ["config-server/application.yml",
         "spring.profiles.active: native，search-locations: file:/config-repo",
         "YAML 放在容器内挂载进来的 /config-repo 目录。",
         "native 模式不需要 Git 服务器，配置和项目一起版本管理，但运行时才读取。"],
        ["docker-compose.yml（config-server）",
         "volumes: ./config-repo:/config-repo",
         "宿主目录 config-repo 变成容器里的 /config-repo。",
         "改一个配置只需要重启服务，不用重建任何镜像。"],
        ["product-service/application.yml",
         "spring.config.import: optional:configserver:http://config-server:8888",
         "optional 导入，配置中心挂了服务也能启动。",
         "这是配置中心的客户端一侧；本地 yml 里的默认值作为兜底。"],
    ], CAP_W))
    B.append(("img", "10-config-server.png",
              "图 3 — GET http://localhost:8888/product-service/default。返回里 propertySources 的名字是 "
              "file:/config-repo/product-service.yml，包含 server.port 8081、MySQL 数据源、"
              "spring.cache.type redis 和 Kafka 地址——就是运行中的容器实际用的那套值。"))

    B.append(("h2", "3.2 注册中心：按名字找服务"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "具体值", "为什么"],
        ["DiscoveryServerApplication", "@EnableEurekaServer", "server.port: 8761",
         "这一个注解就启动了注册中心和它的网页面板。"],
        ["discovery-server/application.yml",
         "eureka.client.register-with-eureka: false，fetch-registry: false",
         "它自己既不去注册，也不去拉注册表。",
         "不关这两个开关，注册中心会尝试注册自己并不断报错；它是服务端，不是客户端。"],
        ["每个服务的 application.yml",
         "spring.application.name + eureka.client.service-url.defaultZone: http://discovery-server:8761/eureka/",
         "例如名字 product-service，注册地址指向 discovery 容器。",
         "名字就是网关和 Feign 使用的键。因此重启、搬动、扩容一个服务，其他服务都不用改代码。"],
    ], CAP_W))

    B.append(("h2", "3.3 API 网关：一个入口 + 一个请求号"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "具体值", "为什么"],
        ["api-gateway/application.yml",
         "spring.cloud.gateway.routes，uri 用 lb://服务名，filter StripPrefix=1",
         "四条路由：/api/products/** → lb://product-service、/api/orders/** → lb://order-service、"
         "/api/carts/** → lb://cart-service、/api/search/** → lb://search-service。",
         "lb:// 表示按 Eureka 里的服务名负载均衡；StripPrefix=1 去掉 /api 前缀，"
         "服务内部保持 /products、/orders 这样的干净路径。"],
        ["XRequestIdFilter",
         "@Component，实现 GlobalFilter 与 Ordered，getOrder() 返回 -100",
         "读取请求头 X-Request-Id，没有就用 UUID 生成；写进转发请求并打日志。",
         "GlobalFilter 对每条路由都生效，-100 让它第一个执行。一个请求一个号，"
         "就能在网关和所有服务日志里串起同一次调用。"],
    ], CAP_W))
    B.append(("p",
              "这也是本报告里所有示例都用 8080 的原因：8081 到 8085 这些端口没有发布到宿主（见 2.1）。"))

    # ------------------------------------------------------------------ 4
    B.append(("break",))
    B.append(("h1", "4. Kafka——事件驱动的下单流程"))
    B.append(("p",
              "Kafka 用在一个服务需要通知其他服务、但又不该等它的地方。下单、扣库存、搜索索引、"
              "发通知是同一个业务事实的四个不同归属，所以用事件连接，而不是互相直接调 HTTP。"))

    B.append(("h2", "4.1 三个 Topic"))
    B.append(("table", [
        ["Topic", "生产者", "消费者（消费组）", "消息类型"],
        ["order-events", "order-service（OrderService.sendOrderEvent）",
         "product-service（组 product-service）、notification-service（组 notification-service）",
         "OrderPlaced、OrderConfirmed、OrderRejected"],
        ["inventory-events", "product-service（OrderEventListener）",
         "order-service（组 order-service）、notification-service",
         "StockReserved、StockRejected"],
        ["product-events", "product-service（ProductController）",
         "search-service（application.yml 里 group-id: search-service-group）",
         "ProductCreated、ProductUpdated、ProductDeleted"],
    ], [3.1 * cm, 4.6 * cm, 5.6 * cm, 3.5 * cm]))
    B.append(("p",
              "Topic 不是手工建的：product-service 里的 KafkaTopicConfig 用 @Configuration 和 "
              "@Bean NewTopic（TopicBuilder.name(topic).partitions(3).replicas(1)）声明。"
              "3 个分区对演示足够，也允许以后并行消费；单 broker 场景副本数只能是 1。"))

    B.append(("h2", "4.2 消息格式与 Key"))
    B.append(("code",
              "value = \"OrderPlaced:\" + JSON          // 先事件名，再消息体\n"
              "value = {\"orderId\":18,\"status\":\"PENDING\",\"items\":[{\"productId\":21,\"quantity\":2}]}\n"
              "key   = 订单号（order-events）或商品号（product-events）"))
    B.append(("p",
              "JSON 前面加一个事件名前缀，消费者不用解析就知道该做什么，代码非常简单。"
              "Key 用业务 id，同一个订单的所有事件落在同一个分区，天然按序消费。"))

    B.append(("h2", "4.3 谁在监听什么"))
    B.append(("table", [
        ["类", "注解", "内部做了什么", "为什么这样设计"],
        ["OrderEventListener（product-service）",
         "@KafkaListener(topics = \"order-events\", groupId = \"product-service\")",
         "读到 OrderPlaced 调 StockReservationService.reserve()，再往 inventory-events 发 "
         "StockReserved 或 StockRejected。",
         "库存归 product-service 所有，只有它能改。消费组让它的多个副本分摊分区，而不是重复处理。"],
        ["InventoryEventListener（order-service）",
         "@KafkaListener(topics = \"inventory-events\", groupId = \"order-service\")",
         "读到 StockReserved / StockRejected，调 OrderService.applyInventoryResult()。",
         "订单状态必须等库存结果回来才确定，这是正确的业务先后顺序。"],
        ["OrderNotificationListener（notification-service）",
         "两个 @KafkaListener 方法，分别监听 order-events 和 inventory-events，组 notification-service",
         "对 OrderConfirmed / OrderRejected 打印“邮件”块；库存事件只打一行日志。",
         "单独一个服务证明：新增消费者完全不用改生产者；它没有数据库、也不对外开端口。"],
        ["ProductEventListener（search-service）",
         "@KafkaListener(topics = \"product-events\")，组来自 application.yml 的 search-service-group",
         "ProductCreated / ProductUpdated → searchRepository.save(doc)；ProductDeleted → deleteById。",
         "搜索索引是商品数据的一份副本，所以只从事件重建，绝不由网关直接写。"],
    ], CAP_W))

    B.append(("h2", "4.4 消费者里的两个正确性问题"))
    B.append(("p",
              "第一，Kafka 可能把同一条消息投两次。StockReservationService 标了 @Transactional，"
              "扣库存前先用 processedOrderRepository.existsById(orderId) 判断，并在同一个事务里写入 "
              "ProcessedOrder 记录。重复的 OrderPlaced 只会打印“已处理过，跳过”，不会扣第二次。"))
    B.append(("p",
              "第二，两个订单可能同时到达。ProductRepository.reserveStock 是一条 @Modifying + @Query 的 "
              "SQL：update Product p set p.stock = p.stock - :quantity where p.id = :id and p.stock >= :quantity。"
              "条件由 MySQL 自己判断，库存不够时返回影响 0 行，服务抛 StockNotAvailableException，"
              "最终变成 StockRejected。中间不存在“先读后写”的空窗，库存不会变成负数。"))

    B.append(("img", "07-kafka-events.png",
              "图 4 — notification-service 的容器日志 + order-events 上的 Kafka 控制台消费者。"
              "日志里能看到 inventory-events、order-events 的分区分配，"
              "[通知服务] 收到库存事件 Key=18 StockReserved {\"orderId\":18}，以及订单 18 的邮件块（状态 CONFIRMED）；"
              "下面是消费到的 OrderPlaced 原始消息与 JSON 内容。"))

    # ------------------------------------------------------------------ 5
    B.append(("break",))
    B.append(("h1", "5. Elasticsearch——索引、同步与搜索查询"))

    B.append(("h2", "5.1 文档与映射"))
    B.append(("table", [
        ["字段", "注解", "为什么用这个类型"],
        ["class ProductDocument", "@Document(indexName = \"products\") + @Setting(replicas = 0)",
         "这个类就是索引。单节点上副本必须为 0，否则索引一直是 yellow。"],
        ["name、description", "@Field(type = FieldType.Text)",
         "全文检索：会被分词，所以搜 demo 能命中 Demo Book。"],
        ["category", "@Field(type = FieldType.Keyword)",
         "给 term 过滤器用的精确值；用 Text 会被分词，过滤结果就不对了。"],
        ["price", "@Field(type = FieldType.Double)", "给 minPrice / maxPrice 的数值范围过滤用。"],
        ["stock", "@Field(type = FieldType.Integer)", "数值字段，搜索结果里直接展示。"],
    ], [3.5 * cm, 5.4 * cm, 8.6 * cm]))

    B.append(("h2", "5.2 索引怎么保持最新"))
    B.append(("p",
              "product-service 是商品数据唯一的写入方。每次新增、修改、删除都往 product-events 发一条事件；"
              "search-service 的 ProductEventListener 消费它并调用 ProductSearchRepository（Spring Data "
              "Elasticsearch 仓库）。消费组是 search-service-group、auto-offset-reset 为 earliest，"
              "所以 search-service 重启后可以把历史重放一遍、重建索引。索引是派生数据，不是第二个真相源。"))

    B.append(("h2", "5.3 查询怎么拼"))
    B.append(("code",
              "BoolQuery.Builder boolQuery = new BoolQuery.Builder();\n"
              "text     -> boolQuery.must(multiMatch(fields \"name\",\"description\", BestFields))\n"
              "category -> boolQuery.filter(term(field \"category\"))\n"
              "price    -> boolQuery.filter(range(field \"price\").gte(min).lte(max))\n"
              "NativeQuery query = NativeQuery.builder().withQuery(...)\n"
              "        .withPageable(PageRequest.of(page, size)).build();\n"
              "elasticsearchOperations.search(query, ProductDocument.class)"))
    B.append(("p",
              "文本用 must，因为它影响相关度打分；分类和价格用 filter，因为它们是“是/不是”的条件，"
              "而且 filter 会被 ES 缓存。分页下推到查询里，服务不会把整个索引读进内存。"))

    B.append(("img", "09-es-search.png",
              "图 5 — 直接查 Elasticsearch：GET /products/_search?q=name:Demo。8 条命中、耗时 4 ms，"
              "返回的 _source 就是 ProductEventListener 写进去的 ProductDocument。"))
    B.append(("img", "11-postman-search.png",
              "图 6 — 走我自己的接口做同样的搜索：GET http://localhost:8080/api/search?text=Demo 返回 "
              "200 OK（1.03 KB）。这份结果由 SearchController 和上面的 BoolQuery 产生，"
              "说明网关、搜索服务、ES 三层一起工作正常。"))

    # ------------------------------------------------------------------ 6
    B.append(("break",))
    B.append(("h1", "6. Redis——商品缓存与购物车"))
    B.append(("p",
              "Redis 在这个项目里干两件不同的事：做 product-service 的缓存，以及做 cart-service 唯一的数据库。"))

    B.append(("h2", "6.1 商品缓存"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "为什么"],
        ["ProductServiceApplication", "@EnableCaching",
         "打开 Spring 的缓存抽象；不加这个注解 @Cacheable 完全不生效。"],
        ["ProductController.one()", "@Cacheable(value = \"products\", key = \"#id\")",
         "单商品接口每个商品页、每次下单都会被调用；有缓存后第二次不再查 MySQL。"],
        ["ProductController.update() / delete()", "@CacheEvict(value = \"products\", key = \"#id\")",
         "改过或删掉的商品不能留在缓存里。"],
        ["RedisConfig",
         "@Configuration + @Bean RedisCacheConfiguration，用 GenericJackson2JsonRedisSerializer",
         "值以可读 JSON 存，而不是 Java 序列化，这样我能用 redis-cli 直接看内容。"],
        ["application.yml",
         "spring.cache.type: redis + redis 的 host/port/password 来自环境变量",
         "缓存后端是 Redis 而不是默认的本地 Map，多个副本共享同一份缓存。"],
        ["StockReservationService.reserve()",
         "扣库存之后执行 cacheManager.getCache(\"products\").evict(productId)",
         "库存变化不经过 Controller，监听器必须自己清缓存，否则缓存里还是旧库存。"],
    ], CAP_W))

    B.append(("img", "08-redis-keys.png",
              "图 7 — 在 redis 容器里执行 redis-cli。products::1、::3、::16、::18、::21 是 "
              "@Cacheable 生成的商品缓存键；carts:101 是 @RedisHash 写的购物车，TTL 3584 秒，"
              "说明 @TimeToLive 设的 3600 秒确实生效。"))

    B.append(("h2", "6.2 购物车"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "为什么"],
        ["Cart", "@RedisHash(\"carts\")、@Id userId、@TimeToLive ttl = 3600",
         "购物车是临时数据且归属单一用户：存成 Redis 哈希，key 是用户 id，一小时后自动消失。"],
        ["CartRepository", "继承 CrudRepository", "Spring Data 负责读写这个哈希，不需要 SQL，也没有表结构。"],
        ["CartServiceApplication", "@EnableRedisRepositories",
         "必须开启，Spring 才会为 @RedisHash 实体生成仓库实现。"],
        ["CartService.addItem / checkout",
         "普通服务方法；结算时组装 item 列表交给 OrderClient",
         "业务规则是：先下单，order-service 返回 201 才删购物车；调用失败就保留购物车。"],
    ], CAP_W))

    B.append(("h2", "6.3 cart 与 order 之间的 Feign"))
    B.append(("table", [
        ["类 / 文件", "注解或配置项", "为什么"],
        ["OrderClient（cart-service）", "@FeignClient(name = \"order-service\") + @PostMapping(\"/orders\")",
         "声明式 HTTP 客户端：URL 就是服务名，具体实例由 Eureka 和负载均衡决定，代码里没有拼接主机和端口。"],
        ["CartServiceApplication", "@EnableFeignClients", "启动时生成 Feign 代理。"],
        ["OrderServiceApplication + ProductClient", "@EnableFeignClients、@FeignClient(name = \"product-service\")",
         "order-service 读商品价格用的是同一套写法。"],
    ], CAP_W))
    B.append(("p",
              "Feign 替代了我第一版“从环境变量拿 URL 再自己拼”的写法。Feign 版本代码更短，"
              "而且服务换了容器或端口也不用改。"))

    # ------------------------------------------------------------------ 7
    B.append(("break",))
    B.append(("h1", "7. 运行结果——一次完整链路"))
    B.append(("p",
              "下面是 2026 年 11 月 22 日 docker compose up -d 之后的一次真实运行记录，"
              "所有请求都走 8080 网关，没有手工往数据库里插任何数据。"))
    B.append(("table", [
        ["步骤", "请求", "实际结果"],
        ["1", "GET /api/products", "200 OK，17 条商品（图 8）"],
        ["2", "POST /api/products，body 为 {\"name\":\"Demo Book\",\"price\":19.90,\"stock\":10}",
         "201 Created，id 21（图 9）"],
        ["3", "POST /api/orders，body 为 {\"items\":[{\"productId\":21,\"quantity\":2}]}",
         "201 Created，订单 18，状态 PENDING，totalPrice 39.80（图 10）"],
        ["4", "几秒后 GET /api/orders/18", "200 OK，状态 CONFIRMED——Kafka 一来一回跑完了（图 11）"],
        ["5", "下单后 GET /api/products/21", "stock 8，说明原子更新真的扣掉了 2 件"],
        ["6", "GET /api/search?text=Demo 与 /products/_search?q=name:Demo",
         "8 条命中，耗时 4 ms（图 5、图 6）"],
        ["7", "redis-cli --scan --pattern 'products*' 与 TTL carts:101",
         "缓存键存在，购物车 TTL 3584 秒（图 7）"],
        ["8", "docker logs notification-service", "订单 18 的邮件日志，状态 CONFIRMED（图 4）"],
    ], [1.2 * cm, 7.6 * cm, 8.7 * cm]))

    B.append(("img", "03-postman-get-products.png",
              "图 8 — Postman 里 GET http://localhost:8080/api/products：200 OK、44 ms、1.96 KB，"
              "返回商品 JSON 数组。这是“网关 → product-service → MySQL”的读链路。"))
    B.append(("img", "04-postman-post-product.png",
              "图 9 — Postman 里 POST /api/products 带 JSON 请求体：201 Created、183 ms，返回落库后的实体 "
              "id 21。同一时刻它还往 product-events 发了 ProductCreated，所以图 6 能在 ES 里搜到它。"))
    B.append(("img", "05-postman-post-order.png",
              "图 10 — Postman 里 POST /api/orders 买 2 件商品 21：201 Created、915 ms，订单 18 状态 "
              "PENDING，totalPrice 39.80，unitPrice 19.90 是通过 Feign 从商品服务读到的。"))
    B.append(("img", "06-postman-order-confirmed.png",
              "图 11 — 几秒后在 Postman 里 GET /api/orders/18：200 OK，状态变成 CONFIRMED。"
              "这是 product-service 发出 StockReserved 后，InventoryEventListener 改的。"))

    # ------------------------------------------------------------------ 8
    B.append(("break",))
    B.append(("h1", "8. 遇到的问题与解决办法"))
    B.append(("table", [
        ["问题", "原因", "解决办法"],
        ["浏览器访问不到各服务的端口",
         "docker-compose.yml 只发布基础设施端口，服务只监听在 Docker 网络内部。",
         "所有流量走 8080 网关；报告里统一用 8080，映射由四条路由加 StripPrefix=1 完成。"],
        ["order-service 取商品价格不稳定",
         "第一版用环境变量里的 URL，服务一换位置就失效。",
         "改成 ProductClient 的 @FeignClient(name = \"product-service\") 加 @EnableFeignClients，"
         "由 Eureka 解析实例。"],
        ["并发下单时库存可能变负数",
         "先读库存再写库存，两步之间别的事务可能已经改了同一行。",
         "ProductRepository.reserveStock 用一条带 stock >= quantity 条件的原子 UPDATE，"
         "影响 0 行就拒单。"],
        ["同一个订单可能被处理两次",
         "Kafka 保证至少投递一次，消费者可能重复收到同一条消息。",
         "processed_orders 表：先 existsById 判断，再在同一个 @Transactional 方法里写入。"],
        ["缓存里显示的是旧库存",
         "库存是被 Kafka 监听器改的，没走 Controller，@CacheEvict 根本不会触发。",
         "StockReservationService 扣完库存后主动把该商品从 products 缓存里清掉。"],
        ["最终通知可能发两遍",
         "库存事件重复到达会导致再次发 OrderConfirmed。",
         "applyInventoryResult 里判断订单已是 CONFIRMED / REJECTED 就直接返回。"],
        ["在宿主上跑 kafka-console-consumer 收不到消息",
         "broker 对外宣告的地址是 kafka:9092，这个名字只在 Docker 网络里存在。",
         "在容器里跑：docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh ..."],
        ["Elasticsearch 索引一直是 yellow",
         "默认副本数是 1，但只有一个节点。",
         "ProductDocument 上加 @Setting(replicas = 0)。"],
    ], [4.3 * cm, 6.1 * cm, 6.6 * cm]))
    B.append(("p",
              "还有一个我知道并且能解释清楚的局限：ES 文档里的 stock 是发商品事件那一刻的值。"
              "扣库存只改 MySQL，所以索引可能落后几件；权威库存永远从 product-service 读。"
              "生产做法是扣完库存再发一个 StockChanged 事件，由 search-service 更新索引。"))

    # ------------------------------------------------------------------ 9
    B.append(("h1", "9. 如何启动项目"))
    B.append(("code",
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose up -d                       # 需要时自动构建，启动 14 个容器\n"
              "docker compose ps                          # 全部 Up，MySQL/ES healthy\n"
              "start http://localhost:8761                # Eureka 面板\n"
              "start http://localhost:3000                # 前端演示页\n\n"
              "# 走网关的接口示例\n"
              "curl http://localhost:8080/api/products\n"
              "curl -X POST http://localhost:8080/api/orders -H \"Content-Type: application/json\" ^\n"
              "     -d \"{\\\"items\\\":[{\\\"productId\\\":21,\\\"quantity\\\":2}]}\"\n"
              "curl http://localhost:8080/api/orders/18\n"
              "curl \"http://localhost:8080/api/search?text=Demo\"\n\n"
              "# 基础设施里的证据\n"
              "docker exec redis redis-cli -a mypass --scan --pattern 'products*'\n"
              "curl \"http://localhost:9200/products/_search?q=name:Demo&pretty\"\n"
              "docker logs -f shopstream-notification-service-1"))

    # ------------------------------------------------------------------ 10
    B.append(("break",))
    B.append(("h1", "10. 附录 A——注解速查表"))
    B.append(("p",
              "这一页是我自己的复习卡：项目里用到的每个注解、它在哪里、起什么作用。"
              "口试讲代码时我也按这个顺序讲。"))
    B.append(("table", [
        ["注解 / 接口", "位置", "作用"],
        ["@SpringBootApplication", "8 个服务的主类", "自动配置、组件扫描、启动入口"],
        ["@EnableEurekaServer", "DiscoveryServerApplication", "启动注册中心和网页面板"],
        ["@EnableConfigServer", "ConfigServerApplication", "提供 /{application}/{profile} 配置接口"],
        ["@EnableCaching", "ProductServiceApplication", "让 @Cacheable / @CacheEvict 生效"],
        ["@EnableRedisRepositories", "CartServiceApplication", "为 @RedisHash 实体生成仓库"],
        ["@EnableFeignClients", "order-service、cart-service", "生成 @FeignClient 代理"],
        ["@RestController + @RequestMapping", "ProductController、OrderController、CartController、SearchController",
         "HTTP 层；这里的路径前缀就是网关转发过来的路径"],
        ["@Cacheable(value, key) / @CacheEvict", "ProductController 的 one()、update()、delete()",
         "读穿透缓存；数据变更时清缓存"],
        ["@KafkaListener(topics, groupId)", "OrderEventListener、InventoryEventListener、OrderNotificationListener、ProductEventListener",
         "消费者方法；消费组决定副本之间是分摊还是各收一份"],
        ["@Document(indexName) / @Setting / @Field / @Id", "ProductDocument", "索引名、映射与文档 id"],
        ["@RedisHash(\"carts\") / @TimeToLive", "Cart", "Redis 哈希 key 空间与过期秒数"],
        ["@Entity / @Table / @Id / @GeneratedValue", "Product、Order", "JPA 表映射与自增主键"],
        ["@Modifying + @Query + @Param", "ProductRepository.reserveStock", "一条原子 UPDATE 取代先读后写"],
        ["@Transactional", "OrderService、StockReservationService、CartService", "一个工作单元，出错回滚"],
        ["@FeignClient(name) + @EnableFeignClients", "ProductClient、OrderClient", "按服务名调用的 HTTP 客户端"],
        ["@Component / @Service / @Configuration / @Bean", "过滤器、监听器、配置类", "声明 Spring Bean 和配置对象"],
        ["GlobalFilter + Ordered", "XRequestIdFilter", "对每条路由生效，order 为 -100 表示最先执行"],
    ], [4.6 * cm, 6.6 * cm, 5.8 * cm]))

    # ------------------------------------------------------------------ 11
    B.append(("break",))
    B.append(("h1", "11. 附录 B——口试演示脚本（八步台本）"))
    B.append(("p",
              "这一版按我个人学习笔记里的演示台本重写：一共八步，顺序不换，每一步都是“做一个操作 → "
              "让老师看到一处证据 → 我说一句英文”。练的时候照这八步走，手上不停、嘴上不停，"
              "比背整段解说更容易稳住。"))
    B.append(("table", [
        ["步", "我要做的操作", "老师看到什么", "我说什么"],
        ["1", "cd 到项目目录，docker compose up -d", "容器全部 Up", "All containers are up."],
        ["2", "浏览器打开 localhost:8761", "Eureka 面板上服务在册", "Services register here."],
        ["3", "Postman GET /api/products", "商品 JSON 数组", "GET products."],
        ["4", "Postman POST /api/products", "201 Created 加一个新的 id", "Create a product. POST."],
        ["5", "另开一个 PowerShell，跟随 search-service 日志，再回到第 4 步点 Send",
         "窗口自己冒出收到事件的日志", "It reads the Kafka event."],
        ["6", "Postman GET /api/search?text=Demo", "200 OK，命中刚建的商品", "Search goes to Elasticsearch."],
        ["7", "先清空 product-service 日志，再对同一商品连打两次 GET",
         "第一次有查库日志，第二次没有", "Redis cache."],
        ["8", "Postman POST /api/orders，再 GET /api/orders/{id}",
         "201 里的 totalPrice，随后能按 id 查回该单", "Feign gets the price."],
    ], [1.2 * cm, 6.2 * cm, 4.6 * cm, 5.0 * cm]))
    B.append(("p",
              "备注：第 2 步面板上实际是 7 个应用（6 个业务服务加 config-server），说 six services "
              "指的是业务服务；第 7、8 步里的商品 id 和订单 id 都用当场返回的真实数字，不要照抄这里的例子。"))

    B.append(("h2", "11.1 逐步操作与解说词"))
    B.append(("p", "第一步：启动全部容器。"))
    B.append(("code",
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose up -d\n"
              "docker compose ps          # 全部 Up 才算起来，两个 MySQL 和 ES 要 (healthy)"))
    B.append(("p", "解说：All containers are up.（所有容器都起来了。）"))

    B.append(("p", "第二步：打开 Eureka 面板。"))
    B.append(("code", "start http://localhost:8761\n"
                      "# 面板刷新一次约 30 秒，刚启动时可能还没列全"))
    B.append(("p", "解说：Services register here.（服务都在这里注册。）"))

    B.append(("p", "第三步：读取商品列表。"))
    B.append(("code", "GET http://localhost:8080/api/products     -> 200 OK，商品 JSON 数组"))
    B.append(("p",
              "如果老师问“它怎么走的”，就补一句：请求先到网关，网关按路由找到 product-service，"
              "再由它读 MySQL 返回 JSON。解说：GET products."))

    B.append(("p", "第四步：新建一个商品。"))
    B.append(("code",
              "POST http://localhost:8080/api/products\n"
              "Body -> raw -> JSON：\n"
              "{\n"
              "  \"name\": \"Demo Book\",\n"
              "  \"description\": \"Created during the demo\",\n"
              "  \"category\": \"book\",\n"
              "  \"price\": 19.90,\n"
              "  \"stock\": 10\n"
              "}"))
    B.append(("p",
              "点 Send 看到 201 Created，记下返回的 id（后面两步要用）。"
              "解说：Create a product. POST."))

    B.append(("p", "第五步：证明写入事件真的进了 Kafka。"))
    B.append(("code",
              "# 另开一个 PowerShell 窗口，让它挂着等日志\n"
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose logs --tail 5 -f search-service\n"
              "# 窗口别关，切回 Postman，把第 4 步那个 POST 再点一次 Send"))
    B.append(("p",
              "一两秒内那个窗口会自己冒出 search-service 收到 product-events 的日志。"
              "解说：It reads the Kafka event.（它读取了这条 Kafka 事件。）"))

    B.append(("p", "第六步：用搜索接口找到刚建的商品。"))
    B.append(("code", "GET http://localhost:8080/api/search?text=Demo      -> 200 OK，命中 Demo Book"))
    B.append(("p",
              "解说：Search goes to Elasticsearch.（搜索走的是 Elasticsearch，不是 MySQL。）"))

    B.append(("p", "第七步：证明 Redis 缓存真的生效。"))
    B.append(("code",
              "# 1. 打开 Docker Desktop -> 找到 product-service-1 -> 标签 Logs -> 先把日志清空\n"
              "# 2. 回到 Postman，GET 同一件商品两次：\n"
              "GET http://localhost:8080/api/products/{刚才返回的 id}\n"
              "GET http://localhost:8080/api/products/{同一个 id}"))
    B.append(("p",
              "第一次在 Logs 里会看到查库的那几行，第二次没有——说明第二次是从 Redis 拿的。"
              "反过来，如果第二次还有查库日志，那就说明缓存没生效，这一步算失败。"
              "解说：Redis cache."))

    B.append(("p", "第八步：下单，再查单——验证 order-service 的订单链路。"))
    B.append(("p",
              "这一步分两下：先下单，再查单。有一处和我最早的笔记不一样：POST 一定返回 PENDING，"
              "这是异步设计，接口不会等 Kafka 回来；隔一两秒再 GET 才会看到 CONFIRMED。"))
    B.append(("table", [
        ["原来笔记写的", "最新代码下的实际行为"],
        ["POST /api/orders → 201，状态 PENDING，totalPrice 39.80", "一致，没有变"],
        ["GET /api/orders/{id} → 返回同样的 PENDING", "几秒后返回 CONFIRMED"],
    ], [8.5 * cm, 8.5 * cm]))
    B.append(("p", "① 先新建一个商品，库存（stock）填 11。选择 Body → raw → JSON："))
    B.append(("code",
              "POST http://localhost:8080/api/products\n"
              "{\n"
              "  \"name\": \"Demo Book\",\n"
              "  \"description\": \"Created during the demo\",\n"
              "  \"category\": \"book\",\n"
              "  \"price\": 19.90,\n"
              "  \"stock\": 11\n"
              "}"))
    B.append(("p",
              "点 Send 拿到 201，把返回体里的 id 记下来（我这轮是 24）。"
              "下一步的 productId 必须填这个新 id，填错了就会因为库存不足被判 REJECTED。"))
    B.append(("p", "② 模拟下单：新建请求，POST，Body → raw → JSON："))
    B.append(("code",
              "POST http://localhost:8080/api/orders\n"
              "{\n"
              "  \"items\": [\n"
              "    {\n"
              "      \"productId\": 24,\n"
              "      \"quantity\": 2\n"
              "    }\n"
              "  ]\n"
              "}"))
    B.append(("p",
              "点 Send，返回 201，订单号 47，状态 PENDING，totalPrice 39.80，unitPrice 19.90。"
              "请求体里没有价格，39.80 是 order-service 用 Feign 去 product-service 读到单价后自己算的。"))
    B.append(("code",
              "{\n"
              "  \"id\": 47,\n"
              "  \"status\": \"PENDING\",\n"
              "  \"totalPrice\": 39.80,\n"
              "  \"items\": [\n"
              "    { \"id\": 47, \"productId\": 24, \"quantity\": 2, \"unitPrice\": 19.90 }\n"
              "  ]\n"
              "}"))
    B.append(("p", "③ 再查这张单：把同一个页签改成 GET，URL 换成刚返回的订单号。"))
    B.append(("code",
              "GET http://localhost:8080/api/orders/47\n"
              "-> 200 OK，\"status\": \"CONFIRMED\"（已确认）"))
    B.append(("p",
              "看到 CONFIRMED 就说明 Kafka 那边已经跑完：OrderPlaced 发出、库存被原子扣减、"
              "StockReserved 回传、订单状态被改写。这一步的解说词是：Feign gets the price. "
              "然后补一句：Now it is CONFIRMED.（现在是已确认。）"))

    B.append(("h2", "11.2 听不懂问题时的救场句"))
    B.append(("code",
              "Sorry, could you repeat the question?\n"
              "Do you mean the order service?\n"
              "Can I show you the code instead?\n"
              "I am not sure. Let me check.\n"
              "Can you speak a little slowly, please?"))

    B.append(("h2", "11.3 演示前的检查清单"))
    B.append(("bullets", [
        "提前 10 分钟执行 docker compose up -d，等两个 MySQL 和 Elasticsearch 都 (healthy) 再开始，"
        "否则第一次请求会失败。",
        "商品 id 和订单 id 每次演示都可能变：先 GET /api/products 看当前真实 id，"
        "订单 id 用 201 响应里返回的那个。",
        "第七步一定要先清空 product-service 的日志再打第二次，否则分不出哪几行是哪一次请求的。",
        "第五步和第七步各需要一个额外的 PowerShell 窗口，提前开好，演示时不用手忙脚乱。",
        "练三遍到不用看稿；先练手上的操作，再练嘴上的句子，两者都顺了再合起来。",
    ]))
    return B
