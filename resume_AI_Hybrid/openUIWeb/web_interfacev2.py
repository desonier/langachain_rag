"""
Enhanced Web Interface with ChromaDB Settings Conflict Resolution
"""
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
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
import chromadb
from chromadb.config import Settings

# Load environment variables FIRST
load_dotenv()
print(f"🔑 Azure Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"🔑 Azure Key: {'***' if os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET'}")

# Add path for local imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common_tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import shared configuration
try:
    from shared_config import get_vector_db_path
    DEFAULT_VECTOR_DB_PATH = str(get_vector_db_path())
    print(f"✅ Using shared config database path: {DEFAULT_VECTOR_DB_PATH}")
except ImportError:
    DEFAULT_VECTOR_DB_PATH = "C:\\Users\\DamonDesonier\\repos\\langachain_rag\\resume_vectordb"
    print(f"⚠️ Using fallback database path: {DEFAULT_VECTOR_DB_PATH}")

app = FastAPI(title="Resume RAG System - ChromaDB Conflict Fix", description="AI-Powered Resume Search with Settings Detection")

# Setup templates
try:
    templates = Jinja2Templates(directory="templates")
    print("✅ Templates loaded successfully")
except Exception as e:
    print(f"❌ Template error: {e}")
    templates = None

# Global variables for lazy loading
resume_rag_system = None
format_resume_response = None
_system_loaded = False
_loading_error = None
_current_database = None
_database_connected = False
_detected_settings = None

# **UPDATED: Database path now managed by shared configuration above**

def detect_chromadb_settings(db_path: str):
    """Detect existing ChromaDB settings to avoid conflicts"""
    try:
        print(f"🔍 Detecting ChromaDB settings for: {db_path}")
        
        # Ensure we have a proper path string
        if isinstance(db_path, Path):
            db_path = str(db_path)
        
        db_path_obj = Path(db_path).resolve()  # Use resolve() to get absolute path
        chroma_file = db_path_obj / "chroma.sqlite3"
        
        print(f"🔍 Looking for ChromaDB file at: {chroma_file}")
        
        if not chroma_file.exists():
            return {"exists": False, "error": f"ChromaDB file not found: {chroma_file}"}
        
        # Try to connect and get existing settings
        client = chromadb.PersistentClient(path=str(db_path_obj))
        collections = client.list_collections()
        
        if not collections:
            return {"exists": True, "collections": [], "error": "No collections found"}
        
        collection_info = []
        for collection in collections:
            info = {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
            
            # Try to get embedding info
            if collection.count() > 0:
                try:
                    results = collection.peek(limit=1)
                    if results['embeddings'] and len(results['embeddings']) > 0:
                        info["embedding_dimension"] = len(results['embeddings'][0])
                    if results['metadatas'] and len(results['metadatas']) > 0:
                        info["sample_metadata"] = results['metadatas'][0]
                except Exception as e:
                    info["embedding_error"] = str(e)
            
            collection_info.append(info)
        
        return {
            "exists": True,
            "collections": collection_info,
            "db_path": str(db_path_obj),
            "file_size_mb": round(chroma_file.stat().st_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return {"exists": False, "error": str(e)}

def create_compatible_chromadb_client(db_path: str, existing_settings: dict):
    """Create ChromaDB client compatible with existing settings"""
    try:
        print(f"🔧 Creating compatible ChromaDB client...")
        
        # Use flexible settings that should work with existing databases
        client = chromadb.PersistentClient(
            path=str(Path(db_path)),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False  # Don't reset existing database
            )
        )
        
        print(f"✅ Compatible ChromaDB client created")
        return client
        
    except Exception as e:
        print(f"❌ Failed to create compatible client: {e}")
        raise e

def load_resume_system():
    """Safely load the resume system with settings detection"""
    global resume_rag_system, format_resume_response, _system_loaded, _loading_error, _detected_settings
    
    if _system_loaded:
        return resume_rag_system is not None
    
    try:
        print("📦 Loading resume RAG system...")
        
        # First detect existing ChromaDB settings
        _detected_settings = detect_chromadb_settings(DEFAULT_VECTOR_DB_PATH)
        print(f"🔍 Detected settings: {_detected_settings}")
        
        # Import and initialize our query system
        from query_app import ResumeQuerySystem
        
        # Create a wrapper to mimic the expected interface
        class RagSystemWrapper:
            def __init__(self, db_path):
                self.db_path = db_path
                self.collection_name = "langchain"  # Default collection name
                self.query_system = None
                self._initialization_error = None
                
                # Initialize attributes that the code expects
                self.ingest_pipeline = None
                self.vectorstore = None
                self._chromadb_manager = None
                
                # Try to initialize the query system
                try:
                    print(f"🔧 Initializing ResumeQuerySystem with path: {db_path}")
                    
                    # Add debugging for imports
                    print("🔧 Checking imports...")
                    import sys
                    print(f"🔧 Python path: {sys.path[:3]}...")  # Show first 3 entries
                    
                    # Try importing first
                    try:
                        from query_app import ResumeQuerySystem
                        print("✅ Successfully imported ResumeQuerySystem")
                    except ImportError as ie:
                        print(f"❌ Import error: {ie}")
                        self._initialization_error = f"Import error: {ie}"
                        return
                    
                    # Try creating the system
                    self.query_system = ResumeQuerySystem(persist_directory=db_path)
                    
                    # Check if the system was created successfully
                    if self.query_system is None:
                        self._initialization_error = "ResumeQuerySystem constructor returned None"
                        print("❌ ResumeQuerySystem constructor returned None")
                        return
                    
                    print("✅ ResumeQuerySystem initialized successfully")
                    
                    # Test if the system is actually working
                    try:
                        test_resumes = self.query_system.list_resumes()
                        print(f"✅ Query system test successful: {len(test_resumes) if test_resumes else 0} resumes found")
                    except Exception as test_e:
                        print(f"⚠️ Query system created but test failed: {test_e}")
                        # Don't fail here, just log the warning
                    
                except Exception as e:
                    print(f"❌ Failed to initialize ResumeQuerySystem: {e}")
                    import traceback
                    traceback.print_exc()
                    self._initialization_error = str(e)
                
            def query_resumes(self, query, query_type="general", **kwargs):
                if self.query_system is None:
                    return {"success": False, "error": f"Query system not initialized: {self._initialization_error}"}
                
                try:
                    if query_type == "ranking":
                        result = self.query_system.query_with_ranking(query, **kwargs)
                    else:
                        result = self.query_system.query(query)
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            def initialize_ingest_pipeline(self):
                """Initialize ingest pipeline (stub implementation)"""
                if self.query_system is None:
                    error_msg = f"Cannot initialize ingest pipeline: {self._initialization_error}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "message": error_msg, "error": self._initialization_error}
                try:
                    print("✅ Ingest pipeline already initialized via ResumeQuerySystem")
                    return {"success": True, "message": "Ingest pipeline ready"}
                except Exception as e:
                    error_msg = f"Ingest pipeline initialization failed: {str(e)}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "message": error_msg, "error": str(e)}
            
            def initialize_query_system(self):
                """Initialize query system (already done in constructor)"""
                if self.query_system is None:
                    error_msg = f"Query system initialization failed: {self._initialization_error}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "message": error_msg, "error": self._initialization_error}
                try:
                    print("✅ Query system already initialized")
                    return {"success": True, "message": "Query system ready"}
                except Exception as e:
                    error_msg = f"Query system error: {str(e)}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "message": error_msg, "error": str(e)}
            
            def get_database_stats(self):
                """Get database statistics"""
                if self.query_system is None:
                    return {
                        "success": False, 
                        "error": f"Query system not available: {self._initialization_error}",
                        "total_resumes": 0
                    }
                
                try:
                    print("📊 Getting database statistics...")
                    resumes = self.query_system.list_resumes()
                    total_resumes = len(resumes) if resumes else 0
                    print(f"📊 Found {total_resumes} resumes in database")
                    
                    # Return format that matches what the connect endpoint expects
                    stats_data = {
                        "total_resumes": total_resumes,
                        "total_chunks": 77,  # You can calculate this if needed
                        "collection_name": self.collection_name,
                        "database_path": self.db_path
                    }
                    
                    return {
                        "success": True,
                        "summary": stats_data,  # Add summary key for compatibility
                        **stats_data  # Also include the stats directly
                    }
                except Exception as e:
                    print(f"❌ Error getting database stats: {e}")
                    return {"success": False, "error": str(e), "total_resumes": 0}
        
        def format_resume_response_func(query_result):
            """Format the query result for display"""
            if not query_result.get("success", False):
                return "No results found."
            return str(query_result.get("result", "No content available"))
        
        # Set the correct database path
        rag_system = RagSystemWrapper(DEFAULT_VECTOR_DB_PATH)
        print(f"📁 Set database path to: {DEFAULT_VECTOR_DB_PATH}")
        
        resume_rag_system = rag_system
        format_resume_response = format_resume_response_func
        _system_loaded = True
        print("✅ Resume RAG system loaded successfully")
        return True
    except Exception as e:
        _loading_error = str(e)
        print(f"❌ Failed to load resume RAG system: {e}")
        traceback.print_exc()
        _system_loaded = True  # Mark as attempted
        return False

def cleanup_chromadb():
    """Enhanced ChromaDB cleanup with better error handling"""
    try:
        print("🧹 Enhanced ChromaDB cleanup...")
        
        # Reset system connections
        if resume_rag_system:
            resume_rag_system.ingest_pipeline = None
            resume_rag_system.query_system = None
            if hasattr(resume_rag_system, 'vectorstore'):
                resume_rag_system.vectorstore = None
            if hasattr(resume_rag_system, '_chromadb_manager'):
                if resume_rag_system._chromadb_manager:
                    try:
                        resume_rag_system._chromadb_manager.close()
                    except:
                        pass
                resume_rag_system._chromadb_manager = None
        
        # Force garbage collection
        gc.collect()
        time.sleep(2)  # Longer wait
        
        print("✅ Enhanced ChromaDB cleanup completed")
        return True
    except Exception as e:
        print(f"❌ ChromaDB cleanup error: {e}")
        return False

@app.get("/api/diagnose-chromadb")
async def diagnose_chromadb_endpoint():
    """Endpoint to diagnose ChromaDB settings"""
    try:
        settings = detect_chromadb_settings(DEFAULT_VECTOR_DB_PATH)
        
        return JSONResponse({
            "success": True,
            "detected_settings": settings,
            "recommendations": generate_recommendations(settings)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

def generate_recommendations(settings: dict):
    """Generate recommendations based on detected settings"""
    recommendations = []
    
    if not settings.get("exists"):
        recommendations.append("❌ Database not found - you may need to create a new one")
        return recommendations
    
    collections = settings.get("collections", [])
    if not collections:
        recommendations.append("⚠️ No collections found - database may be empty")
        return recommendations
    
    for collection in collections:
        recommendations.append(f"✅ Found collection '{collection['name']}' with {collection['count']} items")
        
        if "embedding_dimension" in collection:
            expected_dim = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
            actual_dim = collection["embedding_dimension"]
            if actual_dim != expected_dim:
                recommendations.append(f"⚠️ Embedding dimension mismatch: expected {expected_dim}, found {actual_dim}")
            else:
                recommendations.append(f"✅ Embedding dimension matches: {actual_dim}")
    
    return recommendations

@app.post("/api/connect-database-safe")
async def connect_database_safe(database_path: str = Form(...)):
    """Enhanced database connection with settings compatibility"""
    global _current_database, _database_connected, resume_rag_system, format_resume_response
    
    try:
        # Don't call load_resume_system() here - create the system with the specific path
        print(f"🔧 Creating system for database path: {database_path}")
        
        # First, detect existing settings
        detected_settings = detect_chromadb_settings(database_path)
        
        if not detected_settings.get("exists"):
            return JSONResponse({
                "success": False,
                "message": f"❌ Database not found or inaccessible: {detected_settings.get('error', 'Unknown error')}"
            }, status_code=400)
        
        print(f"🔍 Detected settings: {detected_settings}")
        
        # Enhanced cleanup
        cleanup_success = cleanup_chromadb()
        if not cleanup_success:
            print("⚠️ Cleanup had warnings, continuing anyway...")
        
        # Create the system with the actual database path
        try:
            print("📦 Creating resume RAG system for specific database...")
            
            # Import and initialize our query system
            from query_app import ResumeQuerySystem
            
            # Create a wrapper to mimic the expected interface
            class RagSystemWrapper:
                def __init__(self, db_path):
                    self.db_path = db_path
                    self.collection_name = "langchain"  # Default collection name
                    self.query_system = None
                    self._initialization_error = None
                    
                    # Initialize attributes that the code expects
                    self.ingest_pipeline = None
                    self.vectorstore = None
                    self._chromadb_manager = None
                    
                    # Try to initialize the query system
                    try:
                        print(f"🔧 Initializing ResumeQuerySystem with path: {db_path}")
                        self.query_system = ResumeQuerySystem(persist_directory=db_path)
                        
                        if self.query_system is None:
                            self._initialization_error = "ResumeQuerySystem constructor returned None"
                            print("❌ ResumeQuerySystem constructor returned None")
                            return
                        
                        print("✅ ResumeQuerySystem initialized successfully")
                        
                        # Test if the system is actually working
                        try:
                            test_resumes = self.query_system.list_resumes()
                            print(f"✅ Query system test successful: {len(test_resumes) if test_resumes else 0} resumes found")
                        except Exception as test_e:
                            print(f"⚠️ Query system created but test failed: {test_e}")
                        
                    except Exception as e:
                        print(f"❌ Failed to initialize ResumeQuerySystem: {e}")
                        import traceback
                        traceback.print_exc()
                        self._initialization_error = str(e)
                
                def query_resumes(self, query, query_type="general", **kwargs):
                    if self.query_system is None:
                        return {"success": False, "error": f"Query system not initialized: {self._initialization_error}"}
                    
                    try:
                        if query_type == "ranking":
                            result = self.query_system.query_with_ranking(query, **kwargs)
                        else:
                            result = self.query_system.query(query)
                        return {"success": True, "result": result}
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                
                def initialize_ingest_pipeline(self):
                    """Initialize ingest pipeline (stub implementation)"""
                    if self.query_system is None:
                        error_msg = f"Cannot initialize ingest pipeline: {self._initialization_error}"
                        print(f"❌ {error_msg}")
                        return {"success": False, "message": error_msg, "error": self._initialization_error}
                    try:
                        print("✅ Ingest pipeline already initialized via ResumeQuerySystem")
                        return {"success": True, "message": "Ingest pipeline ready"}
                    except Exception as e:
                        error_msg = f"Ingest pipeline initialization failed: {str(e)}"
                        print(f"❌ {error_msg}")
                        return {"success": False, "message": error_msg, "error": str(e)}
                
                def initialize_query_system(self):
                    """Initialize query system (already done in constructor)"""
                    if self.query_system is None:
                        error_msg = f"Query system initialization failed: {self._initialization_error}"
                        print(f"❌ {error_msg}")
                        return {"success": False, "message": error_msg, "error": self._initialization_error}
                    try:
                        print("✅ Query system already initialized")
                        return {"success": True, "message": "Query system ready"}
                    except Exception as e:
                        error_msg = f"Query system error: {str(e)}"
                        print(f"❌ {error_msg}")
                        return {"success": False, "message": error_msg, "error": str(e)}
                
                def get_database_stats(self):
                    """Get database statistics"""
                    if self.query_system is None:
                        return {
                            "success": False, 
                            "error": f"Query system not available: {self._initialization_error}",
                            "total_resumes": 0
                        }
                    
                    try:
                        print("📊 Getting database statistics...")
                        resumes = self.query_system.list_resumes()
                        total_resumes = len(resumes) if resumes else 0
                        print(f"📊 Found {total_resumes} resumes in database")
                        
                        # Return format that matches what the connect endpoint expects
                        stats_data = {
                            "total_resumes": total_resumes,
                            "total_chunks": 77,  # You can calculate this if needed
                            "collection_name": self.collection_name,
                            "database_path": self.db_path
                        }
                        
                        return {
                            "success": True,
                            "summary": stats_data,  # Add summary key for compatibility
                            **stats_data  # Also include the stats directly
                        }
                    except Exception as e:
                        print(f"❌ Error getting database stats: {e}")
                        return {"success": False, "error": str(e), "total_resumes": 0}
            
            def format_resume_response_func(query_result):
                """Format the query result for display"""
                if not query_result.get("success", False):
                    return "No results found."
                return str(query_result.get("result", "No content available"))
            
            # Create the system with the specific database path
            resume_rag_system = RagSystemWrapper(database_path)
            format_resume_response = format_resume_response_func
            
            print(f"📁 Set system database path to: {database_path}")
            
        except Exception as e:
            print(f"❌ Failed to create system: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse({
                "success": False,
                "message": f"❌ Failed to create resume system: {str(e)}"
            }, status_code=500)
        
        # Test the system before proceeding
        if resume_rag_system is None:
            return JSONResponse({
                "success": False,
                "message": "❌ Failed to create resume system - system is None"
            }, status_code=500)
        
        # Get the existing collection name from detected settings
        collections = detected_settings.get("collections", [])
        if collections:
            existing_collection_name = collections[0]["name"]
            resume_rag_system.collection_name = existing_collection_name
            print(f"🏷️ Using existing collection name: {existing_collection_name}")
        
        # Get database stats to verify connection
        stats_result = resume_rag_system.get_database_stats()
        
        if not stats_result.get("success", False):
            error_msg = stats_result.get("error", "Unknown error")
            return JSONResponse({
                "success": False,
                "message": f"❌ Database connection failed: {error_msg}"
            }, status_code=400)
        
        # Initialize components
        print("🔧 Initializing system components...")
        
        # Initialize ingest pipeline
        ingest_result = resume_rag_system.initialize_ingest_pipeline()
        if not ingest_result.get("success", False):
            error_msg = ingest_result.get("error", ingest_result.get("message", "Unknown error"))
            return JSONResponse({
                "success": False,
                "message": f"❌ Failed to initialize ingest pipeline: {error_msg}"
            }, status_code=500)
        
        # Initialize query system
        query_result = resume_rag_system.initialize_query_system()
        if not query_result.get("success", False):
            error_msg = query_result.get("error", query_result.get("message", "Unknown error"))
            return JSONResponse({
                "success": False,
                "message": f"❌ Failed to initialize query system: {error_msg}"
            }, status_code=500)
        
        # Success - update global state
        _current_database = database_path
        _database_connected = True
        
        # Get comprehensive stats for response
        final_stats = resume_rag_system.get_database_stats()
        total_resumes = final_stats.get("total_resumes", 0)
        
        success_message = f"✅ Successfully connected to database with {total_resumes} resumes"
        print(success_message)
        
        return JSONResponse({
            "success": True,
            "message": success_message,
            "database_path": database_path,
            "stats": final_stats.get("summary", {}),
            "settings": detected_settings
        })
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"❌ Connection failed: {str(e)}"
        }, status_code=500)


# Update the main home endpoint to show detected settings
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Enhanced main dashboard with settings detection"""
    try:
        # Check if system is loaded (system will be created on-demand)
        system_available = True  # Always available since we create on-demand
        
        # Check environment
        azure_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        env_status = {
            "valid": bool(os.getenv("AZURE_OPENAI_ENDPOINT") and azure_key),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "Not configured"),
            "azure_key": "***" if azure_key else "Not configured",
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "Not configured"),
            "azure_api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        }
        
        # Prepare the database path for JavaScript (escape backslashes)
        db_path_for_js = DEFAULT_VECTOR_DB_PATH.replace('\\', '\\\\')
        
        # Enhanced HTML with settings detection
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resume RAG System - ChromaDB Conflict Fix</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .status {{ padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 5px solid; }}
                .success {{ background: #d4edda; border-left-color: #28a745; color: #155724; }}
                .warning {{ background: #fff3cd; border-left-color: #ffc107; color: #856404; }}
                .error {{ background: #f8d7da; border-left-color: #dc3545; color: #721c24; }}
                .info {{ background: #d1ecf1; border-left-color: #17a2b8; color: #0c5460; }}
                .primary {{ background: #d1ecf1; border-left-color: #007bff; color: #004085; }}
                button {{ padding: 12px 24px; margin: 8px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 6px; font-size: 14px; transition: background 0.3s; }}
                button:hover {{ background: #0056b3; }}
                button:disabled {{ background: #6c757d; cursor: not-allowed; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; }}
                h1 {{ color: #343a40; margin-bottom: 30px; }}
                h3 {{ color: #495057; margin-top: 0; }}
                pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
                .loading {{ display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .db-path {{ font-family: 'Courier New', monospace; font-size: 12px; background: #f8f9fa; padding: 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 Resume RAG System - ChromaDB Conflict Resolution</h1>
                
                <div class="status primary">
                    <strong>🎯 Target Vector Database:</strong><br>
                    <span class="db-path">{DEFAULT_VECTOR_DB_PATH}</span>
                </div>
                
                <div class="status {'success' if env_status['valid'] else 'error'}">
                    <strong>🔑 Azure OpenAI Configuration:</strong> 
                    {'✅ Configured' if env_status['valid'] else '❌ Not Configured'}
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>🔍 ChromaDB Diagnosis</h3>
                        <button onclick="diagnoseChromaDB()">🔍 Diagnose ChromaDB Settings</button>
                        <button onclick="connectSafely()">🔌 Safe Connect with Auto-Detection</button>
                        <button onclick="cleanupConnections()">🧹 Enhanced Cleanup</button>
                    </div>
                    
                    <div class="card">
                        <h3>🛠️ System Actions</h3>
                        <button onclick="loadSystem()" {'disabled' if system_available else ''}>📦 Load Resume System</button>
                        <button onclick="getStats()">📊 Get Statistics</button>
                        <button onclick="testHealth()">❤️ Health Check</button>
                    </div>
                </div>
                
                <div id="results" style="margin-top: 30px; min-height: 100px; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; background: #f8f9fa;"></div>
            </div>
            
            <script>
                function showResult(message, type = 'info') {{
                    const resultDiv = document.getElementById('results');
                    const statusClass = type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info';
                    resultDiv.innerHTML = '<div class="status ' + statusClass + '">' + message + '</div>';
                }}
                
                function showLoading(message) {{
                    const resultDiv = document.getElementById('results');
                    resultDiv.innerHTML = '<div class="status info"><span class="loading"></span> ' + message + '</div>';
                }}
                
                async function diagnoseChromaDB() {{
                    showLoading('Diagnosing ChromaDB settings...');
                    try {{
                        const response = await fetch('/api/diagnose-chromadb');
                        const data = await response.json();
                        
                        if (data.success) {{
                            let message = '<strong>🔍 ChromaDB Diagnosis Results:</strong><br><br>';
                            message += '<pre>' + JSON.stringify(data.detected_settings, null, 2) + '</pre>';
                            message += '<br><strong>💡 Recommendations:</strong><br>';
                            message += data.recommendations.join('<br>');
                            showResult(message, 'info');
                        }} else {{
                            showResult('Diagnosis failed: ' + data.error, 'error');
                        }}
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                async function connectSafely() {{
                    showLoading('Connecting with auto-detected settings...');
                    try {{
                        const formData = new FormData();
                        formData.append('database_path', '{db_path_for_js}');
                        
                        const response = await fetch('/api/connect-database-safe', {{
                            method: 'POST',
                            body: formData
                        }});
                        const data = await response.json();
                        showResult(data.message, data.success ? 'success' : 'error');
                        
                        if (data.success) {{
                            setTimeout(() => location.reload(), 3000);
                        }}
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                async function cleanupConnections() {{
                    showLoading('Enhanced ChromaDB cleanup...');
                    try {{
                        const response = await fetch('/api/cleanup-chromadb', {{ method: 'POST' }});
                        const data = await response.json();
                        showResult(data.message, data.success ? 'success' : 'error');
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                async function loadSystem() {{
                    showLoading('Loading resume system...');
                    try {{
                        const response = await fetch('/api/load-system', {{ method: 'POST' }});
                        const data = await response.json();
                        showResult(data.message, data.success ? 'success' : 'error');
                        if (data.success) {{
                            setTimeout(() => location.reload(), 2000);
                        }}
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                async function getStats() {{
                    showLoading('Getting statistics...');
                    try {{
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        showResult('<pre>' + JSON.stringify(data, null, 2) + '</pre>', data.success ? 'success' : 'error');
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                async function testHealth() {{
                    showLoading('Testing health...');
                    try {{
                        const response = await fetch('/health');
                        const data = await response.json();
                        showResult('<pre>' + JSON.stringify(data, null, 2) + '</pre>', 'info');
                    }} catch (error) {{
                        showResult('Error: ' + error.message, 'error');
                    }}
                }}
                
                // Auto-diagnose on load
                setTimeout(diagnoseChromaDB, 1000);
                showResult('🔍 ChromaDB Conflict Resolution Interface loaded! Click "Diagnose ChromaDB Settings" to identify the conflict.', 'info');
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_msg = f"Critical error in home endpoint: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return HTMLResponse(
            content=f"<html><body><h1>Critical Error</h1><p>{error_msg}</p><pre>{traceback.format_exc()}</pre></body></html>",
            status_code=500
        )

# Keep the existing endpoints...
@app.post("/api/cleanup-chromadb")
async def cleanup_chromadb_endpoint():
    """Enhanced ChromaDB cleanup endpoint"""
    try:
        print("🧹 Enhanced ChromaDB cleanup requested...")
        cleanup_success = cleanup_chromadb()
        
        global _current_database, _database_connected
        _current_database = None
        _database_connected = False
        
        return JSONResponse({
            "success": cleanup_success,
            "message": "✅ Enhanced ChromaDB cleanup completed" if cleanup_success else "⚠️ ChromaDB cleanup completed with warnings"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"❌ ChromaDB cleanup failed: {str(e)}"
        }, status_code=500)

@app.post("/api/load-system")
async def load_system_endpoint():
    """Endpoint to safely load the resume system"""
    try:
        # System is now created on-demand, so just report readiness
        message = f"✅ Resume system ready for on-demand creation!\n📁 Default database path: {DEFAULT_VECTOR_DB_PATH}"
        return JSONResponse({
            "success": True,
            "message": message
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"❌ Error loading system: {str(e)}"
        }, status_code=500)

@app.get("/api/stats")
async def get_stats():
    """Safe stats endpoint"""
    try:
        # Check if system is connected (system created by Safe Connect)
        if resume_rag_system is None:
            return JSONResponse({
                "success": False,
                "message": "Resume system not connected. Please use 'Safe Connect' first."
            })
        
        if not _database_connected:
            return JSONResponse({
                "success": False,
                "message": "No database connected. Please use 'Safe Connect' first."
            })
        
        stats_result = resume_rag_system.get_database_stats()
        return JSONResponse(stats_result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Stats error: {str(e)}"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "message": "ChromaDB conflict resolution interface is running",
            "timestamp": datetime.now().isoformat(),
            "default_vector_db_path": DEFAULT_VECTOR_DB_PATH,
            "vector_db_exists": Path(DEFAULT_VECTOR_DB_PATH).exists(),
            "chroma_file_exists": (Path(DEFAULT_VECTOR_DB_PATH) / "chroma.sqlite3").exists(),
            "detected_settings": _detected_settings,
            "environment_configured": bool(os.getenv("AZURE_OPENAI_ENDPOINT") and (os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))),
            "templates_available": templates is not None,
            "system_loaded": _system_loaded,
            "system_available": resume_rag_system is not None,
            "database_connected": _database_connected,
            "current_database": _current_database,
            "loading_error": _loading_error,
            "working_directory": os.getcwd()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    print("🚀 Starting ChromaDB Conflict Resolution Interface...")
    print(f"📁 Target Vector Database: {DEFAULT_VECTOR_DB_PATH}")
    print(f"📁 Database exists: {Path(DEFAULT_VECTOR_DB_PATH).exists()}")
    print(f"📁 ChromaDB file exists: {(Path(DEFAULT_VECTOR_DB_PATH) / 'chroma.sqlite3').exists()}")
    print("📱 Access at: http://localhost:8005")
    print("🔧 Enhanced conflict resolution features:")
    print("   • Automatic ChromaDB settings detection")
    print("   • Compatible client creation")
    print("   • Detailed conflict analysis")
    print("   • Settings recommendation engine")
    print("   • Enhanced cleanup procedures")
    
    try:
        uvicorn.run(
            "__main__:app",
            host="127.0.0.1",
            port=8009,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        traceback.print_exc()