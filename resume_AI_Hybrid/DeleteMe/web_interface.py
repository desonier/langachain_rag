"""
Enhanced Web Interface with Database Selection and Creation
Supports existing databases and creating new ones
"""
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv  # Add this import
import uvicorn
import os
import tempfile
import json
import traceback
import gc
import time
import threading
from typing import List, Optional
from pathlib import Path
from datetime import datetime


# Import our Resume RAG System
from query_app import ResumeQuerySystem

# Initialize the query system globally
resume_rag_system = None

def format_resume_response(query_result):
    """Format the query result for display"""
    if not query_result.get("success", False):
        return "No results found."
    
    formatted_text = ""
    
    # Add answer if available
    if "answer" in query_result:
        formatted_text += f"**Answer:** {query_result['answer']}\n\n"
    
    # Add source documents if available
    if "source_documents" in query_result and query_result["source_documents"]:
        formatted_text += "**Sources:**\n"
        for i, doc in enumerate(query_result["source_documents"][:3], 1):  # Limit to 3 sources
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            source_info = metadata.get('source', 'Unknown source')
            formatted_text += f"{i}. {content}\n   Source: {source_info}\n\n"
    
    # Add ranking results if available
    if "ranking_results" in query_result and query_result["ranking_results"]:
        formatted_text += "**Top Matches:**\n"
        for i, result in enumerate(query_result["ranking_results"][:3], 1):  # Limit to 3 results
            name = result.get('resume_name', 'Unknown')
            score = result.get('fit_score', 0)
            summary = result.get('fit_summary', 'No summary available')
            formatted_text += f"{i}. **{name}** (Score: {score:.1f}%)\n   {summary}\n\n"
    
    return formatted_text if formatted_text else "Results found but no content to display."

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Resume RAG System", description="AI-Powered Resume Search and Analysis - ChromaDB Enhanced")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Global lock for ChromaDB operations
chromadb_lock = threading.Lock()
_initializing = False

