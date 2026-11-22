package hu.unimiskolc.shopstream.cart;

import java.io.Serializable;
import java.util.Objects;

/**
 * 购物车里的一行。价格不存这里：下单时由 order-service 用 Feign 去查最新价格。
 */
public class CartItem implements Serializable {
    private static final long serialVersionUID = 1L;

    private Long productId;
    private Integer quantity;

    public CartItem() {
    }

    public CartItem(Long productId, Integer quantity) {
        this.productId = productId;
        this.quantity = quantity;
    }

    public Long getProductId() { return productId; }
    public void setProductId(Long productId) { this.productId = productId; }
    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof CartItem)) return false;
        return Objects.equals(productId, ((CartItem) o).productId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(productId);
    }
}
