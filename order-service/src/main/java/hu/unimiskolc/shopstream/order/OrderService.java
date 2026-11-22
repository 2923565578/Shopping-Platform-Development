package hu.unimiskolc.shopstream.order;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final ProductClient productClient; // 换成了 Feign 客户端
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public OrderService(OrderRepository orderRepository, ProductClient productClient, KafkaTemplate<String, String> kafkaTemplate) {
        this.orderRepository = orderRepository;
        this.productClient = productClient;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        Order order = new Order();
        BigDecimal total = BigDecimal.ZERO;

        for (OrderItemRequest itemReq : request.items()) {
            // 核心变化：直接用 Feign 发起调用！
            ProductDto product = productClient.getProduct(itemReq.productId());

            if (product == null) {
                throw new RuntimeException("Product not found: " + itemReq.productId());
            }

            OrderItem item = new OrderItem();
            item.setProductId(product.id());
            item.setQuantity(itemReq.quantity());
            item.setUnitPrice(product.price());
            order.addItem(item);

            total = total.add(product.price().multiply(BigDecimal.valueOf(itemReq.quantity())));
        }

        order.setTotalPrice(total);
        order.setStatus(OrderStatus.PENDING);
        Order savedOrder = orderRepository.save(order);

        // Task 4：发 OrderPlaced，带上订单明细，product-service 才有东西可以扣库存
        sendOrderEvent("OrderPlaced", savedOrder);

        return savedOrder;
    }

    /**
     * 统一的 order-events 发送方法，消息格式沿用项目约定： "事件名:" + json
     */
    public void sendOrderEvent(String eventType, Order order) {
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("orderId", order.getId());
            payload.put("status", order.getStatus() == null ? null : order.getStatus().name());

            List<Map<String, Object>> items = new ArrayList<>();
            for (OrderItem item : order.getItems()) {
                Map<String, Object> one = new LinkedHashMap<>();
                one.put("productId", item.getProductId());
                one.put("quantity", item.getQuantity());
                items.add(one);
            }
            payload.put("items", items);

            kafkaTemplate.send("order-events", order.getId().toString(),
                    eventType + ":" + objectMapper.writeValueAsString(payload));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Transactional(readOnly = true)
    public Order getOrder(Long id) {
        return orderRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Order not found: " + id));
    }

    @Transactional
    public void updateOrderStatus(Long orderId, OrderStatus status) {
        orderRepository.findById(orderId).ifPresent(order -> {
            order.setStatus(status);
            orderRepository.save(order);
        });
    }

    /**
     * 收到库存事件后落状态，并广播最终结果（notification-service 就监听这个）。
     * 已经是最终状态的订单直接跳过，避免重复消息导致重复通知。
     */
    @Transactional
    public void applyInventoryResult(Long orderId, boolean stockReserved) {
        orderRepository.findById(orderId).ifPresentOrElse(order -> {
            if (order.getStatus() == OrderStatus.CONFIRMED || order.getStatus() == OrderStatus.REJECTED) {
                System.out.println("订单已是最终状态，跳过: " + orderId);
                return;
            }
            order.setStatus(stockReserved ? OrderStatus.CONFIRMED : OrderStatus.REJECTED);
            Order saved = orderRepository.save(order);
            System.out.println("订单状态更新: " + orderId + " -> " + saved.getStatus());
            sendOrderEvent(stockReserved ? "OrderConfirmed" : "OrderRejected", saved);
        }, () -> System.out.println("订单不存在，忽略库存事件: " + orderId));
    }
}