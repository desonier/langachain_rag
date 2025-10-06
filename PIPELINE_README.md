# Resume RAG System - Ingest & Query Pipeline

This system is split into two separate programs for better organization and workflow:

## 🔄 Ingest Pipeline (`ingest_pipeline.py`)
Handles adding resumes to the vector database with duplicate prevention.

### Usage Examples:
```bash
# Add a single resume file
python ingest_pipeline.py --file ./data/resume.pdf

# Add all resumes from a directory
python ingest_pipeline.py --directory ./data

# List all resumes in database
python ingest_pipeline.py --list

# Show database statistics
python ingest_pipeline.py --stats

# Force update existing resumes
python ingest_pipeline.py --directory ./data --force-update

# Use custom database path
python ingest_pipeline.py --directory ./data --db-path ./custom_db
```

### Features:
- ✅ **Duplicate Prevention**: Automatically skips files already in database
- ✅ **Multi-format Support**: PDF and DOCX files
- ✅ **Force Update**: Option to update existing resumes
- ✅ **Batch Processing**: Add entire directories
- ✅ **Statistics**: View database stats and file counts

## 🔍 Query Application (`query_app.py`)
Handles querying and searching the resume database.

### Usage Examples:
```bash
# Interactive query mode
python query_app.py --interactive

# Basic initialization (shows database info)
python query_app.py
```

### Interactive Commands:
- Type a question to search all resumes
- Type `list` to see available resumes
- Type `resume:<resume_id>` to search a specific resume
- Type `filter:<format>` to search by file format (PDF/DOCX)
- Type `exit` or `quit` to end session

### Python API Usage:
```python
from query_app import ResumeQuerySystem

# Initialize query system
query_system = ResumeQuerySystem()

# Query all resumes
response = query_system.query("What skills does this person have?")
print(response['result'])

# Query specific resume
response = query_system.query("What experience?", resume_id="specific_id")

# Search with metadata filter
response = query_system.search_by_metadata("Skills?", {"file_format": "PDF"})

# List all resumes
resumes = query_system.list_resumes()
for resume in resumes:
    print(f"{resume['document_name']}: {resume['chunk_count']} chunks")
```

## 🚀 Quick Start Workflow

1. **First, ingest your resumes:**
   ```bash
   python ingest_pipeline.py --directory ./data
   ```

2. **Then query the database:**
   ```bash
   python query_app.py --interactive
   ```

3. **Check your database:**
   ```bash
   python ingest_pipeline.py --stats
   ```

## 📂 File Structure
```
├── ingest_pipeline.py     # Resume ingestion pipeline
├── query_app.py          # Query and search application
├── .env                  # Azure OpenAI configuration
├── data/                 # Resume files (PDF, DOCX)
└── resume_vectordb/      # ChromaDB vector database (auto-created)
```

## 🔧 Configuration

Make sure your `.env` file contains:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_API_VERSION=your_version
EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_CHATGPT_DEPLOYMENT=your_deployment
```

## ⚙️ Advanced Features

### Schema & Metadata
Each resume chunk includes:
- **Resume_ID**: Unique identifier based on file path
- **file_format**: PDF or DOCX
- **content_type**: "resume"
- **document_name**: Original filename
- **chunk_id**: Position within document
- **last_updated**: Timestamp

### Search Capabilities
- **Vector Search**: Semantic similarity search
- **Multi-Query**: Enhanced retrieval with multiple query variations
- **Metadata Filtering**: Filter by file format, resume ID, etc.
- **Source Documents**: See which resume chunks provided the answer

### Database Management
- **Persistent Storage**: ChromaDB automatically saves data
- **No Duplicates**: Resume IDs prevent duplicate entries
- **Incremental Updates**: Add new resumes without affecting existing ones
- **Statistics**: Track total resumes, chunks, and file formats

## 💡 Tips

- Run the ingest pipeline first before using the query app
- Use `--force-update` to refresh existing resumes with new versions
- The query app will show an error if no database exists
- Resume IDs are based on file paths, so moving files creates new IDs
- Use interactive mode for exploratory queries
- Use Python API for programmatic integration