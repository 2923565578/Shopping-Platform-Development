package hu.unimiskolc.shopstream.search;

import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;

public interface ProductSearchRepository extends ElasticsearchRepository<ProductDocument, Long> {
    Iterable<ProductDocument> findByNameContainingOrDescriptionContaining(String name, String desc);
    Iterable<ProductDocument> findByCategory(String category);
}