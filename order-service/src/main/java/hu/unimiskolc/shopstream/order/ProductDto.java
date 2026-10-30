package hu.unimiskolc.shopstream.order;

import java.math.BigDecimal;

public record ProductDto(Long id, String name, BigDecimal price, Integer stock) {}