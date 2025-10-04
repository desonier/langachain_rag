# Quick Start Guide

Get started with LangChain RAG and ChromaDB in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Your OpenAI API Key

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

Or export it in your terminal:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Step 3: Run the Example

```bash
python example_usage.py
```

This will:
- Load sample documents about AI and Machine Learning
- Create embeddings and store them in ChromaDB
- Demonstrate similarity search
- Answer questions using RAG

## Step 4: Try It Yourself

Create a simple Python script:

```python
from rag_chromadb import ChromaDBRAG

# Initialize
rag = ChromaDBRAG()

# Load your documents
documents = rag.load_documents("./sample_documents")
chunks = rag.split_documents(documents)

# Create vector store
rag.create_vectorstore(chunks)

# Set up QA
rag.setup_qa_chain()

# Ask questions
response = rag.query("What is machine learning?")
print(response['result'])
```

## Step 5: Use Your Own Documents

1. Create a folder with your text files:
```bash
mkdir my_documents
echo "Your content here" > my_documents/doc1.txt
```

2. Load them in your script:
```python
documents = rag.load_documents("./my_documents")
```

## Common Commands

**Test the installation:**
```bash
python test_rag.py
```

**Load existing vector store:**
```python
rag = ChromaDBRAG()
rag.load_vectorstore()  # Load from disk
rag.setup_qa_chain()
response = rag.query("Your question")
```

**Add more documents:**
```python
new_docs = rag.load_documents("./new_folder")
chunks = rag.split_documents(new_docs)
rag.add_documents(chunks)  # Add to existing store
```

## Tips

- Start with small documents to test
- Adjust `chunk_size` based on your document length
- Use `temperature=0` for consistent answers
- Increase `k` parameter to retrieve more context
- Check `response['source_documents']` to see what was retrieved

## Troubleshooting

**"ModuleNotFoundError"**: Make sure all dependencies are installed
```bash
pip install -r requirements.txt
```

**"OPENAI_API_KEY not found"**: Set your API key in `.env` file or environment

**"Vector store not initialized"**: Call `create_vectorstore()` or `load_vectorstore()` first

**Memory issues**: Reduce `chunk_size` or process fewer documents

## Next Steps

- Check out the full README.md for detailed documentation
- Explore `example_usage.py` for more examples
- Customize prompts for your specific use case
- Integrate with your own applications

Happy RAG-ing! 🚀
