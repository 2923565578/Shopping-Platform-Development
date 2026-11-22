package hu.unimiskolc.shopstream.cart;

import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;
import org.springframework.data.redis.core.TimeToLive;

import java.io.Serializable;
import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Step4 Task2：@RedisHash("carts") 的购物车实体，key 是 userId。
 * Step4 Task3：用 @TimeToLive 让购物车自动过期，这里设 1 小时（见 README）。
 */
@RedisHash("carts")
public class Cart implements Serializable {
    private static final long serialVersionUID = 1L;

    /** 购物车的有效期（秒）：1 小时 */
    public static final long CART_TTL_SECONDS = 3600L;

    @Id
    private Long userId;

    private Set<CartItem> items = new LinkedHashSet<>();

    @TimeToLive
    private Long ttl = CART_TTL_SECONDS;

    public Cart() {
    }

    public Cart(Long userId) {
        this.userId = userId;
    }

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Set<CartItem> getItems() { return items; }
    public void setItems(Set<CartItem> items) { this.items = items; }
    public Long getTtl() { return ttl; }
    public void setTtl(Long ttl) { this.ttl = ttl; }
}
