package hu.unimiskolc.shopstream.product;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Task 5：product-service 作为 order-events 的消费者（consumer group: product-service）。
 * 收到 OrderPlaced 就预留库存，然后发 StockReserved 或 StockRejected 到 inventory-events。
 */
@Component
public class OrderEventListener {

    private final StockReservationService reservationService;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    public OrderEventListener(StockReservationService reservationService,
                              KafkaTemplate<String, String> kafkaTemplate) {
        this.reservationService = reservationService;
        this.kafkaTemplate = kafkaTemplate;
    }

    @KafkaListener(topics = "order-events", groupId = "product-service")
    public void handleOrderEvents(ConsumerRecord<String, String> record) {
        String value = record.value();
        System.out.println("product-service 收到订单事件: Key=" + record.key() + ", Value=" + value);

        if (value == null || !value.startsWith("OrderPlaced:")) {
            return;
        }

        try {
            String json = value.substring(value.indexOf(":") + 1);
            OrderEvent event = objectMapper.readValue(json, OrderEvent.class);
            reservationService.reserve(event);
            sendInventoryEvent("StockReserved", event.orderId(), null);
        } catch (Exception e) {
            System.out.println("库存预留失败: " + e.getMessage());
            sendInventoryEvent("StockRejected", parseOrderId(value), e.getMessage());
        }
    }

    private void sendInventoryEvent(String eventType, Long orderId, String reason) {
        if (orderId == null) return;
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("orderId", orderId);
            if (reason != null) {
                payload.put("reason", reason);
            }
            kafkaTemplate.send("inventory-events", orderId.toString(),
                    eventType + ":" + objectMapper.writeValueAsString(payload));
            System.out.println("已发送库存事件: " + eventType + " orderId=" + orderId);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /** 预留失败时也要拿到订单号，所以从原始 JSON 里再解析一次 */
    private Long parseOrderId(String value) {
        try {
            String json = value.substring(value.indexOf(":") + 1);
            return objectMapper.readValue(json, OrderEvent.class).orderId();
        } catch (Exception e) {
            return null;
        }
    }
}
