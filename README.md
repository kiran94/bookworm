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

---

*`bookworm ask`*

```python
python -m bookworm ask
```

```mermaid
graph LR

query
Bookworm(bookworm ask)

subgraph _
    LLM(LLM e.g OpenAI)
    VectorStore(Vector Store e.g DuckDB)
end

query -->|user queries for information|Bookworm

Bookworm -->|simularity search|VectorStore -->|send similar docs + user query|LLM
LLM -->|send back response|Bookworm
```

---


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
