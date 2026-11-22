package hu.unimiskolc.shopstream.cart;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class CartService {

    private final CartRepository cartRepository;
    private final OrderClient orderClient;

    public CartService(CartRepository cartRepository, OrderClient orderClient) {
        this.cartRepository = cartRepository;
        this.orderClient = orderClient;
    }

    /** 查购物车。没有就返回一个空购物车（不写 Redis） */
    public Cart getOrCreate(Long userId) {
        return cartRepository.findById(userId).orElseGet(() -> new Cart(userId));
    }

    /** 加一件商品。已经在车里就累加数量 */
    public Cart addItem(Long userId, CartItemRequest request) {
        if (request.productId() == null || request.quantity() == null || request.quantity() <= 0) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "productId 和 quantity 必填，quantity 要大于 0");
        }
        Cart cart = getOrCreate(userId);
        Optional<CartItem> existing = findItem(cart, request.productId());
        if (existing.isPresent()) {
            existing.get().setQuantity(existing.get().getQuantity() + request.quantity());
        } else {
            cart.getItems().add(new CartItem(request.productId(), request.quantity()));
        }
        System.out.println("购物车更新: user=" + userId + ", productId=" + request.productId());
        return cartRepository.save(cart);
    }

    /** 改数量。数量 <= 0 就等于删掉这一行 */
    public Cart changeQuantity(Long userId, Long productId, Integer quantity) {
        Cart cart = cartRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "购物车不存在: " + userId));
        CartItem item = findItem(cart, productId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "购物车里没有这个商品: " + productId));

        if (quantity == null || quantity <= 0) {
            cart.getItems().remove(item);
        } else {
            item.setQuantity(quantity);
        }
        return cartRepository.save(cart);
    }

    /** 删掉一件商品 */
    public Cart removeItem(Long userId, Long productId) {
        Cart cart = cartRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "购物车不存在: " + userId));
        cart.getItems().removeIf(i -> i.getProductId().equals(productId));
        return cartRepository.save(cart);
    }

    /** 清空购物车 */
    public void clear(Long userId) {
        cartRepository.deleteById(userId);
    }

    /**
     * Step4 Task4：把购物车丢给 order-service 下单，订单被接受（201）才清空购物车。
     */
    public Map<String, Object> checkout(Long userId) {
        Cart cart = cartRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "购物车为空: " + userId));
        if (cart.getItems().isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "购物车是空的");
        }

        List<Map<String, Object>> items = new ArrayList<>();
        for (CartItem item : cart.getItems()) {
            Map<String, Object> one = new LinkedHashMap<>();
            one.put("productId", item.getProductId());
            one.put("quantity", item.getQuantity());
            items.add(one);
        }
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("items", items);

        Map<String, Object> order;
        try {
            order = orderClient.createOrder(body);
        } catch (Exception e) {
            // 订单没被接受：购物车原样保留
            System.out.println("下单失败，购物车保留: " + e.getMessage());
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "下单失败，购物车已保留: " + e.getMessage());
        }

        cartRepository.deleteById(userId);
        System.out.println("下单成功，购物车已清空: user=" + userId);
        return order;
    }

    private Optional<CartItem> findItem(Cart cart, Long productId) {
        return cart.getItems().stream().filter(i -> i.getProductId().equals(productId)).findFirst();
    }
}
