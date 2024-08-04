# bookworm

### Processes 

*`bookworm sync`*

```python
python -m bookworm sync
```

```mermaid
graph LR

subgraph Bookmarks 
    Chrome(Chrome Bookmarks)
    Brave(Brave Bookmarks)
end

Bookworm(bookworm sync)

EmbeddingsService(Embeddings Service e.g OpenAIEmbeddings)

VectorStore(Vector Store e.g DuckDB)

Chrome -->|load bookmarks|Bookworm
Brave -->|load bookmarks|Bookworm

Bookworm -->|vectorize bookmarks|EmbeddingsService-->|store embeddings|VectorStore
```

*`bookworm ask`*


```python
python -m bookworm ask
```

TODO


### Developer Setup 

```bash
# LLMs
export OPENAI_API_KEY=

# Langchain (optional, but useful for debugging)
export LANGCHAIN_API_KEY=
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=bookworm

# Misc (optional)
export LOGGING_LEVEL=INFO
```
