# File Source Path Display Fix

## Overview
Fixed the issue where file sources were showing temporary paths like `C:\Users\DAMOND~1\AppData\Local\Temp\tmpm_jrdy5q.docx` instead of proper data directory paths like `./data/Brandon_Click_7-4-2025.docx`.

## Problem Description

### Before Fix
When files were uploaded through Streamlit or processed through the system, the source paths displayed:
- Temporary file paths: `C:\Users\DAMOND~1\AppData\Local\Temp\tmpm_jrdy5q.docx`
- Confusing for users trying to locate original files
- No clear indication of the actual file name or location

### After Fix
The same files now display:
- Clean data directory paths: `./data/Brandon_Click_7-4-2025.docx`
- Original filename preserved
- Clear indication of file location

## Technical Implementation

### 🔧 Enhanced Ingest Pipeline

#### Updated Method Signature
```python
def add_resume(self, file_path, force_update=False, original_filename=None):
```

#### New Parameters
- `original_filename`: Optional parameter to preserve the original file name and path
- Used when files are uploaded through Streamlit to maintain proper naming

#### Enhanced Metadata Schema
```python
metadata = {
    # ... existing fields ...
    "file_path": file_path,  # Actual file location (may be temp)
    "original_file_source": os.path.abspath(original_filename) if original_filename else os.path.abspath(file_path),
    "display_filename": file_name,  # Original filename for display
    # ... other fields ...
}
```

### 📱 Streamlit Integration

#### File Upload Enhancement
```python
# Process file with original filename preservation
success, resume_id, chunk_count = st.session_state.ingest_pipeline.add_resume(
    tmp_path, 
    force_update=force_update,
    original_filename=f"./data/{uploaded_file.name}"  # Preserve original path
)
```

#### Smart Display Logic
```python
# Use display filename for better source path
display_source = resume.get('original_file_source', resume.get('file_path', ''))
if resume.get('display_filename'):
    display_source = f"./data/{resume.get('display_filename')}"
```

### 🖥️ Query System Updates

#### Enhanced Source Display
```python
# Show proper source path in command line
display_source = resume.get('original_file_source', resume.get('file_path', 'Unknown'))
if resume.get('display_filename'):
    display_source = f"./data/{resume.get('display_filename')}"
print(f"   📂 Source: {display_source}")
```

#### Ranking Data Collection
```python
# Include display filename in ranking results
resume_info = {
    # ... existing fields ...
    'display_filename': first_doc.metadata.get('display_filename', ''),
    # ... other fields ...
}
```

## Benefits

### 🎯 User Experience
- **Clear File Paths**: Users see `./data/Brandon_Click_7-4-2025.docx` instead of temp paths
- **Original Names**: Preserves meaningful file names for easy identification
- **Consistent Display**: Same clean paths across command line and web interface

### 🔧 Technical Advantages
- **Backward Compatible**: Existing files continue to work
- **Flexible Processing**: Handles both direct files and uploaded files
- **Proper Metadata**: Clean separation between processing paths and display paths

### 📊 Data Integrity
- **Source Tracking**: Maintains link to original file location
- **Download Support**: Download buttons work with proper file resolution
- **Audit Trail**: Clear record of file origins

## Implementation Details

### New Metadata Fields
1. **`display_filename`**: Original filename for UI display
2. **Enhanced `original_file_source`**: Proper absolute path handling
3. **Smart path resolution**: Automatic fallback logic

### File Processing Flow
1. **File Upload**: Streamlit saves to temp location
2. **Metadata Creation**: Original filename passed to ingest pipeline
3. **Path Preservation**: Display paths use original names
4. **UI Display**: Shows clean `./data/filename.ext` format

### Display Logic
```python
# Priority order for source display:
1. ./data/{display_filename} (if display_filename exists)
2. original_file_source (if available)
3. file_path (fallback)
```

## Test Results

### Before Fix
```
Source: C:\Users\DAMOND~1\AppData\Local\Temp\tmpm_jrdy5q.docx
```

### After Fix
```
Source: ./data/Brandon_Click_7-4-2025.docx
```

### Verification Test
**Newly Ingested File**:
- `file_path`: `./data/Brandon_Tobalski_1-28-2022.pdf`
- `display_filename`: `Brandon_Tobalski_1-28-2022.pdf`
- `Display shows`: `./data/Brandon_Tobalski_1-28-2022.pdf` ✅

**Legacy Files**: Continue to work with graceful fallback

## Usage Instructions

### For New Files
1. **Direct Ingestion**: Files automatically use proper paths
2. **Streamlit Upload**: Original filenames preserved automatically
3. **Command Line**: Use normal ingestion commands

### For Existing Files
1. **Automatic Fallback**: Old files continue to work
2. **Re-ingestion**: Use `--force-update` to get enhanced paths
3. **Gradual Migration**: New uploads get improved paths

### Path Display Format
- **Data Directory Files**: `./data/filename.ext`
- **Direct Path Files**: Full absolute path
- **Temp Files**: Graceful fallback to available path

## Migration Strategy

### Immediate Benefits
- ✅ All new file uploads show proper paths
- ✅ Streamlit interface displays clean source references
- ✅ Command line ranking shows meaningful file names

### Gradual Improvement
- ♻️ Re-upload files through Streamlit for enhanced paths
- 🔄 Use `--force-update` flag for command-line re-ingestion
- 📈 Natural migration as files are updated

The fix provides immediate improvement for new files while maintaining full backward compatibility with existing data.