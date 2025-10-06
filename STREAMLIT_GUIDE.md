# 🌐 Resume RAG System - Streamlit Web Interface

## 🚀 Quick Start

Launch the web application:
```bash
streamlit run streamlit_app.py
```

The app will open at: http://localhost:8501

## 📋 Features Overview

### 📥 **Ingest Tab**
Upload and process resume files into the vector database.

**Key Features:**
- ✅ **File Upload**: Drag & drop PDF/DOCX resume files
- ✅ **LLM-Assisted Parsing**: Toggle AI-powered content extraction
- ✅ **Batch Processing**: Upload multiple files at once
- ✅ **Force Update**: Override existing resumes
- ✅ **Real-time Progress**: Watch processing in real-time
- ✅ **Database Statistics**: View resume counts and chunks
- ✅ **Resume Listing**: Browse processed resumes

### 🔍 **Query Tab**
Search and query resume information with AI-powered responses.

**Key Features:**
- ✅ **Natural Language Queries**: Ask questions in plain English
- ✅ **Multiple Query Types**:
  - Search all resumes
  - Target specific resume by ID
  - Filter by file format (PDF/DOCX)
- ✅ **Source Documents**: See which resume chunks provided answers
- ✅ **Rich Metadata**: View section names, chunk types, and more
- ✅ **Database Overview**: Quick stats and resume listing

## 🎯 Usage Guide

### Step 1: Configure Environment
Ensure your `.env` file contains:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_API_VERSION=your_version
EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_CHATGPT_DEPLOYMENT=your_deployment
```

### Step 2: Ingest Resumes
1. Go to the **📥 Ingest** tab
2. Configure settings:
   - Set database path (default: `./resume_vectordb`)
   - Enable/disable LLM-assisted parsing
   - Choose force update if needed
3. Click **"Initialize Pipeline"**
4. Upload resume files (PDF/DOCX)
5. Click **"🚀 Process Files"**
6. Watch real-time processing progress

### Step 3: Query Resumes
1. Go to the **🔍 Query** tab
2. Click **"Initialize Query System"**
3. Enter your question in the text area
4. Choose query type:
   - **All Resumes**: Search across all documents
   - **Specific Resume**: Target one resume by ID
   - **Filter by Format**: Search only PDF or DOCX files
5. Click **"🔍 Search"**
6. Review the AI-generated answer and source documents

## 💡 Example Queries

### General Questions
- "What are Brandon's key skills and technical expertise?"
- "How many years of experience does this candidate have?"
- "What certifications does Brandon hold?"
- "What is Brandon's educational background?"

### Specific Searches
- "Find candidates with cybersecurity experience"
- "Who has Security+ certification?"
- "Show me penetration testing skills"
- "What programming languages are mentioned?"

### Metadata Searches
- Search only PDF resumes: Use "Filter by Format" → PDF
- Target specific resume: Use Resume ID from ingest tab
- Find recent job titles or contact information

## 🔧 Advanced Features

### 🤖 LLM-Assisted Parsing
When enabled, the system extracts:
- **Candidate Name**: Full name identification
- **Contact Info**: Email, phone, location
- **Key Skills**: Technical and professional skills
- **Experience Years**: Estimated total experience
- **Education**: Degree and institution
- **Certifications**: Professional credentials
- **Job Titles**: Recent positions
- **Industries**: Relevant domains

### 📊 Rich Metadata
Each resume chunk includes:
```json
{
  "candidate_name": "Brandon J. Tobalski",
  "key_skills": "Cybersecurity, Leadership...",
  "experience_years": 13,
  "section_name": "Core Competencies",
  "chunk_type": "semantic_section",
  "parsing_method": "llm_assisted"
}
```

### 🎯 Semantic Chunking
Instead of arbitrary splits, creates logical sections:
- Contact Information
- Professional Summary
- Core Competencies  
- Work Experience
- Education & Training
- Certifications

## 🛠️ Sidebar Controls

### Configuration Panel
- ✅ **Environment Check**: Validates required Azure OpenAI settings
- 🗑️ **Clear Database**: Remove all processed resumes
- 📊 **Quick Stats**: Database overview

### Database Management
- **Initialize Systems**: Set up ingest/query pipelines
- **View Statistics**: Resume counts, chunk statistics
- **List Resumes**: Browse processed documents
- **Clear Data**: Fresh start option

## 🚨 Troubleshooting

### Common Issues

**"Missing environment variables"**
- Check `.env` file exists and contains required Azure OpenAI settings
- Restart Streamlit after updating environment

**"Failed to initialize ingest pipeline"**
- Verify Azure OpenAI credentials are correct
- Check network connectivity
- Try disabling LLM parsing for faster setup

**"Database not found"**
- Run ingest process first before querying
- Check database path is correct
- Initialize ingest pipeline before query system

**Upload errors**
- Ensure files are PDF or DOCX format
- Check file sizes aren't too large
- Verify files aren't corrupted

### Performance Tips

**For Faster Processing:**
- Disable LLM-assisted parsing for speed
- Process files in smaller batches
- Use simpler resume formats

**For Better Results:**
- Enable LLM-assisted parsing
- Use well-formatted resumes
- Include complete contact and experience information

## 🎉 Benefits

### User Experience
- 🌐 **Web Interface**: No command-line needed
- 📱 **Responsive Design**: Works on desktop and mobile
- 🔄 **Real-time Updates**: Live progress and results
- 📊 **Visual Statistics**: Charts and metrics

### Functionality
- 🤖 **AI-Powered**: LLM extraction and semantic search
- 📁 **Batch Processing**: Handle multiple files efficiently
- 🔍 **Advanced Search**: Multiple query types and filters
- 📚 **Source Attribution**: See exactly where answers come from

### Productivity  
- ⚡ **Quick Setup**: Initialize with one click
- 🎯 **Targeted Queries**: Find specific information fast
- 📈 **Database Management**: Easy monitoring and maintenance
- 🔄 **Iterative Workflow**: Ingest more, query immediately

Launch the app and start building your intelligent resume database! 🚀