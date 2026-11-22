"""English content of the ShopStream final report."""
from reportlab.lib.units import cm

SERVICE_W = [3.0 * cm, 1.15 * cm, 4.7 * cm, 7.95 * cm]
CAP_W = [4.3 * cm, 4.2 * cm, 4.35 * cm, 4.35 * cm]
TWIN_W = [7.2 * cm, 9.6 * cm]


def blocks():
    B = []
    B.append((
        "titlepage",
        "ShopStream — Distributed E-Commerce Platform",
        "Final Project · Experimental Report",
        [
            "Student: Xu Haojie (Neptun code: DTR5N0)",
            "University of Miskolc · Faculty of Information Technology",
            "Course: Web / Distributed Systems — Final Project",
            "Instructor: Atallah Fadi",
            "Date: 22 November 2026 · Submission deadline: 4 December 2026",
            "Oral presentation: 9 December 2026",
        ],
    ))

    B.append(("h1", "Contents"))
    for line in [
        "1. What the system is — overview and architecture",
        "2. Docker — how the platform is containerised",
        "3. Spring Cloud — Config Server, Discovery Server, API Gateway",
        "4. Kafka — the event-driven order flow",
        "5. Elasticsearch — index, synchronisation and search queries",
        "6. Redis — product cache and shopping cart",
        "7. Results — one complete run of the system",
        "8. Problems and how I solved them",
        "9. How to start the project",
        "10. Appendix A — annotation quick reference",
        "11. Appendix B — demo script for the oral exam",
    ]:
        B.append(("p", line))
    B.append(("break",))

    # ------------------------------------------------------------------ 1
    B.append(("h1", "1. What the system is — overview and architecture"))
    B.append(("p",
              "ShopStream is an online shop built from eight Spring Boot applications that run as "
              "fourteen Docker containers. A client calls only one address — the API gateway on port "
              "8080. The gateway looks the target service up in Eureka and forwards the request. The "
              "services never use fixed IP addresses: they find each other by service name "
              "(Eureka + Feign), they exchange business events through Kafka, and they keep fast, "
              "temporary data in Redis. The front end is a small React page served by nginx; my own "
              "work in this project is the backend — the services, the event flow and the "
              "infrastructure."))

    B.append(("h2", "1.1 Services and responsibilities"))
    B.append(("table", [
        ["Service", "Port", "Storage / technology", "Responsibility"],
        ["api-gateway", "8080", "Spring Cloud Gateway", "Single entry point, routing by path, X-Request-Id filter"],
        ["discovery-server", "8761", "Eureka Server", "Service registry; every other service registers here"],
        ["config-server", "8888", "Spring Cloud Config (native profile)", "Serves the YAML files stored in config-repo"],
        ["product-service", "8081", "MySQL + Redis cache + Kafka", "Product CRUD, stock reservation, publishes product-events"],
        ["order-service", "8082", "MySQL + Kafka + Feign", "Creates orders, reads price from product-service, keeps status"],
        ["cart-service", "8083", "Redis", "One cart per user, TTL 1 hour; checkout calls order-service with Feign"],
        ["search-service", "8084", "Elasticsearch + Kafka", "Consumes product-events, writes the index, serves /search"],
        ["notification-service", "8085", "Kafka only, no database", "Consumes order/inventory events, writes the e-mail log"],
        ["frontend", "3000", "React build + nginx", "Demo page, proxies /api to the gateway"],
    ], SERVICE_W))

    B.append(("h2", "1.2 Two paths through the system"))
    B.append(("p",
              "Read path: browser → gateway 8080 → Eureka lookup → product-service 8081 → MySQL, "
              "with a Redis cache in front of the single-product endpoint."))
    B.append(("p",
              "Order path: POST /api/orders → order-service (Feign call to product-service to read the "
              "price) → order saved as PENDING → OrderPlaced published to Kafka → product-service "
              "reserves the stock and publishes StockReserved → order-service changes the order to "
              "CONFIRMED and publishes OrderConfirmed → notification-service prints the e-mail log. "
              "In parallel every product change is published to product-events and search-service "
              "copies it into Elasticsearch."))

    B.append(("img", "02-eureka.png",
              "Figure 1 — Eureka dashboard (http://localhost:8761). Seven applications are registered and UP: "
              "API-GATEWAY 8080, CART-SERVICE 8083, CONFIG-SERVER 8888, NOTIFICATION-SERVICE 8085, "
              "ORDER-SERVICE 8082, PRODUCT-SERVICE 8081, SEARCH-SERVICE 8084."))

    # ------------------------------------------------------------------ 2
    B.append(("break",))
    B.append(("h1", "2. Docker — how the platform is containerised"))
    B.append(("p",
              "Everything the project needs is a container: the seven services, the gateway, the front "
              "end, two MySQL servers, Kafka, Elasticsearch and Redis. This is the reason the whole "
              "system can be started on another computer with one command and no manual installation."))

    B.append(("h2", "2.1 What I wrote and why"))
    B.append(("table", [
        ["File / setting", "What it does", "Why I used it"],
        ["docker-compose.yml",
         "Defines the 14 containers of the project: build context, image, ports, environment, "
         "volumes, healthchecks and start order.",
         "One file describes the whole system, so a teammate or the teacher can reproduce my "
         "environment exactly with docker compose up -d."],
        ["Dockerfile in every service (multi-stage)",
         "Stage 1 uses maven:3.9.9-eclipse-temurin-21 to build the jar; stage 2 copies only the jar "
         "into eclipse-temurin:21-jre.",
         "The build happens inside the container, so no local Maven or JDK is required, and the "
         "runtime image stays small because the source code and Maven cache are not copied."],
        ["environment: SPRING_DATASOURCE_URL = jdbc:mysql://product-mysql:3306/productdb",
         "Passes the database address to the service as an environment variable.",
         "The host name is the container name; Docker DNS resolves it. No IP address is written in "
         "the code, so the same image works on any machine."],
        ["healthcheck (mysqladmin ping, curl /_cluster/health)",
         "Docker repeats a small command until the database or Elasticsearch is really ready.",
         "Hibernate and the Elasticsearch client must not start against a database that is still "
         "initialising; the healthcheck makes the start deterministic."],
        ["depends_on with condition: service_healthy / service_started",
         "product-service waits for product-mysql (healthy), kafka, redis and config-server; "
         "search-service waits for elasticsearch (healthy).",
         "Start order is a real dependency here: a consumer that starts before Kafka loses the "
         "first messages, and JPA fails if MySQL is not ready."],
        ["volumes: product-mysql-data, order-mysql-data, ./config-repo:/config-repo",
         "Named volumes keep the database files; a bind mount gives config-server the YAML files.",
         "Data must survive docker compose down, and configuration should be editable on the host "
         "without rebuilding an image."],
        ["ports: only 8080, 8761, 8888, 9200, 16379, 9092, 3000 are published",
         "product-service (8081), order-service (8082), cart-service (8083), search-service (8084) "
         "and notification-service (8085) are only visible inside the Docker network.",
         "The gateway is the only public entrance. This is how a real deployment looks: internal "
         "services must not be reachable from outside."],
    ], CAP_W))

    B.append(("h2", "2.2 Result"))
    B.append(("img", "01-containers.png",
              "Figure 2 — docker compose ps inside F:\\Final Project\\ShopStream. All 14 containers are Up, "
              "the three MySQL/Elasticsearch containers report (healthy), and the published ports show the "
              "policy of section 2.1: only infrastructure is exposed."))
    B.append(("p",
              "The image is built once; after that docker compose up -d starts the full stack in about "
              "one minute, which is what I use at the beginning of every test session."))

    # ------------------------------------------------------------------ 3
    B.append(("break",))
    B.append(("h1", "3. Spring Cloud — Config Server, Discovery Server, API Gateway"))
    B.append(("p",
              "Three Spring Cloud components make the services independent of each other's location "
              "and configuration."))

    B.append(("h2", "3.1 Config Server — one place for configuration"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Configuration", "Why"],
        ["ConfigServerApplication",
         "@SpringBootApplication + @EnableConfigServer",
         "server.port: 8888",
         "@EnableConfigServer turns the application into a configuration server that answers "
         "GET /{application}/{profile}."],
        ["config-server/application.yml",
         "spring.profiles.active: native, spring.cloud.config.server.native.search-locations: file:/config-repo",
         "The YAML files live in the mounted folder /config-repo inside the container.",
         "The native profile needs no Git server, so the configuration is versioned together with the "
         "project and still read at run time."],
        ["docker-compose.yml (config-server)",
         "volumes: ./config-repo:/config-repo",
         "The host folder config-repo becomes /config-repo in the container.",
         "I can change a property and only restart the services, without rebuilding any image."],
        ["product-service/application.yml",
         "spring.config.import: optional:configserver:http://config-server:8888",
         "Optional import, so the service also starts if the config server is down.",
         "This is the client side of the central configuration; the default values stay in the local "
         "file as a fallback."],
    ], CAP_W))
    B.append(("img", "10-config-server.png",
              "Figure 3 — GET http://localhost:8888/product-service/default. The response shows "
              "propertySources name file:/config-repo/product-service.yml with server.port 8081, the MySQL "
              "datasource, spring.cache.type redis and the Kafka bootstrap servers — the same values the "
              "running container uses."))

    B.append(("h2", "3.2 Discovery Server — services find each other by name"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Configuration", "Why"],
        ["DiscoveryServerApplication", "@EnableEurekaServer", "server.port: 8761",
         "This single annotation starts the registry and its web dashboard."],
        ["discovery-server/application.yml", "eureka.client.register-with-eureka: false, fetch-registry: false",
         "The server does not register itself and does not download a registry.",
         "Without these two flags the registry tries to register itself and logs errors; it is the "
         "server, not a client."],
        ["Every service application.yml", "spring.application.name + eureka.client.service-url.defaultZone: http://discovery-server:8761/eureka/",
         "For example name product-service, zone pointing to the discovery container.",
         "The name is the key that the gateway and Feign use. Because of it I can restart, move or "
         "duplicate a service and no other service needs a code change."],
    ], CAP_W))

    B.append(("h2", "3.3 API Gateway — one entrance and one request id"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Configuration", "Why"],
        ["api-gateway/application.yml", "spring.cloud.gateway.routes with uri lb://service-name and filter StripPrefix=1",
         "Four routes: /api/products/** → lb://product-service, /api/orders/** → lb://order-service, "
         "/api/carts/** → lb://cart-service, /api/search/** → lb://search-service.",
         "lb:// means load balanced by service name from Eureka. StripPrefix=1 removes the /api part, "
         "so the services keep clean paths such as /products and /orders."],
        ["XRequestIdFilter", "@Component, implements GlobalFilter and Ordered, getOrder() returns -100",
         "Reads the header X-Request-Id or creates a UUID, writes it into the forwarded request and "
         "logs it.",
         "GlobalFilter runs for every route, and -100 makes it the first filter. One id per request "
         "means I can follow the same request through the gateway and all service logs."],
    ], CAP_W))
    B.append(("p",
              "The gateway is also the reason why every example in this report uses port 8080 even for "
              "services that listen on 8081 to 8085: those ports are not published to the host (see "
              "section 2.1)."))

    # ------------------------------------------------------------------ 4
    B.append(("break",))
    B.append(("h1", "4. Kafka — the event-driven order flow"))
    B.append(("p",
              "Kafka is used where one service must inform others without waiting for them. Ordering, "
              "stock reservation, search indexing and the e-mail notification are four different "
              "owners of the same business fact, so they are connected by events instead of direct "
              "HTTP calls."))

    B.append(("h2", "4.1 Topics"))
    B.append(("table", [
        ["Topic", "Producer", "Consumers (group)", "Payload"],
        ["order-events", "order-service (OrderService.sendOrderEvent)",
         "product-service (groupId product-service), notification-service (groupId notification-service)",
         "OrderPlaced, OrderConfirmed, OrderRejected"],
        ["inventory-events", "product-service (OrderEventListener)",
         "order-service (groupId order-service), notification-service",
         "StockReserved, StockRejected"],
        ["product-events", "product-service (ProductController)",
         "search-service (spring.kafka.consumer.group-id search-service-group)",
         "ProductCreated, ProductUpdated, ProductDeleted"],
    ], [3.1 * cm, 4.6 * cm, 5.6 * cm, 3.5 * cm]))
    B.append(("p",
              "The topics are not created by hand: KafkaTopicConfig in product-service declares them "
              "with @Configuration and @Bean NewTopic built by TopicBuilder.name(topic)"
              ".partitions(3).replicas(1). Three partitions are enough for the demo but already allow "
              "parallel consumers; replication factor 1 is correct for a single broker."))

    B.append(("h2", "4.2 Message format and keys"))
    B.append(("code",
              "value = \"OrderPlaced:\" + JSON          // event name, then the body\n"
              "value = {\"orderId\":18,\"status\":\"PENDING\",\"items\":[{\"productId\":21,\"quantity\":2}]}\n"
              "key   = order id (order-events) or product id (product-events)"))
    B.append(("p",
              "One string in front of the JSON keeps the consumer simple: it reads the prefix and "
              "decides what to do before parsing the body. The key is the business id, so all events "
              "of one order go to the same partition and are consumed in order."))

    B.append(("h2", "4.3 Who listens to what"))
    B.append(("table", [
        ["Class", "Annotation", "What happens inside", "Why this design"],
        ["OrderEventListener (product-service)",
         "@KafkaListener(topics = \"order-events\", groupId = \"product-service\")",
         "Reads OrderPlaced, calls StockReservationService.reserve(), then sends StockReserved or "
         "StockRejected to inventory-events.",
         "product-service owns the stock, so only it may change the stock. The group id makes every "
         "replica of product-service share the partitions instead of duplicating the work."],
        ["InventoryEventListener (order-service)",
         "@KafkaListener(topics = \"inventory-events\", groupId = \"order-service\")",
         "Reads StockReserved / StockRejected and calls OrderService.applyInventoryResult().",
         "The order status is decided after the stock answer arrives, which is the correct order of "
         "business steps."],
        ["OrderNotificationListener (notification-service)",
         "Two @KafkaListener methods, topics order-events and inventory-events, groupId notification-service",
         "Prints the e-mail block for OrderConfirmed / OrderRejected and logs every inventory event.",
         "A separate service proves that a new consumer can be added without touching the producers; "
         "it has no database and no published port."],
        ["ProductEventListener (search-service)",
         "@KafkaListener(topics = \"product-events\") + group-id search-service-group in application.yml",
         "ProductCreated / ProductUpdated → searchRepository.save(doc); ProductDeleted → deleteById.",
         "The search index is a copy of the product data, so it is rebuilt from events and never "
         "written by the gateway."],
    ], CAP_W))

    B.append(("h2", "4.4 Two correctness problems inside the consumer"))
    B.append(("p",
              "First, Kafka can deliver the same message twice. StockReservationService is annotated "
              "@Transactional and checks processedOrderRepository.existsById(orderId) before any "
              "update; it saves a ProcessedOrder row in the same transaction. A repeated OrderPlaced "
              "therefore prints the skip message and does not deduct twice."))
    B.append(("p",
              "Second, two orders can arrive at the same moment. ProductRepository.reserveStock is a "
              "single statement with @Modifying and @Query: update Product p set p.stock = p.stock - "
              ":quantity where p.id = :id and p.stock >= :quantity. The condition is evaluated by MySQL "
              "itself, so the update returns 0 when the stock is too small and the service throws "
              "StockNotAvailableException, which becomes StockRejected. There is no read-then-write window "
              "in which the stock could go negative."))

    B.append(("img", "07-kafka-events.png",
              "Figure 4 — Docker logs of notification-service plus a Kafka console consumer on order-events. "
              "The log shows the partition assignment for inventory-events and order-events, the line "
              "[notification] inventory event Key=18 StockReserved {\"orderId\":18}, and the e-mail block "
              "for order 18 with status CONFIRMED. The consumer output shows the stored OrderPlaced "
              "message with its JSON body."))

    # ------------------------------------------------------------------ 5
    B.append(("break",))
    B.append(("h1", "5. Elasticsearch — index, synchronisation and search queries"))

    B.append(("h2", "5.1 The document and the mapping"))
    B.append(("table", [
        ["Field", "Annotation", "Why this type"],
        ["class ProductDocument", "@Document(indexName = \"products\") + @Setting(replicas = 0)",
         "The class is the index. replicas 0 is required on a single node, otherwise the index stays yellow."],
        ["name, description", "@Field(type = FieldType.Text)",
         "Full text: analysed, split into words, so a search for \"demo\" finds \"Demo Book\"."],
        ["category", "@Field(type = FieldType.Keyword)",
         "Exact value for a term filter; a Text field would be analysed and the filter would be wrong."],
        ["price", "@Field(type = FieldType.Double)",
         "Numeric range filter minPrice / maxPrice."],
        ["stock", "@Field(type = FieldType.Integer)", "Numeric field, shown in the search result."],
    ], [3.5 * cm, 5.4 * cm, 8.6 * cm]))

    B.append(("h2", "5.2 How the index is kept up to date"))
    B.append(("p",
              "product-service is the only writer of product data. Every create, update and delete "
              "publishes an event to product-events; ProductEventListener in search-service consumes it "
              "and calls the ProductSearchRepository (a Spring Data Elasticsearch repository). "
              "Because the consumer group is search-service-group with auto-offset-reset earliest, a "
              "restarted search-service can replay the history and rebuild the index. The index is "
              "therefore derived data, not a second source of truth."))

    B.append(("h2", "5.3 The query"))
    B.append(("code",
              "BoolQuery.Builder boolQuery = new BoolQuery.Builder();\n"
              "text     -> boolQuery.must(multiMatch(fields \"name\",\"description\", BestFields))\n"
              "category -> boolQuery.filter(term(field \"category\"))\n"
              "price    -> boolQuery.filter(range(field \"price\").gte(min).lte(max))\n"
              "NativeQuery query = NativeQuery.builder().withQuery(...)\n"
              "        .withPageable(PageRequest.of(page, size)).build();\n"
              "elasticsearchOperations.search(query, ProductDocument.class)"))
    B.append(("p",
              "must is used for the text because the relevance score matters; filter is used for "
              "category and price because they are yes/no conditions and filters are cached by "
              "Elasticsearch. Paging is pushed into the query, so the service does not load the whole "
              "index into memory."))

    B.append(("img", "09-es-search.png",
              "Figure 5 — Direct query to Elasticsearch: GET /products/_search?q=name:Demo. Total 8 hits in "
              "4 ms, and the returned _source is the ProductDocument written by ProductEventListener."))
    B.append(("img", "11-postman-search.png",
              "Figure 6 — The same search through my own API: GET http://localhost:8080/api/search?text=Demo "
              "returns 200 OK (1.03 KB body). The list is produced by SearchController and the BoolQuery "
              "above, i.e. the gateway, the search service and Elasticsearch all work together."))

    # ------------------------------------------------------------------ 6
    B.append(("break",))
    B.append(("h1", "6. Redis — product cache and shopping cart"))
    B.append(("p",
              "Redis has two different jobs in this project: it is the cache of product-service and it "
              "is the only database of cart-service."))

    B.append(("h2", "6.1 Product cache"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Why"],
        ["ProductServiceApplication", "@EnableCaching", "Turns on the Spring cache abstraction; without it @Cacheable is ignored."],
        ["ProductController.one()", "@Cacheable(value = \"products\", key = \"#id\")",
         "The single-product endpoint is called on every product page and by order-service; with the "
         "cache the second call does not touch MySQL."],
        ["ProductController.update() / delete()", "@CacheEvict(value = \"products\", key = \"#id\")",
         "A changed or deleted product must not stay in the cache."],
        ["RedisConfig", "@Configuration + @Bean RedisCacheConfiguration with GenericJackson2JsonRedisSerializer",
         "Values are stored as readable JSON instead of Java serialisation, so I can inspect them with redis-cli."],
        ["application.yml", "spring.cache.type: redis + spring.data.redis.host/port/password from environment",
         "The cache backend is Redis, not the default in-memory map, so all replicas see the same cache."],
        ["StockReservationService.reserve()", "cacheManager.getCache(\"products\").evict(productId) after the update",
         "Stock changes do not pass through the controller, so the listener must evict as well; otherwise "
         "the cached product would show the old stock."],
    ], CAP_W))

    B.append(("img", "08-redis-keys.png",
              "Figure 7 — redis-cli inside the redis container. products::1, ::3, ::16, ::18 and ::21 are the "
              "cached product entries created by @Cacheable; carts:101 is a cart written with @RedisHash and "
              "TTL 3584 seconds, which proves the @TimeToLive value of 3600 seconds is applied."))

    B.append(("h2", "6.2 Shopping cart"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Why"],
        ["Cart", "@RedisHash(\"carts\"), @Id userId, @TimeToLive ttl = 3600",
         "A cart is temporary data with one owner; it is stored as a Redis hash whose key is the user id "
         "and it disappears by itself after one hour."],
        ["CartRepository", "extends CrudRepository", "Spring Data writes and reads the hash; no SQL and no schema."],
        ["CartServiceApplication", "@EnableRedisRepositories", "Needed to generate the repository implementation for @RedisHash entities."],
        ["CartService.addItem / checkout", "Plain service methods; checkout builds the item list and calls OrderClient",
         "The business rule is: send the order first, delete the cart only when order-service answers 201; "
         "if the call fails the cart is kept."],
    ], CAP_W))

    B.append(("h2", "6.3 Feign between cart and order"))
    B.append(("table", [
        ["Class / file", "Annotation or setting", "Why"],
        ["OrderClient (cart-service)", "@FeignClient(name = \"order-service\") with @PostMapping(\"/orders\")",
         "A declarative HTTP client: the URL is the service name, so Eureka and the load balancer decide "
         "the instance. No string concatenation of host and port anywhere."],
        ["CartServiceApplication", "@EnableFeignClients", "Creates the Feign proxy at start-up."],
        ["OrderServiceApplication + ProductClient", "@EnableFeignClients, @FeignClient(name = \"product-service\")",
         "The same pattern is used by order-service to read the price of a product."],
    ], CAP_W))
    B.append(("p",
              "In this project Feign replaces the first version where I called the product service through "
              "a URL taken from an environment variable. The Feign version is shorter and survives a "
              "service that moves to another container or port."))

    # ------------------------------------------------------------------ 7
    B.append(("break",))
    B.append(("h1", "7. Results — one complete run of the system"))
    B.append(("p",
              "The following table is one run on 22 November 2026 after docker compose up -d, all calls "
              "through the gateway on port 8080. Nothing was inserted into the databases by hand."))
    B.append(("table", [
        ["Step", "Request", "Observed result"],
        ["1", "GET /api/products", "200 OK, list of 17 products (figure 8)"],
        ["2", "POST /api/products with {\"name\":\"Demo Book\",\"price\":19.90,\"stock\":10}",
         "201 Created, id 21 (figure 9)"],
        ["3", "POST /api/orders with {\"items\":[{\"productId\":21,\"quantity\":2}]}",
         "201 Created, order 18, status PENDING, totalPrice 39.80 (figure 10)"],
        ["4", "GET /api/orders/18 a few seconds later",
         "200 OK, status CONFIRMED — the Kafka round trip finished (figure 11)"],
        ["5", "GET /api/products/21 after the order",
         "stock 8, i.e. 2 units were reserved by the atomic update"],
        ["6", "GET /api/search?text=Demo and /products/_search?q=name:Demo",
         "8 documents, took 4 ms (figures 5 and 6)"],
        ["7", "redis-cli --scan --pattern 'products*' and TTL carts:101",
         "products::21 cached, cart TTL 3584 s (figure 7)"],
        ["8", "docker logs notification-service",
         "e-mail log for order 18 with status CONFIRMED (figure 4)"],
    ], [1.2 * cm, 7.6 * cm, 8.7 * cm]))

    B.append(("img", "03-postman-get-products.png",
              "Figure 8 — Postman, GET http://localhost:8080/api/products: 200 OK, 44 ms, 1.96 KB, JSON array of "
              "products. This is the read path gateway → product-service → MySQL."))
    B.append(("img", "04-postman-post-product.png",
              "Figure 9 — Postman, POST /api/products with a JSON body: 201 Created, 183 ms, the saved entity "
              "with id 21. The same request published ProductCreated to product-events, which is why the "
              "document appears in Elasticsearch in figure 6."))
    B.append(("img", "05-postman-post-order.png",
              "Figure 10 — Postman, POST /api/orders for 2 units of product 21: 201 Created, 915 ms, order 18 "
              "with status PENDING, totalPrice 39.80 and unitPrice 19.90 read through Feign."))
    B.append(("img", "06-postman-order-confirmed.png",
              "Figure 11 — Postman, GET /api/orders/18 a few seconds later: 200 OK, status CONFIRMED. The order "
              "was changed by InventoryEventListener after product-service published StockReserved."))

    # ------------------------------------------------------------------ 8
    B.append(("break",))
    B.append(("h1", "8. Problems and how I solved them"))
    B.append(("table", [
        ["Problem", "Cause", "Solution"],
        ["The service ports were not reachable from the browser",
         "Only infrastructure ports are published in docker-compose.yml, the services listen inside the network.",
         "All traffic goes through the gateway on 8080; the report uses 8080 everywhere, and the mapping is "
         "done by the four routes with StripPrefix=1."],
        ["order-service could not get the product price reliably",
         "The first version used a URL from an environment variable, which breaks when the service moves.",
         "I introduced ProductClient with @FeignClient(name = \"product-service\") and @EnableFeignClients, "
         "so Eureka resolves the instance."],
        ["Stock could become negative under two simultaneous orders",
         "Read the stock, then write it: between the two steps another transaction can change the row.",
         "One atomic statement in ProductRepository.reserveStock with the condition stock >= quantity; "
         "0 updated rows means reject."],
        ["The same order could be processed twice",
         "Kafka guarantees at-least-once delivery, so a consumer can see the same record again.",
         "processed_orders table: existsById before the update, save in the same @Transactional method."],
        ["The cached product showed the old stock",
         "The stock is changed by the Kafka listener, not by the controller, so @CacheEvict never ran.",
         "StockReservationService evicts the product from the products cache after the update."],
        ["A duplicate final notification was possible",
         "OrderConfirmed could be sent again if the inventory event arrived twice.",
         "applyInventoryResult returns early when the order is already CONFIRMED or REJECTED."],
        ["kafka-console-consumer on the host saw no messages",
         "The broker advertises itself as kafka:9092, a name that only exists inside the Docker network.",
         "I run the consumer inside the container: docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh ..."],
        ["Elasticsearch index stayed yellow",
         "The default number of replicas is 1, but there is only one node.",
         "@Setting(replicas = 0) on ProductDocument."],
    ], [4.3 * cm, 6.1 * cm, 6.6 * cm]))
    B.append(("p",
              "One limitation I know and can explain: the Elasticsearch document keeps the stock value "
              "that was current when the product event was published. The stock reservation updates "
              "MySQL only, so the index can be a few units behind; the authoritative stock is always "
              "read from product-service. A production version would publish a StockChanged event after "
              "the reservation and index it in search-service."))

    # ------------------------------------------------------------------ 9
    B.append(("h1", "9. How to start the project"))
    B.append(("code",
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose up -d                       # builds if needed, starts 14 containers\n"
              "docker compose ps                          # all Up, MySQL/ES healthy\n"
              "start http://localhost:8761                # Eureka dashboard\n"
              "start http://localhost:3000                # front end (demo page)\n\n"
              "# API examples through the gateway\n"
              "curl http://localhost:8080/api/products\n"
              "curl -X POST http://localhost:8080/api/orders -H \"Content-Type: application/json\" ^\n"
              "     -d \"{\\\"items\\\":[{\\\"productId\\\":21,\\\"quantity\\\":2}]}\"\n"
              "curl http://localhost:8080/api/orders/18\n"
              "curl \"http://localhost:8080/api/search?text=Demo\"\n\n"
              "# evidence inside the infrastructure\n"
              "docker exec redis redis-cli -a mypass --scan --pattern 'products*'\n"
              "curl \"http://localhost:9200/products/_search?q=name:Demo&pretty\"\n"
              "docker logs -f shopstream-notification-service-1"))

    # ------------------------------------------------------------------ 10
    B.append(("break",))
    B.append(("h1", "10. Appendix A — annotation quick reference"))
    B.append(("p",
              "This page is my own revision sheet: every annotation used in the project, where it is and "
              "what it does. It is also the order in which I will explain the code during the oral exam."))
    B.append(("table", [
        ["Annotation / interface", "Where", "Effect"],
        ["@SpringBootApplication", "all eight services", "Auto-configuration, component scan, main class"],
        ["@EnableEurekaServer", "DiscoveryServerApplication", "Starts the registry and the dashboard"],
        ["@EnableConfigServer", "ConfigServerApplication", "Serves /{application}/{profile} from config-repo"],
        ["@EnableCaching", "ProductServiceApplication", "Activates @Cacheable and @CacheEvict"],
        ["@EnableRedisRepositories", "CartServiceApplication", "Creates repositories for @RedisHash entities"],
        ["@EnableFeignClients", "order-service, cart-service", "Creates the @FeignClient proxies"],
        ["@RestController + @RequestMapping", "ProductController, OrderController, CartController, SearchController",
         "HTTP layer; the path prefix is the one the gateway forwards"],
        ["@Cacheable(value, key) / @CacheEvict", "ProductController one(), update(), delete()",
         "Read-through cache; eviction on change"],
        ["@KafkaListener(topics, groupId)", "OrderEventListener, InventoryEventListener, OrderNotificationListener, ProductEventListener",
         "Consumer method; the group id controls load sharing"],
        ["@Document(indexName) / @Setting / @Field / @Id", "ProductDocument", "Index name, mapping and document id"],
        ["@RedisHash(\"carts\") / @TimeToLive", "Cart", "Redis hash key space and expiry in seconds"],
        ["@Entity / @Table / @Id / @GeneratedValue", "Product, Order", "JPA table mapping and identity generation"],
        ["@Modifying + @Query + @Param", "ProductRepository.reserveStock", "One atomic UPDATE instead of read-then-write"],
        ["@Transactional", "OrderService, StockReservationService, CartService", "One unit of work; rollback on error"],
        ["@FeignClient(name) + @EnableFeignClients", "ProductClient, OrderClient", "HTTP client by service name"],
        ["@Component / @Service / @Configuration / @Bean", "filters, listeners, configs", "Spring beans and configuration objects"],
        ["GlobalFilter + Ordered", "XRequestIdFilter", "Runs on every route, order -100 = first"],
    ], [4.6 * cm, 6.6 * cm, 5.8 * cm]))

    # ------------------------------------------------------------------ 11
    B.append(("break",))
    B.append(("h1", "11. Appendix B — demo script for the oral exam (eight steps)"))
    B.append(("p",
              "This version follows the eight-step demo script from my own study notes. The order is fixed "
              "and every step is the same pattern: do one action, show him one piece of evidence, say one "
              "sentence in English. Rehearsing this way keeps both hands and speech moving, which is easier "
              "to hold than a long prepared speech."))
    B.append(("table", [
        ["Step", "What I do", "What he sees", "What I say"],
        ["1", "cd into the project folder, docker compose up -d", "All containers Up",
         "All containers are up."],
        ["2", "Open localhost:8761 in the browser", "Services listed in Eureka",
         "Services register here."],
        ["3", "Postman GET /api/products", "JSON array of products", "GET products."],
        ["4", "Postman POST /api/products", "201 Created with a new id", "Create a product. POST."],
        ["5", "Open a second PowerShell, follow the search-service log, go back and press Send in step 4",
         "The window prints the event by itself", "It reads the Kafka event."],
        ["6", "Postman GET /api/search?text=Demo", "200 OK, the new product is found",
         "Search goes to Elasticsearch."],
        ["7", "Clear the product-service log, then GET the same product twice",
         "First call logs a database read, second one does not", "Redis cache."],
        ["8", "Postman POST /api/orders, then GET /api/orders/{id}",
         "totalPrice in the 201, then the same order read back", "Feign gets the price."],
    ], [1.2 * cm, 6.2 * cm, 4.6 * cm, 5.0 * cm]))
    B.append(("p",
              "Note: the dashboard in step 2 actually lists seven applications (six business services plus "
              "config-server), so \"six services\" means the business services. The product id and order id "
              "in steps 7 and 8 must be the real numbers returned at that moment, not the examples in this "
              "table."))

    B.append(("h2", "11.1 Step by step, with the sentences I say"))
    B.append(("p", "Step 1: start all containers."))
    B.append(("code",
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose up -d\n"
              "docker compose ps          # all Up; both MySQL and Elasticsearch must be (healthy)"))
    B.append(("p", "Say: All containers are up."))

    B.append(("p", "Step 2: open the Eureka dashboard."))
    B.append(("code", "start http://localhost:8761\n"
                      "# the page refreshes about every 30 seconds, so give it a moment after start-up"))
    B.append(("p", "Say: Services register here."))

    B.append(("p", "Step 3: read the product list."))
    B.append(("code", "GET http://localhost:8080/api/products     -> 200 OK, JSON array of products"))
    B.append(("p",
              "If he asks how the request travels, add one sentence: it hits the gateway first, the gateway "
              "routes it to product-service by service name, and that service reads MySQL and returns JSON. "
              "Say: GET products."))

    B.append(("p", "Step 4: create a product."))
    B.append(("code",
              "POST http://localhost:8080/api/products\n"
              "Body -> raw -> JSON:\n"
              "{\n"
              "  \"name\": \"Demo Book\",\n"
              "  \"description\": \"Created during the demo\",\n"
              "  \"category\": \"book\",\n"
              "  \"price\": 19.90,\n"
              "  \"stock\": 11\n"
              "}"))
    B.append(("p",
              "Press Send, get 201 Created, and write down the id in the response — the next steps need it. "
              "Say: Create a product. POST."))

    B.append(("p", "Step 5: prove the write really reached Kafka."))
    B.append(("code",
              "# In a second PowerShell window, leave it waiting for log lines\n"
              "cd \"F:\\Final Project\\ShopStream\"\n"
              "docker compose logs --tail 5 -f search-service\n"
              "# keep the window open, switch back to Postman and press Send on the step-4 request again"))
    B.append(("p",
              "Within a second or two the window prints the log lines showing search-service received the "
              "product-events message. Say: It reads the Kafka event."))

    B.append(("p", "Step 6: find the new product through the search API."))
    B.append(("code", "GET http://localhost:8080/api/search?text=Demo      -> 200 OK, Demo Book is found"))
    B.append(("p", "Say: Search goes to Elasticsearch. It does not read MySQL."))

    B.append(("p", "Step 7: prove the Redis cache is really used."))
    B.append(("code",
              "# 1. Docker Desktop -> product-service-1 -> tab Logs -> clear the log first\n"
              "# 2. Back in Postman, GET the same product twice:\n"
              "GET http://localhost:8080/api/products/{the id returned in step 4}\n"
              "GET http://localhost:8080/api/products/{the same id}"))
    B.append(("p",
              "The first call shows the database read in the log; the second one shows nothing, which means "
              "it was served from Redis. If the second call still reads the database, the cache did not "
              "work and that step has failed. Say: Redis cache."))

    B.append(("p", "Step 8: place an order and show that the price is computed on the server."))
    B.append(("p",
              "This step has two halves: place the order, then read it back. One expectation from my older "
              "notes changed: POST always returns PENDING by design, because the interface does not wait for "
              "Kafka; only the GET one or two seconds later shows CONFIRMED."))
    B.append(("table", [
        ["What my older notes said", "What the current code actually does"],
        ["POST /api/orders -> 201, status PENDING, totalPrice 39.80", "The same, unchanged"],
        ["GET /api/orders/{id} -> returns the same PENDING", "Returns CONFIRMED after a few seconds"],
    ], [8.5 * cm, 8.5 * cm]))
    B.append(("p", "First create a product with stock 11. Body -> raw -> JSON:"))
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
              "Press Send, get 201, and note the new id (in my run it was 24). The productId below must be "
              "this new id; with an id whose stock is zero the order is rejected as REJECTED."))
    B.append(("p", "Now the order itself. New request, POST, Body -> raw -> JSON:"))
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
              "201 Created with order 47, status PENDING, totalPrice 39.80 and unitPrice 19.90. There is no "
              "price in the request body: 39.80 was read from product-service through Feign and multiplied "
              "by the order-service itself."))
    B.append(("code",
              "{\n"
              "  \"id\": 47,\n"
              "  \"status\": \"PENDING\",\n"
              "  \"totalPrice\": 39.80,\n"
              "  \"items\": [\n"
              "    { \"id\": 47, \"productId\": 24, \"quantity\": 2, \"unitPrice\": 19.90 }\n"
              "  ]\n"
              "}"))
    B.append(("p", "Finally read the order back: change the same tab to GET and use the returned id."))
    B.append(("code",
              "GET http://localhost:8080/api/orders/47\n"
              "-> 200 OK, \"status\": \"CONFIRMED\""))
    B.append(("p",
              "CONFIRMED means the Kafka side finished: OrderPlaced was published, the stock was decremented "
              "by the atomic UPDATE, StockReserved came back, and the order status was rewritten. Say: "
              "Feign gets the price. Then add: Now it is CONFIRMED."))

    B.append(("h2", "11.2 Sentences for when I do not understand a question"))
    B.append(("code",
              "Sorry, could you repeat the question?\n"
              "Do you mean the order service?\n"
              "Can I show you the code instead?\n"
              "I am not sure. Let me check.\n"
              "Can you speak a little slowly, please?"))

    B.append(("h2", "11.3 Pre-demo checklist"))
    B.append(("bullets", [
        "Run docker compose up -d about ten minutes early and wait until both MySQL containers and "
        "Elasticsearch show (healthy), otherwise the first request fails.",
        "Product ids and order ids change between demos: read the real id from GET /api/products, and use "
        "the id returned in the 201 response for the order.",
        "In step 7 clear the product-service log before the second call, otherwise the two calls cannot be "
        "told apart.",
        "Steps 5 and 7 each need an extra PowerShell window; open them in advance so nothing has to be "
        "hunted for during the demo.",
        "Rehearse three times until the script is not needed: first the actions, then the sentences, and "
        "only then both together.",
    ]))
    return B
