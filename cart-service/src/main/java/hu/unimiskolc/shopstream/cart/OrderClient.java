package hu.unimiskolc.shopstream.cart;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.Map;

/**
 * Step4 Task4 / Step5 Task3：用服务名调用 order-service，不写死 IP。
 */
@FeignClient(name = "order-service")
public interface OrderClient {

    @PostMapping("/orders")
    Map<String, Object> createOrder(@RequestBody Map<String, Object> request);
}
