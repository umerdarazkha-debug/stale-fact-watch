# facts.json shape

A list (or `{"facts": [...]}`) of objects:

```json
{"id": "acme-pro-price", "entity": "Acme CRM Pro plan", "attribute": "price",
 "value": "$29", "keywords": ["Pro"], "source_url": "https://acme.example.com/pricing",
 "our_page": "pages/acme-review.md", "priority": "high"}
```

Required: `id`, `entity`, `attribute`, `value`, `source_url`. Optional: `keywords` (defaults to attribute and entity, which is loose), `our_page` (path relative to facts.json, or a URL), `priority`.

history.json is written by the script: `{"runs": [{"date": ..., "results": {id: {status, candidates}}}]}`. The last 26 runs are kept.
