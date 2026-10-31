package hu.unimiskolc.shopstream.product;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {
    private final ProductRepository repo;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ProductController(ProductRepository repo, KafkaTemplate<String, String> kafkaTemplate) {
        this.repo = repo;
        this.kafkaTemplate = kafkaTemplate;
    }

    @GetMapping
    public List<Product> all() { return repo.findAll(); }

    @GetMapping("/{id}")
    public ResponseEntity<Product> one(@PathVariable Long id) {
        return repo.findById(id).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<Product> create(@RequestBody Product product) {
        product.setId(null);
        Product saved = repo.save(product);
        sendEvent("ProductCreated", saved);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Product> update(@PathVariable Long id, @RequestBody Product body) {
        return repo.findById(id).map(p -> {
            p.setName(body.getName());
            p.setDescription(body.getDescription());
            p.setCategory(body.getCategory());
            p.setPrice(body.getPrice());
            p.setStock(body.getStock());
            Product saved = repo.save(p);
            sendEvent("ProductUpdated", saved);
            return ResponseEntity.ok(saved);
        }).orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        if (!repo.existsById(id)) return ResponseEntity.notFound().build();
        repo.deleteById(id);
        kafkaTemplate.send("product-events", id.toString(), "ProductDeleted");
        return ResponseEntity.noContent().build();
    }

    private void sendEvent(String eventType, Product product) {
        try {
            String json = objectMapper.writeValueAsString(product);
            kafkaTemplate.send("product-events", product.getId().toString(), eventType + ":" + json);
            System.out.println("成功发送商品事件: " + eventType);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}