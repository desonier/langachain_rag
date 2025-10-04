# LangChain RAG with ChromaDB

A comprehensive implementation of Retrieval-Augmented Generation (RAG) using LangChain and ChromaDB as the vector storage backend.

## Overview

This project demonstrates how to build a RAG system that:
- Loads and processes documents from various sources
- Creates embeddings using OpenAI's embedding models
- Stores embeddings in ChromaDB (a persistent vector database)
- Retrieves relevant context based on user queries
- Generates answers using Large Language Models (LLMs)

## Features

- **Document Loading**: Support for multiple document formats (txt, pdf, etc.)
- **Text Chunking**: Intelligent document splitting with configurable chunk size and overlap
- **Vector Storage**: Persistent storage using ChromaDB
- **Similarity Search**: Fast and efficient retrieval of relevant documents
- **Question Answering**: RAG-based QA system with customizable prompts
- **Extensible Design**: Easy to extend and customize for specific use cases

## Installation

1. Clone the repository:
```bash
git clone https://github.com/desonier/langachain_rag.git
cd langachain_rag
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_api_key_here
```

Or set it as an environment variable:
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

### Quick Start

Run the example script:
```bash
python example_usage.py
```

### Basic Usage

```python
from rag_chromadb import ChromaDBRAG

# Initialize the RAG system
rag = ChromaDBRAG(
    persist_directory="./chroma_db",
    collection_name="my_collection"
)

# Load documents
documents = rag.load_documents("./sample_documents")

# Split documents into chunks
chunks = rag.split_documents(documents, chunk_size=1000, chunk_overlap=200)

# Create vector store
rag.create_vectorstore(chunks)

# Set up QA chain
rag.setup_qa_chain(llm_model="gpt-3.5-turbo", temperature=0)

# Ask questions
response = rag.query("What is artificial intelligence?")
print(response['result'])
```

### Loading Existing Vector Store

```python
from rag_chromadb import ChromaDBRAG

# Initialize and load existing vector store
rag = ChromaDBRAG(persist_directory="./chroma_db")
rag.load_vectorstore()

# Set up QA chain and query
rag.setup_qa_chain()
response = rag.query("Your question here")
```

### Similarity Search

```python
# Perform similarity search without LLM
results = rag.similarity_search("machine learning", k=4)
for doc in results:
    print(doc.page_content)
```

### Custom Prompts

```python
custom_prompt = """Use the following context to answer the question.
If you don't know the answer, say so.

Context: {context}
Question: {question}
Answer:"""

response = rag.query_with_custom_prompt("Your question", custom_prompt)
```

## Project Structure

```
langachain_rag/
├── rag_chromadb.py          # Main RAG implementation
├── example_usage.py         # Example usage script
├── requirements.txt         # Project dependencies
├── sample_documents/        # Sample documents for testing
│   ├── ai_overview.txt
│   ├── machine_learning.txt
│   └── neural_networks.txt
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## API Reference

### ChromaDBRAG Class

#### `__init__(persist_directory, collection_name, openai_api_key)`
Initialize the RAG system.

#### `load_documents(source_path, glob_pattern)`
Load documents from a file or directory.

#### `split_documents(documents, chunk_size, chunk_overlap)`
Split documents into smaller chunks.

#### `create_vectorstore(documents)`
Create a new vector store from documents.

#### `load_vectorstore()`
Load an existing vector store from disk.

#### `add_documents(documents)`
Add documents to an existing vector store.

#### `similarity_search(query, k)`
Search for similar documents.

#### `setup_qa_chain(llm_model, temperature, chain_type)`
Set up a question-answering chain.

#### `query(question)`
Query the RAG system with a question.

#### `query_with_custom_prompt(question, prompt_template)`
Query with a custom prompt template.

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Parameters

- `chunk_size`: Size of text chunks (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `llm_model`: OpenAI model to use (default: "gpt-3.5-turbo")
- `temperature`: LLM temperature (default: 0)
- `k`: Number of documents to retrieve (default: 4)

## Use Cases

- **Knowledge Base QA**: Answer questions from company documentation
- **Research Assistant**: Query research papers and articles
- **Customer Support**: Automated responses based on support documents
- **Legal Document Analysis**: Query legal documents and contracts
- **Educational Tools**: Interactive learning from textbooks and materials

## Requirements

- Python 3.8+
- OpenAI API key
- See `requirements.txt` for all dependencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Vector storage powered by [ChromaDB](https://github.com/chroma-core/chroma)
- Embeddings and LLMs from [OpenAI](https://openai.com)

## Troubleshooting

### Common Issues

1. **ChromaDB persistence issues**: Make sure the persist_directory exists and has write permissions.

2. **OpenAI API errors**: Verify your API key is correctly set and has sufficient credits.

3. **Memory issues with large documents**: Reduce chunk_size or process documents in smaller batches.

4. **Rate limiting**: Add delays between API calls or use a higher-tier OpenAI account.

## Further Reading

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [RAG Overview](https://www.pinecone.io/learn/retrieval-augmented-generation/)

## Contact

For questions or issues, please open an issue on GitHub.