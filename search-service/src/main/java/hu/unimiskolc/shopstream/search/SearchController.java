package hu.unimiskolc.shopstream.search;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/search")
public class SearchController {
    private final ProductSearchRepository searchRepository;

    public SearchController(ProductSearchRepository searchRepository) {
        this.searchRepository = searchRepository;
    }

    @GetMapping
    public Iterable<ProductDocument> search(
            @RequestParam(required = false) String text,
            @RequestParam(required = false) String category) {
        
        if (text != null && !text.isEmpty()) {
            return searchRepository.findByNameContainingOrDescriptionContaining(text, text);
        }
        if (category != null && !category.isEmpty()) {
            return searchRepository.findByCategory(category);
        }
        return searchRepository.findAll();
    }
}