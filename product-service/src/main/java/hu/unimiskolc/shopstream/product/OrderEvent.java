package hu.unimiskolc.shopstream.product;

import java.util.List;

/**
 * order-events 里 OrderPlaced 消息的 JSON 载荷。
 * 消息格式沿用项目现有约定： "OrderPlaced:" + json
 */
public record OrderEvent(Long orderId, String status, List<OrderItemEvent> items) {
}