class ChromaDBInstanceManager:
    """Enhanced ChromaDB instance manager to prevent conflicts"""
    
    def __init__(self):
        self.active_connections = {}
        self.lock = threading.Lock()
    
    def cleanup_all_instances(self):
        """Cleanup all ChromaDB instances with enhanced error handling"""
        with self.lock:
            try:
                print("🧹 Enhanced ChromaDB cleanup starting...")
                
                # Step 1: Clear any cached ChromaDB clients
                try:
                    import chromadb
                    if hasattr(chromadb, '_client_cache'):
                        chromadb._client_cache.clear()
                    if hasattr(chromadb, '_global_client'):
                        chromadb._global_client = None
                except Exception as e:
                    print(f"Warning: ChromaDB cache cleanup: {e}")
                
                # Step 2: Reset resume_rag_system connections
                try:
                    resume_rag_system.ingest_pipeline = None
                    resume_rag_system.query_system = None
                    
                    # Clear any vectorstore references
                    if hasattr(resume_rag_system, 'vectorstore'):
                        resume_rag_system.vectorstore = None
                    
                    # Clear ChromaDB manager if it exists
                    if hasattr(resume_rag_system, '_chromadb_manager'):
                        if resume_rag_system._chromadb_manager:
                            try:
                                resume_rag_system._chromadb_manager.close()
                            except:
                                pass
                        resume_rag_system._chromadb_manager = None
                        
                except Exception as e:
                    print(f"Warning: System state cleanup: {e}")
                
                # Step 3: Force garbage collection
                gc.collect()
                
                # Step 4: Wait for cleanup to complete
                time.sleep(1)
                
                print("✅ Enhanced ChromaDB cleanup completed")
                return True
                
            except Exception as e:
                print(f"❌ ChromaDB cleanup error: {e}")
                return False
    
    def safe_initialize(self, database_path=None, create_new=False, max_retries=3):
        """Safely initialize ChromaDB with conflict resolution and database creation"""
        with self.lock:
            for attempt in range(max_retries):
                try:
                    print(f"🔄 ChromaDB initialization attempt {attempt + 1}/{max_retries}")
                    
                    # Cleanup before each attempt
                    self.cleanup_all_instances()
                    
                    # Wait longer between attempts
                    if attempt > 0:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    
                    # Set database path if provided
                    if database_path:
                        if create_new:
                            # Ensure the directory exists for new databases
                            db_path = Path(database_path)
                            db_path.mkdir(parents=True, exist_ok=True)
                            print(f"📁 Created/ensured database directory: {database_path}")
                        
                        resume_rag_system.db_path = database_path
                        
                        # Re-detect ChromaDB sharing for the path
                        if hasattr(resume_rag_system, '_detect_chromadb_sharing'):
                            resume_rag_system._detect_chromadb_sharing()
                    
                    # Try robust initialization first
                    if hasattr(resume_rag_system, 'initialize_ingest_pipeline_robust'):
                        print("🔧 Using robust initialization method...")
                        ingest_result = resume_rag_system.initialize_ingest_pipeline_robust()
                        if ingest_result.get("success", False):
                            query_result = resume_rag_system.initialize_query_system_robust()
                        else:
                            query_result = {"success": False, "message": "Ingest failed"}
                    else:
                        print("🔧 Using standard initialization method...")
                        ingest_result = resume_rag_system.initialize_ingest_pipeline()
                        if ingest_result.get("success", False):
                            query_result = resume_rag_system.initialize_query_system()
                        else:
                            query_result = {"success": False, "message": "Ingest failed"}
                    
                    # Check if both succeeded
                    if ingest_result.get("success", False) and query_result.get("success", False):
                        print("✅ ChromaDB initialization successful!")
                        return {
                            "success": True,
                            "message": "✅ System initialized successfully!" + (" (New database created)" if create_new else ""),
                            "database_path": resume_rag_system.db_path,
                            "collection_name": resume_rag_system.collection_name,
                            "attempt": attempt + 1,
                            "created_new": create_new
                        }
                    else:
                        error_msg = f"Attempt {attempt + 1} failed - Ingest: {ingest_result.get('message', 'Unknown')}, Query: {query_result.get('message', 'Unknown')}"
                        print(f"❌ {error_msg}")
                        
                        if attempt == max_retries - 1:
                            return {
                                "success": False,
                                "message": f"❌ All {max_retries} initialization attempts failed. Last error: {error_msg}"
                            }
                
                except Exception as e:
                    error_msg = f"Initialization attempt {attempt + 1} exception: {str(e)}"
                    print(f"❌ {error_msg}")
                    
                    if attempt == max_retries - 1:
                        return {
                            "success": False,
                            "message": f"❌ Initialization failed after {max_retries} attempts: {str(e)}"
                        }
            
            return {
                "success": False,
                "message": "❌ Unexpected initialization failure"
            }

