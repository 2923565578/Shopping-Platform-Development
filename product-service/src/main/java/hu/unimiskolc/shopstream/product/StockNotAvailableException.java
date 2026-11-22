package hu.unimiskolc.shopstream.product;

/**
 * 库存不足时抛出，让 @Transactional 回滚（扣了一半的库存也会退回去）。
 */
public class StockNotAvailableException extends RuntimeException {
    public StockNotAvailableException(String message) {
        super(message);
    }
}
