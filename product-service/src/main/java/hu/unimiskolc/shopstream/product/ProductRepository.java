package hu.unimiskolc.shopstream.product;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProductRepository extends JpaRepository<Product, Long> {

    /**
     * 原子扣库存：只有 stock >= quantity 才会更新成功，返回受影响行数。
     * 返回 0 表示库存不足或商品不存在。
     */
    @Modifying
    @Query("update Product p set p.stock = p.stock - :quantity where p.id = :id and p.stock >= :quantity")
    int reserveStock(@Param("id") Long id, @Param("quantity") Integer quantity);
}