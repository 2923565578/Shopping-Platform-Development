package hu.unimiskolc.shopstream.order;

public record InventoryEvent(Long orderId, String reason) {
}
