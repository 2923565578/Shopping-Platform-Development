package hu.unimiskolc.shopstream.product;

public record OrderItemEvent(Long productId, Integer quantity) {
}
