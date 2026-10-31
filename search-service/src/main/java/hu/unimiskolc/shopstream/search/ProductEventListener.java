package hu.unimiskolc.shopstream.search;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class ProductEventListener {
    private final ProductSearchRepository searchRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ProductEventListener(ProductSearchRepository searchRepository) {
        this.searchRepository = searchRepository;
    }

    @KafkaListener(topics = "product-events")
    public void handleProductEvents(ConsumerRecord<String, String> record) {
        String key = record.key();
        String value = record.value();
        System.out.println("收到商品事件: Key=" + key + ", Value=" + value);

        if (key == null) return;
        Long productId = Long.parseLong(key);

        try {
            if ("ProductDeleted".equals(value)) {
                searchRepository.deleteById(productId);
                System.out.println("商品已从 ES 删除: " + productId);
            } else if (value.startsWith("ProductCreated:") || value.startsWith("ProductUpdated:")) {
                String jsonData = value.substring(value.indexOf(":") + 1);
                ProductDocument doc = objectMapper.readValue(jsonData, ProductDocument.class);
                searchRepository.save(doc);
                System.out.println("商品已存入 ES: " + doc.getId());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}