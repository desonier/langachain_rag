# Resume RAG Admin Interface 🚀

## Overview

The **Resume RAG Admin Interface** is a Flask-based web application that provides comprehensive management and querying capabilities for resume collections stored in ChromaDB. It combines vector search with Azure OpenAI to deliver intelligent resume analysis and candidate discovery.

## What It Does

### 🎯 **Core Features**
- **Collection Management**: Create, view, and manage resume collections
- **Document Upload**: Process PDF/DOCX resume files with automatic text extraction
- **Intelligent Queries**: Natural language search across resume databases
- **AI-Powered Analysis**: Generate insights using Azure OpenAI GPT models
- **Cost Tracking**: Monitor token usage and estimated costs
- **Database Administration**: Comprehensive ChromaDB management tools

### 🔍 **Admin Capabilities**
- **Bulk Operations**: Upload multiple resumes at once
- **Collection Analytics**: View document counts and storage statistics
- **Query Debugging**: Detailed search result analysis
- **Database Health**: Connection status and performance monitoring
- **Error Handling**: Comprehensive error reporting and recovery

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Flask Web Interface                     │
├─────────────────┬─────────────────┬───────────────────┤
│  Admin Dashboard │  Query Interface │  Collection Mgmt  │
└─────────────────┴─────────────────┴───────────────────┘
           │                │                │
           ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│               Application Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │Admin Manager│ │Query Engine │ │Document Manager │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
           │                │                │
           ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                  Data & AI Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ ChromaDB    │ │Azure OpenAI │ │ HuggingFace     │   │
│  │Vector Store │ │   Service   │ │ Embeddings      │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### 🖥️ **Backend**
- **Flask**: Web framework with template rendering
- **Python 3.11**: Core runtime environment
- **Gunicorn**: Production WSGI server

### 🤖 **AI & Search**
- **ChromaDB**: Vector database for semantic search
- **Azure OpenAI**: GPT-4 for intelligent responses
- **LangChain**: RAG pipeline orchestration
- **HuggingFace**: Sentence transformer embeddings

### 🎨 **Frontend**
- **Jinja2**: Server-side template rendering
- **Bootstrap 5**: Responsive UI framework
- **JavaScript**: Dynamic client interactions
- **CSS3**: Custom styling and animations

## Key Features

### 📁 **Collection Management**
- Create and organize resume collections
- View collection statistics and metadata
- Bulk document upload with progress tracking
- Collection-specific search and filtering

### 🔍 **Advanced Querying**
- Natural language search queries
- Vector similarity search with relevance scoring
- Contextual AI responses with source attribution
- Query history and result caching

### 🛠️ **Administrative Tools**
- Database connection management
- Performance monitoring and diagnostics
- Error logging and debugging tools
- Backup and restore capabilities

### 💰 **Cost Management**
- Real-time token usage tracking
- Cost estimation per query
- Usage analytics and reporting
- Budget alerts and monitoring

## Getting Started

### 🚀 **Quick Setup**

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Set Azure OpenAI credentials
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_KEY="your-api-key"
   export AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-4"
   ```

3. **Run the Application**
   ```bash
   cd src
   python main.py
   ```

4. **Access the Interface**
   - Navigate to: `http://localhost:5001`
   - Admin Dashboard: `http://localhost:5001/admin`
   - Query Interface: `http://localhost:5001/admin/query`

### 📋 **First Steps**

1. **Create a Collection**: Start by creating your first resume collection
2. **Upload Documents**: Add PDF/DOCX resume files to the collection
3. **Test Queries**: Try natural language searches like "Python developers with 3+ years experience"
4. **Review Results**: Analyze AI responses and relevance scores

## Configuration

### 🔧 **Environment Variables**
```bash
# Required - Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional - Application Settings
CHROMA_PERSIST_DIRECTORY=./resume_vectordb
FLASK_ENV=development
FLASK_DEBUG=True
```

### 📂 **Directory Structure**
```
openwebui-resume-rag-admin/
├── src/
│   ├── main.py                 # Main Flask application
│   ├── admin/
│   │   ├── chromadb_admin.py   # Database management
│   │   └── utils.py            # Utility functions
│   ├── models/
│   │   ├── admin_models.py     # Data models
│   │   └── response_models.py  # Response schemas
│   └── ui/
│       └── interface_manager.py # UI management
├── templates/                  # HTML templates
│   ├── admin_dashboard.html
│   ├── query_interface.html
│   └── collection_manager.html
├── static/                     # CSS/JS assets
│   ├── css/
│   └── js/
├── config/
│   ├── admin_config.py         # Admin configuration
│   └── database_config.py      # Database settings
└── tests/                      # Test suites
```

## Usage Examples

### 🔍 **Query Examples**
```python
# Natural language queries
"Find Python developers with machine learning experience"
"Show me senior software engineers from the last 2 years"
"List candidates with AWS certification and 5+ years experience"
"Find data scientists with PhD in computer science"
```

### 📊 **Admin Operations**
- **View Statistics**: Check collection size and document counts
- **Debug Queries**: Analyze search results and relevance scores
- **Manage Collections**: Create, rename, or delete collections
- **Monitor Performance**: View query response times and costs

## API Endpoints

### 🔗 **REST API**
```bash
# Collections
GET    /api/collections              # List all collections
POST   /api/collections              # Create new collection
DELETE /api/collections/<name>       # Delete collection

# Documents
POST   /api/upload                   # Upload documents
GET    /api/documents/<collection>   # List documents

# Queries
POST   /api/query                    # Execute search query
GET    /api/stats                    # Get usage statistics
```

## Deployment

### 🐳 **Docker Support**
```bash
# Build container
docker build -t resume-rag-admin .

# Run with environment variables
docker run -d -p 5001:80 \
  -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
  -e AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
  -e AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-4" \
  resume-rag-admin
```

### ☁️ **Production Deployment**
- **Azure App Service**: Ready for cloud deployment
- **Container Registry**: Docker image support
- **Application Insights**: Monitoring and logging
- **HTTPS**: SSL/TLS encryption enabled

## Troubleshooting

### 🚨 **Common Issues**

**Database Connection Errors**
```bash
# Check ChromaDB path and permissions
ls -la ./resume_vectordb/
```

**Azure OpenAI Authentication**
```bash
# Verify environment variables
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_KEY
```

**Port Conflicts**
```bash
# Check if port 5001 is available
netstat -an | grep 5001
```

### 🔧 **Debug Mode**
```bash
# Enable detailed logging
export FLASK_DEBUG=True
python main.py
```

## Contributing

### 📋 **Development Setup**
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Run tests before submitting PRs

### 🧪 **Testing**
```bash
# Run test suite
python -m pytest tests/

# Run specific test
python -m pytest tests/test_admin_interface.py
```

## Security

### 🔒 **Best Practices**
- Environment-based configuration
- Secure API key management
- Input validation and sanitization
- HTTPS enforcement in production
- Container security scanning

## Performance

### ⚡ **Optimization**
- Async document processing
- Efficient vector search indexing
- Query result caching
- Database connection pooling
- Resource usage monitoring

---

**Built with ❤️ for intelligent resume management**

For more information, see the main project [README](../../README.md) and [deployment documentation](../../DEPLOYMENT.md).