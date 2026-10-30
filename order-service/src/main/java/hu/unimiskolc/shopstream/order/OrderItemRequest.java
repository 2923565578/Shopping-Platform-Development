package hu.unimiskolc.shopstream.order;

public record OrderItemRequest(Long productId, Integer quantity) {}