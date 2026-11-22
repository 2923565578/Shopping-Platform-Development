package hu.unimiskolc.shopstream.notification;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Task 7：notification-service 订阅 order-events 和 inventory-events，
 * 每个最终订单状态打一行 "email" 日志。没有数据库，只写日志。
 */
@Component
public class OrderNotificationListener {

    @KafkaListener(topics = "order-events", groupId = "notification-service")
    public void handleOrderEvents(ConsumerRecord<String, String> record) {
        String value = record.value();
        if (value == null) return;

        if (value.startsWith("OrderConfirmed:")) {
            sendEmail(record.key(), "CONFIRMED", "Your order is confirmed. Thank you!");
        } else if (value.startsWith("OrderRejected:")) {
            sendEmail(record.key(), "REJECTED", "Sorry, your order was rejected: not enough stock.");
        }
    }

    @KafkaListener(topics = "inventory-events", groupId = "notification-service")
    public void handleInventoryEvents(ConsumerRecord<String, String> record) {
        System.out.println("[通知服务] 收到库存事件: Key=" + record.key() + ", Value=" + record.value());
    }

    private void sendEmail(String orderId, String status, String text) {
        System.out.println("================================");
        System.out.println("EMAIL 订单通知");
        System.out.println("订单号: " + orderId);
        System.out.println("状态: " + status);
        System.out.println("内容: " + text);
        System.out.println("================================");
    }
}
