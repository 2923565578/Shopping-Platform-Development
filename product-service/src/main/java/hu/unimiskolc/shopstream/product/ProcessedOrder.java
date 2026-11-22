package hu.unimiskolc.shopstream.product;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * 已经处理过的订单号。Task 8 的幂等：同一个 OrderPlaced 来两次，库存只扣一次。
 */
@Entity
@Table(name = "processed_orders")
public class ProcessedOrder {

    @Id
    private Long orderId;

    private LocalDateTime processedAt = LocalDateTime.now();

    public ProcessedOrder() {
    }

    public ProcessedOrder(Long orderId) {
        this.orderId = orderId;
    }

    public Long getOrderId() { return orderId; }
    public void setOrderId(Long orderId) { this.orderId = orderId; }
    public LocalDateTime getProcessedAt() { return processedAt; }
    public void setProcessedAt(LocalDateTime processedAt) { this.processedAt = processedAt; }
}
