package hu.unimiskolc.shopstream.product;

import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Task 5：在一个数据库事务里预留库存（扣 stock）。
 * Task 8：幂等 —— processed_orders 表记录已处理的订单号，重复消息直接跳过。
 * Step4 Task5：库存变化后清掉 Redis 里的商品缓存。
 */
@Service
public class StockReservationService {

    private final ProcessedOrderRepository processedOrderRepository;
    private final ProductRepository productRepository;
    private final CacheManager cacheManager;

    public StockReservationService(ProcessedOrderRepository processedOrderRepository,
                                   ProductRepository productRepository,
                                   CacheManager cacheManager) {
        this.processedOrderRepository = processedOrderRepository;
        this.productRepository = productRepository;
        this.cacheManager = cacheManager;
    }

    /**
     * @return true = 库存已经预留（或之前就预留过）；抛异常 = 库存不足 / 商品不存在
     */
    @Transactional
    public void reserve(OrderEvent event) {
        Long orderId = event.orderId();

        // 幂等：这个订单已经处理过，就不再扣第二次
        if (processedOrderRepository.existsById(orderId)) {
            System.out.println("[幂等] 订单已处理过，跳过: " + orderId);
            return;
        }
        processedOrderRepository.save(new ProcessedOrder(orderId));

        for (OrderItemEvent item : event.items()) {
            // 一条 UPDATE ... WHERE stock >= quantity，原子操作，两个实例并发也不会超卖
            int updated = productRepository.reserveStock(item.productId(), item.quantity());
            if (updated == 0) {
                throw new StockNotAvailableException("库存不足: productId=" + item.productId());
            }
            System.out.println("预留库存成功: productId=" + item.productId() + ", quantity=" + item.quantity());
        }

        // 库存变了，商品缓存要清掉（下一次 GET 会重新查库）
        Cache cache = cacheManager.getCache("products");
        if (cache != null) {
            for (OrderItemEvent item : event.items()) {
                cache.evict(item.productId());
            }
        }
    }
}
