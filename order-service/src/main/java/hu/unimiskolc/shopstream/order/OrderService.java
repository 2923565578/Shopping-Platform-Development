package hu.unimiskolc.shopstream.order;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;

@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final RestClient productRestClient;

    public OrderService(OrderRepository orderRepository, RestClient productRestClient) {
        this.orderRepository = orderRepository;
        this.productRestClient = productRestClient;
    }

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        Order order = new Order();
        BigDecimal total = BigDecimal.ZERO;

        for (OrderItemRequest itemReq : request.items()) {
            ProductDto product = productRestClient.get()
                    .uri("/products/{id}", itemReq.productId())
                    .retrieve()
                    .body(ProductDto.class);

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
        return orderRepository.save(order);
    }

    @Transactional(readOnly = true)
    public Order getOrder(Long id) {
        return orderRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Order not found: " + id));
    }
}