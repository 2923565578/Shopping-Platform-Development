package hu.unimiskolc.shopstream.cart;

import org.springframework.data.repository.CrudRepository;

/**
 * Step4 Task2：CrudRepository，key 是 userId，数据存在 Redis。
 */
public interface CartRepository extends CrudRepository<Cart, Long> {
}
