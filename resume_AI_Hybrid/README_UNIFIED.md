# 🎯 Resume RAG System - Unified Configuration

## 📖 Overview

This Resume RAG system now supports **unified database access** across multiple interfaces:
- **Streamlit Interface**: Full-featured web UI for development and testing
- **OpenWebUI Interface**: Chat-based interface for production use
- **Both interfaces share the same ChromaDB vector database and Azure LLM configuration**

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Configuration                     │
│  ┌──────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Vector DB      │ │   Azure LLM     │ │   Embeddings    │ │
│  │  (ChromaDB)      │ │ (OpenAI GPT)    │ │ (HuggingFace)   │ │
│  └──────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           │                           │                    
           ▼                           ▼                    
┌─────────────────────┐      ┌─────────────────────┐
│  Streamlit          │      │  OpenWebUI          │
│  Interface          │      │  Interface          │
│                     │      │                     │
│  • Upload resumes   │      │  • Chat queries     │
│  • Process files    │      │  • Auto-detection   │
│  • Query database   │      │  • Ranking results  │
│  • Admin features   │      │  • Conflict res.    │
└─────────────────────┘      └─────────────────────┘
```

## 🚀 **Quick Start**

### 1. **Test Configuration**
```bash
# Test that both interfaces will use the same database
python test_unified_config.py
```

### 2. **Set Up Database**
```bash
# Create data directory and add resume files
mkdir data
# Copy your PDF/DOCX resume files to ./data/

# Process resumes into shared database
python common_tools/ingest_pipeline.py --directory ./data
```

### 3. **Run Streamlit Interface**
```bash
cd langchain
streamlit run streamlit_app.py
```
- Access at: http://localhost:8501
- Full development interface with upload, processing, and querying

### 4. **Run OpenWebUI Interface**
```bash
cd openUIWeb
python web_interface_fixed.py
```
- Access at: http://localhost:8005
- Chat-based interface with conflict resolution

## 🔧 **Configuration**

All configuration is centralized in `shared_config.py`:

### **Database Path**
- **Automatic Detection**: Finds existing database or creates new one
- **Environment Override**: Set `VECTOR_DB_PATH` to specify custom path
- **Default**: `./resume_vectordb` in project root

### **Azure OpenAI**
Required environment variables:
```bash
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_CHATGPT_DEPLOYMENT=your-chat-deployment
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### **Embeddings**
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Device**: CPU (configurable)
- **Normalization**: Enabled

## 🎯 **Key Features**

### **Unified Database Access**
- ✅ Both interfaces use identical ChromaDB instance
- ✅ Consistent embedding models across interfaces
- ✅ Same Azure LLM configuration
- ✅ Shared resume processing pipeline

### **Streamlit Interface**
- 📄 File upload and processing
- 🔍 Natural language queries
- 🎯 Candidate ranking and scoring
- 📊 Database statistics and management
- 💾 Resume listing and metadata viewing

### **OpenWebUI Interface**
- 💬 Chat-based interaction
- 🔍 Automatic query detection
- ⚡ Quick actions (stats, list, clear)
- 🛠️ ChromaDB conflict resolution
- 📱 Responsive design

## 🧪 **Testing**

### **Verify Unified Setup**
```bash
# Run comprehensive test
python test_unified_config.py

# Expected output:
# ✅ Configuration valid: Yes
# ✅ Database available: Yes  
# ✅ Component imports: Yes
# 🎉 SUCCESS: Both interfaces use the same database!
```

### **Test Database Consistency**
1. **Add data via Streamlit**:
   - Upload resumes through Streamlit interface
   - Note the database statistics

2. **Query via OpenWebUI**:
   - Switch to OpenWebUI interface
   - Query the same data
   - Verify same results

## 📁 **File Structure**

```
resume_AI_Hybrid/
├── shared_config.py              # 🔧 Unified configuration
├── test_unified_config.py        # 🧪 Configuration tester
├── data/                         # 📄 Resume files to process
├── resume_vectordb/              # 💾 Shared ChromaDB database
│
├── langchain/                    # 🖥️ Streamlit Interface
│   ├── streamlit_app.py         # Main Streamlit app
│   └── ingest_pipeline.py       # (symlink to common_tools/)
│
├── openUIWeb/                    # 💬 OpenWebUI Interface  
│   ├── query_app.py             # Query system
│   ├── web_interface_fixed.py   # FastAPI interface
│   └── README.md                # OpenWebUI docs
│
└── common_tools/                 # 🛠️ Shared Components
    ├── ingest_pipeline.py       # Resume processing
    ├── list_chromadb_files.py   # Database utilities
    └── openwebui-resume-rag-admin/ # Admin interface
```

## 🔍 **Usage Examples**

### **Streamlit Workflow**
1. Start Streamlit: `streamlit run langchain/streamlit_app.py`
2. Go to "Ingest" tab
3. Upload resume files or process directory
4. Go to "Query" tab  
5. Ask questions: "Show me top 5 Python developers"

### **OpenWebUI Workflow**
1. Start interface: `python openUIWeb/web_interface_fixed.py`
2. Click "Safe Connect with Auto-Detection"
3. Use actions: Database Stats, List Resumes
4. Chat naturally: "Find candidates with machine learning experience"

## 🚨 **Troubleshooting**

### **Database Path Issues**
```bash
# Check current configuration
python shared_config.py

# Verify both interfaces use same path
python test_unified_config.py
```

### **ChromaDB Conflicts**
```bash
# Use OpenWebUI conflict resolution
python openUIWeb/web_interface_fixed.py
# Click "Diagnose ChromaDB Settings"
```

### **Environment Issues**
```bash
# Check configuration
python -c "from shared_config import get_config; get_config().print_config_summary()"
```

## 🎉 **Success Criteria**

When properly configured, you should see:

1. **Same Database Path**: Both interfaces show identical database path
2. **Consistent Results**: Same queries return same results in both interfaces
3. **Shared Statistics**: Database stats match across interfaces
4. **Resume Sync**: Resumes added via one interface visible in the other

## 📞 **Next Steps**

1. **Run the test**: `python test_unified_config.py`
2. **Add resume data**: Copy files to `./data/` and process
3. **Test both interfaces**: Verify they show the same data
4. **Production use**: Choose the interface that fits your workflow best

Both interfaces now share the same underlying ChromaDB database and Azure LLM configuration! 🎯