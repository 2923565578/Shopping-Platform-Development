package hu.unimiskolc.shopstream.search;

import org.springframework.data.elasticsearch.client.elc.NativeQuery;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.data.elasticsearch.core.SearchHits;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery;
import co.elastic.clients.elasticsearch._types.query_dsl.RangeQuery;
import co.elastic.clients.elasticsearch._types.query_dsl.TextQueryType;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/search")
public class SearchController {
    private final ElasticsearchOperations elasticsearchOperations;

    public SearchController(ElasticsearchOperations elasticsearchOperations) {
        this.elasticsearchOperations = elasticsearchOperations;
    }

    @GetMapping
    public List<ProductDocument> search(
            @RequestParam(required = false) String text,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        BoolQuery.Builder boolQuery = new BoolQuery.Builder();

        if (text != null && !text.isEmpty()) {
            boolQuery.must(m -> m.multiMatch(mm -> mm
                    .fields("name", "description")
                    .query(text)
                    .type(TextQueryType.BestFields)));
        }

        if (category != null && !category.isEmpty()) {
            boolQuery.filter(f -> f.term(t -> t.field("category").value(category)));
        }

        if (minPrice != null || maxPrice != null) {
            RangeQuery.Builder range = new RangeQuery.Builder().field("price");
            if (minPrice != null) range.gte(co.elastic.clients.json.JsonData.of(minPrice));
            if (maxPrice != null) range.lte(co.elastic.clients.json.JsonData.of(maxPrice));
            boolQuery.filter(f -> f.range(range.build()));
        }

        NativeQuery query = NativeQuery.builder()
                .withQuery(boolQuery.build()._toQuery())
                .withPageable(org.springframework.data.domain.PageRequest.of(page, size))
                .build();

        SearchHits<ProductDocument> hits = elasticsearchOperations.search(query, ProductDocument.class);

        return hits.stream().map(org.springframework.data.elasticsearch.core.SearchHit::getContent).collect(Collectors.toList());
    }
}