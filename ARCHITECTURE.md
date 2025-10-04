# LangChain RAG System Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├─────────────────────────────────────────────────────────────────────┤
│  Python API  │  CLI (cli.py)  │  Jupyter Notebook  │  Examples     │
└──────┬───────────────┬──────────────┬───────────────────┬───────────┘
       │               │              │                   │
       └───────────────┴──────────────┴───────────────────┘
                              │
                              ▼
       ┌──────────────────────────────────────────┐
       │     ChromaDBRAG Class (rag_chromadb.py)  │
       │  ┌────────────────────────────────────┐  │
       │  │  Initialization                    │  │
       │  │  - persist_directory               │  │
       │  │  - collection_name                 │  │
       │  │  - OpenAI API key                  │  │
       │  └────────────────────────────────────┘  │
       └──────────────────┬───────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │ Document│    │  Vector  │    │    QA    │
    │ Loading │    │  Store   │    │  Chain   │
    └─────────┘    └──────────┘    └──────────┘
         │                │                │
         ▼                ▼                ▼
```

## Component Details

### 1. Document Processing Pipeline

```
Documents (txt, pdf, etc.)
          │
          ▼
┌─────────────────────┐
│  DirectoryLoader    │  Load files from directory
│  TextLoader         │  Or load single file
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ RecursiveCharacter  │  Split into chunks
│   TextSplitter      │  - chunk_size: 1000
│                     │  - chunk_overlap: 200
└──────────┬──────────┘
           │
           ▼
      [Document Chunks]
```

### 2. Vector Storage Pipeline

```
[Document Chunks]
       │
       ▼
┌─────────────────────┐
│  OpenAIEmbeddings   │  Convert text to vectors
│  (text-ada-002)     │  1536 dimensions
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    ChromaDB         │  Store vectors persistently
│  - SQLite backend   │  - Fast similarity search
│  - Disk persistence │  - Multiple collections
│  - HNSW indexing    │  - Metadata filtering
└─────────────────────┘
```

### 3. Query & Retrieval Pipeline

```
User Question
     │
     ▼
┌─────────────────────┐
│  Query Embedding    │  Convert question to vector
│  (same model)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Similarity Search   │  Find relevant chunks
│  (ChromaDB)         │  - Cosine similarity
│                     │  - Return top-k (default: 4)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieved Context   │  Combine chunks
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Prompt Template    │  Format context + question
│  + Context          │
│  + Question         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ChatOpenAI        │  Generate answer
│  (GPT-3.5-turbo)    │  - Temperature: 0
│                     │  - Context-aware
└──────────┬──────────┘
           │
           ▼
    Answer + Sources
```

## Data Flow Example

### Creating a Vector Store

```
1. Load documents
   ./sample_documents/*.txt → [3 documents]

2. Split into chunks
   [3 documents] → [~20 chunks] (500 chars each)

3. Generate embeddings
   [20 chunks] → [20 × 1536 vectors]

4. Store in ChromaDB
   [vectors] → ./chroma_db/ (persisted)
```

### Querying the System

```
1. User asks: "What is machine learning?"

2. Convert to embedding
   "What is machine learning?" → [1 × 1536 vector]

3. Search ChromaDB
   Find top 4 similar chunks

4. Build context
   Chunk 1: "Machine Learning is..."
   Chunk 2: "Types of ML include..."
   Chunk 3: "Applications are..."
   Chunk 4: "ML algorithms like..."

5. Create prompt
   "Use this context: [chunks 1-4]
    Answer: What is machine learning?"

6. LLM generates answer
   "Machine learning is a subset of AI that..."

7. Return result
   {
     "result": "Machine learning is...",
     "source_documents": [chunk1, chunk2, chunk3, chunk4]
   }
```

## Key Components

### Core Classes

- **ChromaDBRAG**: Main orchestrator class
- **OpenAIEmbeddings**: Converts text to vectors
- **Chroma**: Vector database for storage and retrieval
- **RetrievalQA**: Question-answering chain
- **ChatOpenAI**: LLM for answer generation

### Important Methods

- `load_documents()`: Load files from disk
- `split_documents()`: Chunk text intelligently
- `create_vectorstore()`: Build and persist vector DB
- `load_vectorstore()`: Load existing vector DB
- `similarity_search()`: Find relevant documents
- `setup_qa_chain()`: Initialize QA system
- `query()`: Ask questions and get answers

## Performance Characteristics

### Time Complexity

- Document Loading: O(n) - linear in file size
- Text Splitting: O(n) - linear in text length
- Embedding Creation: O(n × API_latency)
- Vector Storage: O(n log n) - HNSW index
- Similarity Search: O(log n) - approximate nearest neighbor
- LLM Response: O(context_size × API_latency)

### Space Complexity

- Embeddings: ~6KB per chunk (1536 floats × 4 bytes)
- ChromaDB: ~1-2MB per 1000 chunks
- Total: Depends on document size and chunking

## Configuration Options

### Chunking
- `chunk_size`: 500-2000 tokens (affects context quality)
- `chunk_overlap`: 10-20% of chunk_size (prevents loss)

### Retrieval
- `k`: Number of chunks to retrieve (3-5 typical)
- `search_type`: similarity, mmr, similarity_score_threshold

### LLM
- `model`: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- `temperature`: 0 (factual) to 1 (creative)
- `max_tokens`: Response length limit

### Storage
- `persist_directory`: Where to save ChromaDB
- `collection_name`: Namespace for documents

## Extension Points

1. **Custom Document Loaders**: Add PDF, DOCX, CSV, etc.
2. **Alternative Embeddings**: HuggingFace, Cohere, etc.
3. **Different Vector Stores**: Pinecone, Weaviate, Qdrant
4. **Custom Retrievers**: Hybrid search, reranking
5. **Advanced Chains**: Multi-step reasoning, agents
6. **Caching**: Cache embeddings and responses
7. **Monitoring**: Track usage, costs, performance

## Security Considerations

1. **API Keys**: Store in .env, never commit
2. **Input Validation**: Sanitize user queries
3. **Rate Limiting**: Prevent API abuse
4. **Data Privacy**: Be careful with sensitive documents
5. **Access Control**: Implement authentication if needed

## Cost Estimation

### Per 1000 Documents (avg 500 tokens each)

- Embeddings: 500,000 tokens × $0.0001/1K = $0.05
- Storage: ~500MB ChromaDB (negligible)
- Queries (100): 100 × 2,000 tokens × $0.002/1K = $0.40
- **Total: ~$0.45**

### Optimization Tips

1. Cache embeddings to avoid regeneration
2. Use smaller chunks for less context
3. Reduce k to retrieve fewer documents
4. Use gpt-3.5-turbo instead of gpt-4
5. Batch process documents