# Global instance manager
chromadb_manager = ChromaDBInstanceManager()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page with enhanced ChromaDB handling and database selection"""
    try:
        # Get available databases
        available_databases = get_available_databases()
        
        # Check current system status
        system_connected = (resume_rag_system.ingest_pipeline is not None and 
                           resume_rag_system.query_system is not None)
        
        print(f"🔍 System status check: connected={system_connected}")
        
        # Get current database info if connected
        current_db_info = None
        database_stats = None
        
        if system_connected:
            try:
                stats_result = resume_rag_system.get_database_stats()
                if stats_result.get("success", False):
                    current_db_info = {
                        "path": resume_rag_system.db_path,
                        "stats": stats_result["summary"]
                    }
                    database_stats = stats_result["summary"]
            except Exception as e:
                print(f"Warning: Could not get database stats: {e}")
        
        # Check environment status
        env_status = {
            "valid": bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY")),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "Not configured"),
            "azure_key": "***" if os.getenv("AZURE_OPENAI_API_KEY") else "Not configured",
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "Not configured"),
            "azure_api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        }
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "available_databases": available_databases,
            "current_db_info": current_db_info,
            "system_connected": system_connected,
            "system_initialized": system_connected,
            "env_status": env_status,
            "database_stats": database_stats,
            "stats": database_stats,
            "system_ready": system_connected and env_status["valid"]
        })
        
    except Exception as e:
        print(f"Error in home endpoint: {e}")
        traceback.print_exc()
        return HTMLResponse(
            content=f"<html><body><h1>Error loading page</h1><p>{str(e)}</p><p>Try refreshing the page or initializing the system.</p></body></html>",
            status_code=500
        )

def get_available_databases():
    """Scan for available ChromaDB databases and add option to create new"""
    databases = []
    
    try:
        # Search paths for ChromaDB databases
        search_paths = [
            Path("C:/Users/DamonDesonier/repos/langachain_rag/resume_vectordb"),  # Your main database
            Path("."),
            Path("./data"),
            Path("./databases"),
            Path("../langachain_rag/resume_vectordb"),
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                # Look for chroma.sqlite3 files
                for db_file in search_path.rglob("chroma.sqlite3"):
                    db_path = db_file.parent
                    try:
                        size_mb = round(db_file.stat().st_size / (1024 * 1024), 2)
                        modified_time = datetime.fromtimestamp(db_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                        
                        databases.append({
                            "name": db_path.name,
                            "path": str(db_path),
                            "size_mb": size_mb,
                            "modified": modified_time,
                            "is_current": str(db_path) == getattr(resume_rag_system, 'db_path', ''),
                            "display_name": f"{db_path.name} ({size_mb} MB) - Modified: {modified_time}",
                            "type": "existing"
                        })
                    except Exception as e:
                        print(f"Warning: Could not process database at {db_path}: {e}")
                        continue
        
        # Sort by most recently modified
        try:
            databases.sort(key=lambda x: Path(x["path"]).stat().st_mtime, reverse=True)
        except Exception as e:
            print(f"Warning: Could not sort databases: {e}")
        
        # Add option to create new database
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_db_options = [
            {
                "name": "new_database",
                "path": f"./databases/resume_db_{timestamp}",
                "size_mb": 0,
                "modified": "New",
                "is_current": False,
                "display_name": "📝 Create New Database",
                "type": "create_new"
            },
            {
                "name": "custom_path",
                "path": "custom",
                "size_mb": 0,
                "modified": "Custom",
                "is_current": False,
                "display_name": "📁 Specify Custom Path",
                "type": "custom"
            }
        ]
        
        # Add new database options at the beginning
        databases = new_db_options + databases
        
    except Exception as e:
        print(f"Error scanning for databases: {e}")
    
    return databases

@app.post("/api/initialize")
async def initialize_system(
    database_path: Optional[str] = Form(None),
    custom_path: Optional[str] = Form(None),
    create_new: bool = Form(False)
):
    """Initialize system with database selection and creation options"""
    global _initializing
    
    if _initializing:
        return JSONResponse({
            "success": False,
            "message": "⏳ System is already being initialized, please wait..."
        })
    
    try:
        _initializing = True
        print("🚀 Enhanced initialization with database selection requested...")
        
        # Determine the target database path
        target_path = None
        create_new_db = False
        
        if database_path:
            if database_path == "custom" and custom_path:
                target_path = custom_path.strip()
                create_new_db = True
                print(f"📁 Using custom database path: {target_path}")
            elif database_path.startswith("./databases/resume_db_"):
                target_path = database_path
                create_new_db = True
                print(f"📝 Creating new database: {target_path}")
            else:
                target_path = database_path
                create_new_db = False
                print(f"🔌 Connecting to existing database: {target_path}")
        
        # Check if already initialized with the same database
        if (resume_rag_system.ingest_pipeline is not None and 
            resume_rag_system.query_system is not None and
            target_path and str(resume_rag_system.db_path) == target_path):
            print("✅ System already initialized with selected database")
            return JSONResponse({
                "success": True,
                "message": "✅ System is already initialized with the selected database!",
                "database_path": resume_rag_system.db_path,
                "collection_name": resume_rag_system.collection_name
            })
        
        # Validate custom path if provided
        if target_path and create_new_db:
            try:
                target_path_obj = Path(target_path)
                if not target_path_obj.is_absolute():
                    target_path_obj = Path.cwd() / target_path
                target_path = str(target_path_obj)
                
                # For new databases, ensure parent directory exists
                target_path_obj.parent.mkdir(parents=True, exist_ok=True)
                print(f"✅ Validated target path: {target_path}")
            except Exception as e:
                return JSONResponse({
                    "success": False,
                    "message": f"❌ Invalid database path: {str(e)}"
                }, status_code=400)
        
        # Use enhanced initialization
        result = chromadb_manager.safe_initialize(
            database_path=target_path,
            create_new=create_new_db,
            max_retries=3
        )
        
        if result["success"]:
            # Get stats after successful initialization
            try:
                stats_result = resume_rag_system.get_database_stats()
                stats = stats_result.get("summary", {}) if stats_result.get("success", False) else {}
                result["stats"] = stats
            except Exception as e:
                print(f"Warning: Could not get stats after initialization: {e}")
                result["stats"] = {}
            
            return JSONResponse(result)
        else:
            return JSONResponse(result, status_code=500)
            
    except Exception as e:
        error_msg = f"❌ Unexpected initialization error: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": error_msg
        }, status_code=500)
    finally:
        _initializing = False

@app.post("/api/cleanup-chromadb")
async def cleanup_chromadb_endpoint():
    """Enhanced ChromaDB cleanup endpoint"""
    try:
        print("🧹 Manual ChromaDB cleanup requested...")
        cleanup_success = chromadb_manager.cleanup_all_instances()
        
        return JSONResponse({
            "success": cleanup_success,
            "message": "✅ Enhanced ChromaDB cleanup completed" if cleanup_success else "⚠️ ChromaDB cleanup completed with warnings"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"❌ ChromaDB cleanup failed: {str(e)}"
        }, status_code=500)

@app.post("/api/connect-database")
async def connect_database(database_path: str = Form(...)):
    """Connect to database with enhanced conflict resolution"""
    try:
        print(f"🔌 Enhanced database connection to: {database_path}")
        
        # Handle special cases
        if database_path == "custom":
            return JSONResponse({
                "success": False,
                "message": "❌ Please specify a custom path"
            }, status_code=400)
        
        # Check if it's a new database creation request
        create_new = database_path.startswith("./databases/resume_db_")
        
        if not create_new:
            # Validate existing database path
            db_path = Path(database_path)
            if not db_path.exists():
                return JSONResponse({
                    "success": False,
                    "message": f"❌ Database path does not exist: {database_path}"
                }, status_code=400)
            
            # Check for ChromaDB file
            chroma_file = db_path / "chroma.sqlite3"
            if not chroma_file.exists():
                return JSONResponse({
                    "success": False,
                    "message": f"❌ No ChromaDB database found at: {database_path}"
                }, status_code=400)
        
        # Enhanced cleanup and connection
        with chromadb_lock:
            # Store old path for rollback
            old_path = resume_rag_system.db_path
            
            # Cleanup existing connections
            print("🧹 Cleaning up before database switch...")
            chromadb_manager.cleanup_all_instances()
            time.sleep(2)
            
            # Initialize with database using enhanced method
            try:
                result = chromadb_manager.safe_initialize(
                    database_path=database_path,
                    create_new=create_new,
                    max_retries=2
                )
                
                if result["success"]:
                    # Get stats for the database
                    try:
                        stats_result = resume_rag_system.get_database_stats()
                        stats = stats_result.get("summary", {}) if stats_result.get("success", False) else {}
                    except Exception as e:
                        print(f"Warning: Could not get stats: {e}")
                        stats = {}
                    
                    db_path_obj = Path(database_path)
                    return JSONResponse({
                        "success": True,
                        "message": f"✅ {'Created and connected to' if create_new else 'Connected to'} database: {db_path_obj.name}",
                        "database_info": {
                            "path": database_path,
                            "name": db_path_obj.name,
                            "stats": stats,
                            "created_new": create_new
                        }
                    })
                else:
                    # Rollback on failure
                    resume_rag_system.db_path = old_path
                    chromadb_manager.cleanup_all_instances()
                    return JSONResponse({
                        "success": False,
                        "message": f"❌ Failed to connect: {result['message']}"
                    }, status_code=500)
                    
            except Exception as init_error:
                # Rollback on exception
                resume_rag_system.db_path = old_path
                chromadb_manager.cleanup_all_instances()
                raise init_error
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"❌ Database connection error: {str(e)}"
        }, status_code=500)

@app.get("/api/databases")
async def list_databases():
    """Get list of available databases with metadata and creation options"""
    try:
        databases = get_available_databases()
        
        # Add current connection status
        current_db = getattr(resume_rag_system, 'db_path', None)
        
        return JSONResponse({
            "success": True,
            "databases": databases,
            "current_database": current_db,
            "total_found": len([db for db in databases if db["type"] == "existing"]),
            "total_options": len(databases)
        })
    except Exception as e:
        print(f"Error listing databases: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error listing databases: {str(e)}",
            "databases": [],
            "total_found": 0,
            "total_options": 0
        })

# Keep all your existing endpoints unchanged
@app.get("/api/database-status")
async def get_database_status():
    """Get current database connection status and basic info"""
    try:
        system_ready = (resume_rag_system.ingest_pipeline is not None and 
                       resume_rag_system.query_system is not None)
        
        if not system_ready:
            return JSONResponse({
                "success": False,
                "connected": False,
                "message": "No database connected",
                "database_path": resume_rag_system.db_path,
                "collection_name": getattr(resume_rag_system, 'collection_name', 'unknown')
            })
        
        try:
            stats_result = resume_rag_system.get_database_stats()
            db_path = Path(resume_rag_system.db_path) if resume_rag_system.db_path else None
            
            return JSONResponse({
                "success": True,
                "connected": True,
                "database_name": db_path.name if db_path else "Unknown",
                "database_path": str(db_path) if db_path else "Unknown",
                "collection_name": resume_rag_system.collection_name,
                "stats": stats_result.get("summary", {}) if stats_result.get("success", False) else {},
                "collections": stats_result.get("collections", []) if stats_result.get("success", False) else []
            })
        except Exception as stats_error:
            print(f"Error getting stats in status check: {stats_error}")
            return JSONResponse({
                "success": True,
                "connected": True,
                "database_name": "Connected (stats unavailable)",
                "database_path": resume_rag_system.db_path,
                "collection_name": resume_rag_system.collection_name,
                "stats": {},
                "collections": [],
                "error": str(stats_error)
            })
    except Exception as e:
        print(f"Error getting database status: {e}")
        return JSONResponse({
            "success": False,
            "connected": False,
            "message": f"Error getting database status: {str(e)}"
        })

@app.get("/api/stats")
async def get_database_stats():
    """Get database statistics with error handling"""
    try:
        if not resume_rag_system.ingest_pipeline or not resume_rag_system.query_system:
            return JSONResponse({
                "success": False,
                "message": "System not initialized. Please initialize first.",
                "requires_initialization": True
            }, status_code=400)
        
        stats_result = resume_rag_system.get_database_stats()
        return JSONResponse(stats_result)
        
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error getting database stats: {str(e)}"
        }, status_code=500)

@app.get("/api/resumes")
async def list_resumes():
    """List all resumes in the current database"""
    try:
        if not resume_rag_system.ingest_pipeline:
            return JSONResponse({
                "success": False,
                "message": "No database connected. Please initialize the system first."
            }, status_code=400)
        
        list_result = resume_rag_system.list_resumes()
        return JSONResponse(list_result)
    except Exception as e:
        print(f"Error listing resumes: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error listing resumes: {str(e)}"
        }, status_code=500)

@app.post("/api/upload")
async def upload_resume(files: List[UploadFile] = File(...)):
    """Upload and process resume files"""
    try:
        if not resume_rag_system.ingest_pipeline:
            return JSONResponse({
                "success": False,
                "message": "No database connected. Please initialize the system first."
            }, status_code=400)
        
        results = []
        supported_extensions = ('.pdf', '.docx', '.txt')
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith(supported_extensions):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"❌ Unsupported file type. Supported: {', '.join(supported_extensions)}"
                })
                continue
            
            # Validate file size (10MB limit)
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:  # 10MB
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": "❌ File too large (max 10MB)"
                })
                continue
            
            # Save file temporarily and process
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                # Process the file
                result = resume_rag_system.process_uploaded_file(
                    tmp_path,
                    file.filename,
                    force_update=False
                )
                
                results.append({
                    "filename": file.filename,
                    "size_mb": round(len(content) / (1024 * 1024), 2),
                    **result
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"❌ Processing error: {str(e)}"
                })
            finally:
                # Clean up temporary file
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
        
        return JSONResponse({
            "success": True,
            "results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r.get("success", False)])
        })
        
    except Exception as e:
        print(f"Error in upload endpoint: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"Upload failed: {str(e)}"
        }, status_code=500)

@app.post("/api/query")
async def query_resumes(
    query: str = Form(...),
    query_type: str = Form("All Resumes"),
    max_results: Optional[int] = Form(5)
):
    """Query resumes with enhanced error handling"""
    try:
        # Check if system is ready
        if not resume_rag_system.query_system:
            return JSONResponse({
                "success": False,
                "message": "Query system not initialized. Please initialize the system first.",
                "requires_initialization": True
            }, status_code=400)
        
        # Validate query
        if not query or len(query.strip()) < 3:
            return JSONResponse({
                "success": False,
                "message": "Query must be at least 3 characters long"
            }, status_code=400)
        
        # Execute query
        kwargs = {}
        if query_type == "Ranked Candidates" and max_results:
            kwargs["max_results"] = min(max_results, 20)
        
        print(f"🔍 Executing query: '{query.strip()}' (type: {query_type})")
        query_result = resume_rag_system.query_resumes(query.strip(), query_type, **kwargs)
        
        if query_result.get("success", False):
            try:
                formatted_response = format_resume_response(query_result)
            except Exception as format_error:
                print(f"Warning: Response formatting failed: {format_error}")
                formatted_response = "Results found but formatting failed."
            
            return JSONResponse({
                "success": True,
                "query": query.strip(),
                "query_type": query_type,
                "database_used": getattr(resume_rag_system, 'db_path', 'Unknown'),
                "results_count": len(query_result.get("results", [])),
                "raw_results": query_result,
                "formatted_response": formatted_response
            })
        else:
            return JSONResponse({
                "success": False,
                "message": query_result.get("message", "Query failed")
            }, status_code=400)
            
    except Exception as e:
        print(f"Error in query endpoint: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"❌ Query failed: {str(e)}"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Enhanced health check"""
    try:
        db_connected = resume_rag_system.ingest_pipeline is not None
        query_ready = resume_rag_system.query_system is not None
        azure_configured = bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))
        
        return {
            "status": "healthy" if (db_connected and query_ready and azure_configured) else "degraded",
            "database_connected": db_connected,
            "query_system_ready": query_ready,
            "azure_configured": azure_configured,
            "current_database": getattr(resume_rag_system, 'db_path', None),
            "collection_name": getattr(resume_rag_system, 'collection_name', 'unknown'),
            "chromadb_sharing": getattr(resume_rag_system, 'force_chromadb', False),
            "chromadb_conflicts_resolved": True,
            "database_creation_supported": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "chromadb_conflicts_resolved": False,
            "database_creation_supported": False
        }

if __name__ == "__main__":
    print("🚀 Starting Enhanced Resume RAG System Web Interface...")
    print("📱 Access at: http://localhost:8000")
    print("✨ Features:")
    print("   • Database selection dropdown")
    print("   • Create new databases")
    print("   • Enhanced ChromaDB conflict resolution")
    print("   • Robust initialization with retries")
    print("   • Existing database support")
    print("   • Thread-safe operations")
    print("   • Automatic cleanup management")
    
    uvicorn.run(
        "web_interface:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )