# 📊 Vector Database Schema Documentation

## 🎯 Overview

The vector database schema is defined in **`ingest_pipeline.py`** in the `_create_resume_metadata()` method. The schema has two levels:

1. **Resume-level metadata** (applied to all chunks from a resume)
2. **Chunk-level metadata** (specific to each document chunk)

## 📋 Schema Definition Location

**Primary File**: `c:\Users\DamonDesonier\repos\langachain_rag\ingest_pipeline.py`

**Key Methods**:
- `_create_resume_metadata()` - Lines 294-379 (Resume-level schema)
- `add_resume()` - Lines 430-447 (Chunk-level metadata)
- `_create_semantic_chunks()` - Lines 272-279 (Section-level metadata)

## 🏗️ Complete Schema Structure

### Resume-Level Metadata (Base)
```python
# Core Resume Fields (Always Present)
{
    # Identity & File Info
    "Resume_ID": "unique_hash_based_on_filename",
    "Resume_Date": "2025-10-22T15:30:45.123456",
    "Source": "PDF resume" | "DOCX resume",
    "file_path": "/path/to/actual/file.pdf",
    "original_file_source": "/abs/path/to/original/file.pdf", 
    "display_filename": "clean_filename.pdf",
    "document_name": "clean_filename.pdf",
    
    # File Processing Info
    "content_type": "resume",
    "file_format": "PDF" | "DOCX",
    "last_updated": "2025-10-22T15:30:45.123456",
    "parsing_method": "llm_assisted" | "basic",
    "is_temp_file": true | false,
    
    # LLM-Extracted Fields (If Available)
    "candidate_name": "John Doe",
    "contact_info": "john.doe@email.com | (555) 123-4567",
    "key_skills": "Python, JavaScript, React, Node.js",
    "skills_count": 15,
    "experience_years": 8,
    "education": "B.S. Computer Science, MIT (2015)",
    "certifications": "AWS Certified, PMP Certified",
    "certifications_count": 2,
    "recent_job_titles": "Senior Software Engineer, Tech Lead",
    "industries": "Technology, Healthcare, Finance"
}
```

### Chunk-Level Metadata (Per Document Chunk)
```python
# Added to each chunk in add_resume() method
{
    # Chunk Identity
    "chunk_id": 0,  # Sequential number within resume
    "chunk_content": "First 100 chars of chunk content...",
    "total_chunks": 5,  # Total chunks for this resume
    
    # Chunk Classification
    "chunk_type": "semantic_section" | "traditional",
    
    # Section Info (For Semantic Chunks Only)
    "section_name": "Experience" | "Education" | "Skills",
    "section_order": 1,  # Order within resume
    
    # Update Tracking
    "update_timestamp": "2025-10-22T15:30:45.123456"  # If force_update=True
}
```

### Section-Level Metadata (Semantic Chunks)
```python
# Added during semantic chunking (_create_semantic_chunks)
{
    "section_name": "Professional Experience",
    "section_order": 2,
    "chunk_type": "semantic_section"
}
```

## 🔍 Schema Usage Patterns

### Document Structure
```
Resume Document
├── Resume-Level Metadata (shared by all chunks)
├── Chunk 1
│   ├── Content: "John Doe - Software Engineer..."
│   └── Metadata: Base + Chunk-specific + Section-specific
├── Chunk 2
│   ├── Content: "Experience: Senior Developer at..."
│   └── Metadata: Base + Chunk-specific + Section-specific
└── Chunk N...
```

### Metadata Hierarchy
1. **Base Resume Metadata** → Applied to ALL chunks from a resume
2. **Chunk-Level Metadata** → Specific to each chunk 
3. **Section Metadata** → Added for semantic sections (Experience, Skills, etc.)

## 📊 Field Types and Constraints

### Required Fields (Always Present)
- `Resume_ID` (string, unique hash)
- `Resume_Date` (ISO datetime string)
- `Source` (string, file type description)
- `file_path` (string, actual file path)
- `content_type` (string, always "resume")
- `file_format` (string, "PDF" or "DOCX")
- `chunk_id` (integer, 0-based index)
- `total_chunks` (integer, count of chunks)

### Optional Fields (LLM-Dependent)
- `candidate_name` (string)
- `contact_info` (string)
- `key_skills` (comma-separated string)
- `skills_count` (integer)
- `experience_years` (integer, 0 if parse fails)
- `education` (string)
- `certifications` (comma-separated string)
- `certifications_count` (integer)

### Enhanced Fields (Recent Additions)
- `display_filename` (clean filename for UI)
- `original_file_source` (absolute path to original)
- `is_temp_file` (boolean, tracks temp file usage)
- `section_name` (string, for semantic chunks)
- `section_order` (integer, section position)

## 🎯 Key Schema Features

### 1. **Temp File Handling**
- `is_temp_file`: Tracks if original was a temp file
- `display_filename`: Clean name for UI display
- `original_file_source`: Points to actual file location

### 2. **LLM Integration** 
- Conditional fields based on LLM extraction success
- Fallback values for parsing failures
- Rich candidate information when available

### 3. **Semantic Chunking**
- Section-aware metadata for better retrieval
- Hierarchical section information
- Chunk type classification

### 4. **Version Tracking**
- `last_updated`: When resume was processed
- `update_timestamp`: When chunk was updated
- `parsing_method`: Processing approach used

## 🔧 Schema Evolution

The schema has evolved through several enhancements:

1. **Original**: Basic file info and chunk data
2. **LLM Enhancement**: Added extracted candidate information  
3. **Temp File Fix**: Added clean filename handling
4. **Semantic Chunking**: Added section-aware metadata
5. **Source Tracking**: Enhanced file source management

## 📝 Usage Examples

### Querying by Metadata
```python
# Search by experience level
results = db.similarity_search(
    "python developer",
    filter={"experience_years": {"$gte": 5}}
)

# Filter by file format
results = db.similarity_search(
    "software engineer", 
    filter={"file_format": "PDF"}
)

# Find specific sections
results = db.similarity_search(
    "education background",
    filter={"section_name": "Education"}
)
```

### Accessing Metadata
```python
for doc in results:
    metadata = doc.metadata
    print(f"Candidate: {metadata.get('candidate_name', 'Unknown')}")
    print(f"Experience: {metadata.get('experience_years', 0)} years")
    print(f"Section: {metadata.get('section_name', 'N/A')}")
    print(f"File: {metadata.get('display_filename', 'N/A')}")
```

## 📍 Schema Location Summary

| Component | File | Method/Line | Purpose |
|-----------|------|-------------|---------|
| **Base Metadata** | `ingest_pipeline.py` | `_create_resume_metadata()` L294-379 | Resume-level fields |
| **Chunk Metadata** | `ingest_pipeline.py` | `add_resume()` L430-447 | Chunk-specific fields |
| **Section Metadata** | `ingest_pipeline.py` | `_create_semantic_chunks()` L272-279 | Semantic section info |
| **Temp File Handling** | `ingest_pipeline.py` | `_extract_original_filename()` L284-293 | Clean filename logic |

The vector database schema is **primarily defined in the `_create_resume_metadata()` method** with additional chunk-level enhancements applied during document processing.