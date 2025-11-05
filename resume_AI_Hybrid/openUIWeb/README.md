# Resume RAG System - OpenWebUI Version

A comprehensive Resume Retrieval-Augmented Generation (RAG) system converted from Streamlit to OpenWebUI. This system allows you to upload, process, and intelligently query resume documents using AI-powered search and ranking capabilities.

## 🚀 Features

### Core Functionality
- **📄 Document Processing**: Upload and process PDF and DOCX resume files
- **🤖 AI-Powered Analysis**: Extract structured information using LLM-assisted parsing
- **🔍 Intelligent Search**: Natural language querying across resume database
- **🎯 Candidate Ranking**: Automated candidate scoring and ranking for specific queries
- **📊 Database Management**: Statistics, listing, and administration tools

### OpenWebUI Integration
- **🔌 Native Filters**: Automatic query processing for resume-related questions
- **⚡ Actions**: Direct commands for system management and data operations
- **💬 Natural Interface**: Chat-based interaction for all functionality
- **📱 Responsive Design**: Works seamlessly within OpenWebUI's interface

## 📋 Requirements

### Environment Variables
Create a `.env` file with the following Azure OpenAI configuration:

```env
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_CHATGPT_DEPLOYMENT=your_gpt_deployment_name
```

### Dependencies
Install required packages:

```bash
pip install -r requirements.txt
```

## 🛠️ Installation

### For OpenWebUI Integration

1. **Clone/Copy Files**: Place all Python files in your OpenWebUI custom functions directory
2. **Install Dependencies**: Ensure all required packages are available in your OpenWebUI environment
3. **Configure Environment**: Set up the required Azure OpenAI environment variables
4. **Register Functions**: Import the filters and actions in your OpenWebUI configuration

### Standalone Testing

```bash
# Clone the repository
git clone <repository-url>
cd OpenWebUI_Sage

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Test the system
python main.py
```

## 📖 Usage

### Getting Started

1. **Initialize the System**
   ```
   Initialize System
   ```
   This sets up both the ingest pipeline and query system.

2. **Upload Resume Files**
   Use OpenWebUI's file upload feature or the upload action to add PDF/DOCX resume files.

3. **Query the Database**
   Ask natural language questions about the resumes:
   ```
   "Show me the top 5 candidates for a Python developer role"
   "What are John's technical skills?"
   "Find candidates with machine learning experience"
   ```

### Available Commands

#### System Management
- **Database Stats**: View current database statistics
- **List Resumes**: Show all resumes in the database  
- **Clear Database**: Remove all data (use with caution)
- **Help**: Display detailed usage instructions

#### Query Examples

**General Queries:**
- "What programming languages do our candidates know?"
- "Who has the most experience with cloud technologies?"
- "Show me candidates with certification in AWS"

**Ranking Queries:**
- "Top 5 candidates for a senior developer position"
- "Best matches for a data scientist role"
- "Rank candidates by their machine learning experience"

**Specific Queries:**
- "Tell me about candidate ID abc123"
- "What's the educational background of our Python developers?"

## 🏗️ Architecture

### File Structure
```
├── main.py                     # Core system class and utilities
├── openwebui_integration.py    # OpenWebUI filters and actions
├── mock_ingest_pipeline.py     # Document processing pipeline
├── mock_query_app.py          # Query and ranking system
├── requirements.txt           # Python dependencies
└── README.md                 # This documentation
```

### System Components

1. **ResumeRAGSystem** (`main.py`)
   - Main system orchestrator
   - Environment validation
   - System initialization and configuration

2. **OpenWebUI Integration** (`openwebui_integration.py`)
   - Filters for automatic query processing
   - Actions for direct system commands
   - Response formatting for chat interface

3. **Ingest Pipeline** (`mock_ingest_pipeline.py`)
   - File upload and processing
   - Text extraction from PDF/DOCX
   - Document chunking and metadata storage

4. **Query System** (`mock_query_app.py`)
   - Natural language search
   - Candidate ranking and scoring
   - Result formatting and presentation

### Data Flow

1. **Upload**: Resume files → Text extraction → Chunking → Vector storage
2. **Query**: User question → Relevance search → LLM processing → Formatted response
3. **Ranking**: Query → All candidates → Scoring algorithm → Ranked list

## ⚙️ Configuration

### Database Settings
- **Default Path**: `./resume_vectordb`
- **Supported Formats**: PDF, DOCX
- **Chunking**: Automatic paragraph-based segmentation
- **Metadata**: File format, sections, timestamps

### LLM Processing
- **Structured Extraction**: Contact info, skills, experience
- **Section Identification**: Education, experience, skills, certifications
- **Scoring Algorithm**: Keyword matching + structured data analysis

### OpenWebUI Settings
- **Auto-detection**: Resume queries automatically processed
- **Filters**: `initialize_system`, `resume_query`
- **Actions**: `database_stats`, `list_resumes`, `upload_resume`, `clear_database`, `help`

## 🔧 Customization

### Adding New Document Types
Extend `_extract_text_from_file()` in `mock_ingest_pipeline.py`:

```python
elif file_ext == '.txt':
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
```

### Modifying Ranking Algorithm
Update `query_with_ranking()` in `mock_query_app.py`:

```python
# Add new scoring factors
total_score += custom_scoring_function(resume, query)
```

### Custom Query Types
Add new query patterns in `resume_query_filter()`:

```python
custom_indicators = ["specific", "keywords", "here"]
is_custom_query = any(indicator in content_lower for indicator in custom_indicators)
```

## 🧪 Testing

### Mock Data
The system includes mock implementations that generate sample resume data for testing:
- **Sample Candidates**: John Doe (Software Engineer), Jane Smith (Data Scientist)
- **Mock Skills**: Python, JavaScript, Machine Learning, etc.
- **Sample Experience**: Realistic job histories and education

### Running Tests
```bash
# Test system initialization
python -c "from main import resume_rag_system; print(resume_rag_system.validate_environment())"

# Test query processing
python -c "from openwebui_integration import resume_query_filter; print('Filter loaded successfully')"
```

## 🚨 Important Notes

### Mock Implementation
- **Development Version**: Current implementation uses mock data for demonstration
- **Production Ready**: Replace mock modules with actual `ingest_pipeline.py` and `query_app.py`
- **Azure OpenAI**: Requires valid Azure OpenAI credentials for full functionality

### Security Considerations
- **Environment Variables**: Keep Azure OpenAI keys secure
- **File Uploads**: Validate file types and sizes
- **Database Access**: Implement proper access controls

### Performance
- **File Size**: Large PDFs may take longer to process
- **Concurrent Users**: Consider database locking for multiple users
- **Memory Usage**: Monitor memory with large document collections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Environment Variables Not Found**
- Ensure `.env` file is in the project root
- Check variable names match exactly
- Restart the application after changes

**File Upload Errors**
- Verify file format (PDF/DOCX only)
- Check file permissions
- Ensure sufficient disk space

**Query Failures**
- Initialize the system first
- Check database has resumes
- Verify Azure OpenAI connection

### Getting Help
- Check the help action: `Help`
- Review the console logs for error details
- Ensure all dependencies are installed correctly

---

**Built with ❤️ for OpenWebUI** | Converted from Streamlit Resume RAG System