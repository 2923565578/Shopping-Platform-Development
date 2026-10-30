package hu.unimiskolc.shopstream.order;

import java.util.List;

public record CreateOrderRequest(List<OrderItemRequest> items) {}