package hu.unimiskolc.shopstream.cart;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/carts")
public class CartController {

    private final CartService cartService;

    public CartController(CartService cartService) {
        this.cartService = cartService;
    }

    /** 查购物车 */
    @GetMapping("/{userId}")
    public Cart get(@PathVariable Long userId) {
        return cartService.getOrCreate(userId);
    }

    /** 加一件商品 body: {"productId":17,"quantity":2} */
    @PostMapping("/{userId}/items")
    public Cart addItem(@PathVariable Long userId, @RequestBody CartItemRequest request) {
        return cartService.addItem(userId, request);
    }

    /** 改数量 body: {"quantity":3} */
    @PutMapping("/{userId}/items/{productId}")
    public Cart changeQuantity(@PathVariable Long userId, @PathVariable Long productId,
                               @RequestBody CartItemRequest request) {
        return cartService.changeQuantity(userId, productId, request.quantity());
    }

    /** 删掉一件商品 */
    @DeleteMapping("/{userId}/items/{productId}")
    public Cart removeItem(@PathVariable Long userId, @PathVariable Long productId) {
        return cartService.removeItem(userId, productId);
    }

    /** 清空购物车 */
    @DeleteMapping("/{userId}")
    public ResponseEntity<Void> clear(@PathVariable Long userId) {
        cartService.clear(userId);
        return ResponseEntity.noContent().build();
    }

    /** 结算：调 order-service 下单，成功才清空 */
    @PostMapping("/{userId}/checkout")
    public ResponseEntity<Map<String, Object>> checkout(@PathVariable Long userId) {
        return ResponseEntity.status(HttpStatus.CREATED).body(cartService.checkout(userId));
    }
}
