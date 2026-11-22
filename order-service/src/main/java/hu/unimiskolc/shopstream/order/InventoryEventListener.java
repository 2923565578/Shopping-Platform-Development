package hu.unimiskolc.shopstream.order;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Task 6：order-service 消费 inventory-events，把订单改成 CONFIRMED 或 REJECTED。
 */
@Component
public class InventoryEventListener {

    private final OrderService orderService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public InventoryEventListener(OrderService orderService) {
        this.orderService = orderService;
    }

    @KafkaListener(topics = "inventory-events", groupId = "order-service")
    public void handleInventoryEvents(ConsumerRecord<String, String> record) {
        String value = record.value();
        System.out.println("order-service 收到库存事件: Key=" + record.key() + ", Value=" + value);

        if (value == null) return;

        try {
            if (value.startsWith("StockReserved:")) {
                Long orderId = readOrderId(value);
                orderService.applyInventoryResult(orderId, true);
            } else if (value.startsWith("StockRejected:")) {
                Long orderId = readOrderId(value);
                orderService.applyInventoryResult(orderId, false);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private Long readOrderId(String value) throws Exception {
        String json = value.substring(value.indexOf(":") + 1);
        return objectMapper.readValue(json, InventoryEvent.class).orderId();
    }
}
