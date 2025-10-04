# LangChain RAG with ChromaDB

A Dockerized application demonstrating Retrieval Augmented Generation (RAG) using LangChain framework with ChromaDB as the vector database backend.

## Features

- 🐳 **Docker-based deployment** - Easy setup with Docker and Docker Compose
- 🔗 **LangChain integration** - Built with the LangChain framework for LLM applications
- 💾 **ChromaDB backend** - Efficient vector storage and similarity search
- 📚 **Document ingestion** - Add and process documents for retrieval
- 🔍 **Semantic search** - Find relevant documents using embeddings
- 🤖 **QA capabilities** - Optional integration with OpenAI for question answering

## Architecture

The application consists of:
- **LangChain**: Framework for building LLM-powered applications
- **ChromaDB**: Open-source embedding database for vector storage
- **HuggingFace Embeddings**: Free sentence-transformers for creating embeddings
- **Docker**: Containerization for easy deployment

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- (Optional) OpenAI API key for QA chain functionality

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/desonier/langachain_rag.git
cd langachain_rag
```

### 2. (Optional) Configure environment variables

If you want to use the QA chain with OpenAI:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Build and run with Docker Compose

```bash
docker-compose up --build
```

The application will:
- Build the Docker image
- Initialize ChromaDB
- Load sample documents
- Demonstrate similarity search queries
- Persist data in the `chroma_data` directory

### 4. View logs

```bash
docker-compose logs -f langchain-app
```

## Project Structure

```
langachain_rag/
├── app.py                 # Main application code
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Usage

### Running the Demo

The default `app.py` includes a demonstration that:
1. Initializes the RAG system with ChromaDB
2. Adds sample documents about LangChain, ChromaDB, Docker, and RAG
3. Performs similarity searches on the knowledge base
4. Displays relevant results

### Customizing the Application

#### Add Your Own Documents

Edit `app.py` and modify the `sample_docs` list:

```python
sample_docs = [
    "Your first document text here...",
    "Your second document text here...",
    # Add more documents
]
```

#### Query the Knowledge Base

```python
rag = LangChainRAG()
rag.add_documents(your_documents)
results = rag.query("Your question here", k=3)
```

#### Use QA Chain with OpenAI

```python
# Set OPENAI_API_KEY in .env file
qa_chain = rag.create_qa_chain()
if qa_chain:
    response = qa_chain({"query": "What is LangChain?"})
    print(response['result'])
```

## Development

### Running Locally (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Building the Docker Image Manually

```bash
docker build -t langchain-rag .
docker run -v $(pwd)/chroma_data:/app/chroma_data langchain-rag
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: (Optional) Your OpenAI API key for QA chain functionality

### Docker Compose Services

The `docker-compose.yml` includes:
- **langchain-app**: Main application service
- **chromadb** (commented): Optional standalone ChromaDB server

To use a standalone ChromaDB server, uncomment the `chromadb` service in `docker-compose.yml`.

## Data Persistence

ChromaDB data is persisted in the `chroma_data` directory using Docker volumes. This ensures your vector database persists between container restarts.

## Technologies Used

- **Python 3.11**: Programming language
- **LangChain**: Framework for LLM applications
- **ChromaDB**: Vector database
- **HuggingFace Transformers**: For creating embeddings
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration

## Troubleshooting

### Permission Issues

If you encounter permission issues with the `chroma_data` directory:

```bash
sudo chown -R $USER:$USER chroma_data
```

### Out of Memory

If the application runs out of memory, increase Docker's memory limit:
- Docker Desktop: Settings → Resources → Memory

### Port Conflicts

If using the standalone ChromaDB service and port 8000 is in use, modify the port mapping in `docker-compose.yml`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Docker Documentation](https://docs.docker.com/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)

## Acknowledgments

- LangChain team for the excellent framework
- ChromaDB team for the vector database
- HuggingFace for the embedding models