from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sys
import os
import signal
import atexit
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables if .env file exists
try:
    from dotenv import load_dotenv
    env_path = current_dir.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed

# Import langchain dependencies at module level
try:
    from langchain_openai import AzureChatOpenAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    # Import PromptTemplate to avoid "not defined" errors, even if we don't use it
    from langchain_core.prompts import PromptTemplate
    print("✅ All langchain imports successful")
except ImportError as e:
    print(f"❌ Langchain import error: {e}")
    print(f"🐍 Python executable: {sys.executable}")
    print(f"🐍 Python path: {sys.path[:3]}")

try:
    from admin.chromadb_admin import ChromaDBAdmin
    from models.admin_models import CollectionForm, DatabaseForm
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔍 Checking file structure...")
    print(f"Current dir: {current_dir}")
    print(f"Admin dir exists: {(current_dir / 'admin').exists()}")
    print(f"Models dir exists: {(current_dir / 'models').exists()}")
    print(f"Templates dir exists: {(current_dir.parent / 'templates').exists()}")
    sys.exit(1)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Use environment variable for secret key or default
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

def query_with_chromadb_admin(chromadb_admin, query_text, collection_name, query_type, max_results):
    """
    Query using the existing ChromaDB admin instance to avoid conflicts
    """
    print(f"🚨 ENTERING QUERY FUNCTION: query_text='{query_text}', collection='{collection_name}', type='{query_type}'")
    try:
        print(f"🔍 QUERY DEBUG: Starting query with text='{query_text}', collection='{collection_name}', type='{query_type}'")
        
        # Debug Python environment
        import sys
        print(f"🐍 Python executable: {sys.executable}")
        print(f"🐍 Python path: {sys.path[:3]}...")  # Show first 3 paths
        
        # Get Azure OpenAI configuration
        azure_config = {
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_key': os.getenv('AZURE_OPENAI_KEY'),  # Using AZURE_OPENAI_KEY from .env
            'azure_deployment': os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT', 'resumemodel'),  # Using CHATGPT_DEPLOYMENT
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            'temperature': 0.1
        }
        
        # Validate Azure OpenAI config
        if not azure_config['azure_endpoint'] or not azure_config['api_key']:
            return jsonify({
                "success": False,
                "error": "Azure OpenAI configuration missing. Please check your .env file."
            }), 500
        
        # Initialize Azure OpenAI
        llm = AzureChatOpenAI(**azure_config)
        
        # Use the existing ChromaDB client from admin - DO NOT create a new one
        chroma_client = chromadb_admin.client
        
        # Get collections to query
        if collection_name and collection_name.lower() != 'all':
            collections_to_query = [collection_name]
        else:
            # Query all collections
            all_collections = chromadb_admin.list_collections()
            collections_to_query = [col['name'] for col in all_collections]
        
        all_results = []
        
        for coll_name in collections_to_query:
            try:
                # Get the collection directly from the existing client
                collection = chroma_client.get_collection(coll_name)
                
                # Debug: Check collection info
                collection_count = collection.count()
                print(f"🔍 DEBUG: Querying collection '{coll_name}' with {collection_count} documents")
                
                if collection_count == 0:
                    print(f"⚠️ WARNING: Collection '{coll_name}' is empty, skipping...")
                    continue
                
                if query_type == 'ranking':
                    # Use direct ChromaDB query for similarity search
                    query_results = collection.query(
                        query_texts=[query_text],
                        n_results=max_results * 3,  # Get more results to group by source
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # Debug: Show query results
                    result_count = len(query_results['documents'][0]) if query_results['documents'] and query_results['documents'][0] else 0
                    print(f"🔍 DEBUG: Collection '{coll_name}' returned {result_count} results for query: '{query_text[:50]}...'")
                    
                    # Group ranking results by original source file
                    source_groups = {}
                    if query_results['documents'] and query_results['documents'][0]:
                        for doc, metadata, distance in zip(
                            query_results['documents'][0],
                            query_results['metadatas'][0],
                            query_results['distances'][0]
                        ):
                            # Determine the original filename
                            original_name = (metadata.get('display_filename') or 
                                           metadata.get('original_file_source', '').split('\\')[-1].split('/')[-1] or
                                           metadata.get('document_name') or 
                                           metadata.get('source', 'Unknown'))
                            
                            if original_name not in source_groups:
                                source_groups[original_name] = {
                                    'best_score': float(distance),
                                    'content_chunks': [],
                                    'metadata': metadata,
                                    'collection': coll_name
                                }
                            else:
                                # Keep the best (lowest) score for this source
                                source_groups[original_name]['best_score'] = min(
                                    source_groups[original_name]['best_score'], 
                                    float(distance)
                                )
                            
                            # Add this chunk
                            chunk_text = doc[:300] + '...' if len(doc) > 300 else doc
                            source_groups[original_name]['content_chunks'].append(chunk_text)
                    
                    # Convert grouped sources to collection results
                    collection_results = []
                    for original_name, group_data in source_groups.items():
                        # Combine chunks but limit total length
                        combined_content = '\n\n'.join(group_data['content_chunks'])
                        if len(combined_content) > 500:
                            combined_content = combined_content[:500] + '...'
                        
                        collection_results.append({
                            'content': combined_content,
                            'metadata': group_data['metadata'],
                            'score': group_data['best_score'],
                            'collection': coll_name,
                            'original_filename': original_name,
                            'chunk_count': len(group_data['content_chunks'])
                        })
                    
                    # Sort by best score and limit to max_results
                    collection_results.sort(key=lambda x: x['score'])
                    collection_results = collection_results[:max_results]
                    
                    all_results.extend(collection_results)
                
                else:
                    # Standard RAG query with LLM - get relevant documents first
                    query_results = collection.query(
                        query_texts=[query_text],
                        n_results=max_results,
                        include=["documents", "metadatas"]
                    )
                    
                    # Debug: Show query results for RAG
                    result_count = len(query_results['documents'][0]) if query_results['documents'] and query_results['documents'][0] else 0
                    print(f"🔍 DEBUG: RAG query on collection '{coll_name}' returned {result_count} results")
                    
                    if query_results['documents'] and query_results['documents'][0]:
                        # Format context from retrieved documents
                        context_docs = []
                        for doc, metadata in zip(query_results['documents'][0], query_results['metadatas'][0]):
                            context_docs.append(doc)
                        
                        # Join all context
                        context = "\n\n".join(context_docs)
                        
                        # Create prompt template
                        prompt_template = """You are an AI assistant helping with resume and career information queries.
Use the following pieces of context to answer the question. If you don't know the answer based on the context, just say that you don't know.

Context:
{context}

Question: {question}

Answer:"""
                        
                        # Create and execute the prompt without PromptTemplate class
                        formatted_prompt = prompt_template.format(context=context, question=query_text)
                        response = llm.invoke(formatted_prompt)
                        
                        # Extract token usage if available
                        token_usage = {}
                        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                            usage = response.response_metadata['token_usage']
                            token_usage = {
                                'prompt_tokens': usage.get('prompt_tokens', 0),
                                'completion_tokens': usage.get('completion_tokens', 0),
                                'total_tokens': usage.get('total_tokens', 0)
                            }
                            
                            # Estimate cost (approximate rates for GPT-4)
                            # These are example rates - adjust based on your Azure OpenAI pricing
                            input_cost_per_1k = 0.03  # $0.03 per 1K tokens for input
                            output_cost_per_1k = 0.06  # $0.06 per 1K tokens for output
                            
                            input_cost = (token_usage['prompt_tokens'] / 1000) * input_cost_per_1k
                            output_cost = (token_usage['completion_tokens'] / 1000) * output_cost_per_1k
                            token_usage['estimated_cost'] = input_cost + output_cost
                        
                        # Format source documents - Group by original source file
                        print(f"🔍 DEBUG: Processing {len(query_results['documents'][0])} documents for grouping")
                        source_groups = {}
                        for doc, metadata in zip(query_results['documents'][0], query_results['metadatas'][0]):
                            # Debug: Print metadata to see what we're working with
                            print(f"🔍 DEBUG: Document metadata: {metadata}")
                            
                            # Determine the original filename
                            original_name = (metadata.get('display_filename') or 
                                           metadata.get('original_file_source', '').split('\\')[-1].split('/')[-1] or
                                           metadata.get('document_name') or 
                                           metadata.get('source', 'Unknown'))
                            
                            print(f"🔍 DEBUG: Determined original_name: '{original_name}' from metadata")
                            
                            if original_name not in source_groups:
                                source_groups[original_name] = {
                                    'content_chunks': [],
                                    'metadata': metadata,
                                    'collection': coll_name
                                }
                                print(f"🔍 DEBUG: Created new group for '{original_name}'")
                            else:
                                print(f"🔍 DEBUG: Added to existing group for '{original_name}'")
                            
                            # Add this chunk to the group
                            chunk_text = doc[:300] + '...' if len(doc) > 300 else doc
                            source_groups[original_name]['content_chunks'].append(chunk_text)
                        
                        print(f"🔍 DEBUG: Created {len(source_groups)} source groups: {list(source_groups.keys())}")
                        
                        # Convert grouped sources to formatted list
                        formatted_sources = []
                        for original_name, group_data in source_groups.items():
                            # Combine all chunks for this source, but limit total length
                            combined_content = '\n\n'.join(group_data['content_chunks'])
                            if len(combined_content) > 500:
                                combined_content = combined_content[:500] + '...'
                            
                            formatted_sources.append({
                                'content': combined_content,
                                'metadata': group_data['metadata'],
                                'collection': coll_name,
                                'original_filename': original_name,
                                'chunk_count': len(group_data['content_chunks'])
                            })
                            print(f"🔍 DEBUG: Group '{original_name}' has {len(group_data['content_chunks'])} chunks")
                        
                        all_results.append({
                            'collection': coll_name,
                            'response': response.content if hasattr(response, 'content') else str(response),
                            'sources': formatted_sources,
                            'token_usage': token_usage
                        })
                    else:
                        # No documents found
                        all_results.append({
                            'collection': coll_name,
                            'response': f"No relevant documents found in collection '{coll_name}' for the query.",
                            'sources': []
                        })
                    
            except Exception as e:
                print(f"❌ ERROR: Failed to query collection '{coll_name}': {e}")
                print(f"❌ ERROR: Exception type: {type(e).__name__}")
                import traceback
                print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
                all_results.append({
                    'collection': coll_name,
                    'error': str(e)
                })
        
        if query_type == 'ranking':
            # Sort ranking results by score
            all_results.sort(key=lambda x: x.get('score', 0))
            response_data = {
                "success": True,
                "query_type": "ranking",
                "results": all_results
            }
            print(f"🔍 QUERY DEBUG: Returning ranking response with {len(all_results)} results")
            return jsonify(response_data)
        else:
            # Calculate aggregated token usage for standard queries
            total_token_usage = {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0,
                'estimated_cost': 0
            }
            
            for result in all_results:
                if 'token_usage' in result:
                    usage = result['token_usage']
                    total_token_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
                    total_token_usage['completion_tokens'] += usage.get('completion_tokens', 0)
                    total_token_usage['total_tokens'] += usage.get('total_tokens', 0)
                    total_token_usage['estimated_cost'] += usage.get('estimated_cost', 0)
            
            response_data = {
                "success": True,
                "query_type": "standard",
                "results": all_results,
                "token_usage": total_token_usage if total_token_usage['total_tokens'] > 0 else None
            }
            print(f"🔍 QUERY DEBUG: Returning standard response with {len(all_results)} results")
            print(f"🔍 QUERY DEBUG: Sample result: {all_results[0] if all_results else 'No results'}")
            print(f"🔍 QUERY DEBUG: Token usage: {total_token_usage}")
            return jsonify(response_data)
            
    except Exception as e:
        print(f"❌ Error in query_with_chromadb_admin: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Query failed: {str(e)}"
        }), 500

def validate_existing_database():
    """
    Check if database exists and validate it can be properly initialized
    Returns: (exists, can_connect, error_message)
    """
    try:
        # Add path to import shared config
        sys.path.append(str(current_dir.parent.parent.parent))
        
        # Check if shared config is available and get DB path
        try:
            from shared_config import get_vector_db_path
            db_path = Path(get_vector_db_path())
        except ImportError:
            # Fallback path
            db_path = Path(r"C:\Users\DamonDesonier\repos\langachain_rag\resume_AI_Hybrid\resume_vectordb")
        
        print(f"🔍 Checking for existing database at: {db_path}")
        
        # Check if database directory and files exist
        if not db_path.exists():
            print("📂 No existing database found")
            return False, True, None  # No database exists, connection would be fine
        
        # Check for ChromaDB database file
        chroma_db_file = db_path / "chroma.sqlite3"
        if not chroma_db_file.exists():
            print("📂 Database directory exists but no ChromaDB files found")
            return False, True, None
        
        print("✅ Existing database found, testing connection...")
        
        # Test database connection
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use consistent settings that match the admin
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
            
            # Test connection
            test_client = chromadb.PersistentClient(path=str(db_path), settings=settings)
            
            # Test basic operations
            collections = test_client.list_collections()
            print(f"✅ Database connection successful. Found {len(collections)} collections.")
            
            # Clean up test connection
            del test_client
            
            return True, True, None
            
        except Exception as db_error:
            error_msg = f"Database found but failed to connect: {str(db_error)}"
            print(f"❌ {error_msg}")
            return True, False, error_msg
            
    except Exception as e:
        error_msg = f"Error during database validation: {str(e)}"
        print(f"❌ {error_msg}")
        return False, False, error_msg

def show_database_error_popup(error_message):
    """Show database error in both console and attempt to show system notification"""
    print("\n" + "="*60)
    print("🚨 DATABASE INITIALIZATION ERROR")
    print("="*60)
    print(f"❌ {error_message}")
    print("="*60)
    print("Recommendations:")
    print("1. Check if another ChromaDB instance is running")
    print("2. Restart the application")
    print("3. Check database file permissions")
    print("4. Consider backing up and recreating the database")
    print("="*60 + "\n")
    
    # Try to show Windows notification (optional, won't fail if not available)
    try:
        import subprocess
        subprocess.run([
            'powershell', '-Command',
            f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
            f'[System.Windows.Forms.MessageBox]::Show("{error_message}", "Database Error", "OK", "Error")'
        ], capture_output=True, timeout=5)
    except:
        pass  # Notification failed, but continue anyway

# Validate existing database before initializing admin
print("🚀 Starting ChromaDB Admin Interface...")
db_exists, can_connect, error_msg = validate_existing_database()

# Store validation results globally
startup_db_validation = {
    'db_exists': db_exists,
    'can_connect': can_connect, 
    'error_message': error_msg,
    'validation_time': None
}

if db_exists and not can_connect:
    show_database_error_popup(error_msg)
    print("⚠️ Continuing with limited functionality...")

def startup_banner():
    """Display startup status banner"""
    print("\n" + "="*60)
    print("🚀 ChromaDB Admin Interface")
    print("="*60)
    
    if startup_db_validation['db_exists']:
        print(f"📂 Database Status: Found existing database")
        if startup_db_validation['can_connect']:
            print(f"✅ Connection Test: Successful")
        else:
            print(f"❌ Connection Test: Failed")
            print(f"   Error: {startup_db_validation['error_message']}")
    else:
        print(f"📂 Database Status: No existing database (will create on first use)")
    
    if chromadb_admin:
        print(f"✅ Admin Status: Initialized successfully")
    else:
        print(f"❌ Admin Status: Failed to initialize")
        if startup_db_validation['error_message']:
            print(f"   Error: {startup_db_validation['error_message']}")
    
    print("="*60)
    print("📊 Dashboard: http://localhost:5001")
    print("🗂️ Collections: http://localhost:5001/admin/collections")
    print("📈 Statistics: http://localhost:5001/admin/stats")
    print("🛠️ Database: http://localhost:5001/admin/database")
    print("💡 Press Ctrl+C to gracefully shutdown")
    print("="*60 + "\n")

# Initialize ChromaDBAdmin with error handling
try:
    chromadb_admin = ChromaDBAdmin()
    print("✅ ChromaDBAdmin initialized successfully")
    startup_db_validation['validation_time'] = "Startup validation completed"
    
    # If database validation failed but admin initialized, warn user
    if db_exists and not can_connect:
        print("⚠️ Database connection issues detected but admin initialized")
        print("   Some features may not work properly")
        
except Exception as e:
    print(f"❌ Failed to initialize ChromaDBAdmin: {e}")
    chromadb_admin = None
    startup_db_validation['error_message'] = f"ChromaDBAdmin initialization failed: {e}"
    
    # Show error popup if admin initialization also failed
    if db_exists:
        show_database_error_popup(f"ChromaDBAdmin initialization failed: {e}")
    else:
        print("ℹ️  No existing database found - will create new one on first use")

# Display startup banner
startup_banner()

@app.route('/')
def index():
    """Redirect to admin dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    """Main admin dashboard"""
    database_status = {
        'initialized': chromadb_admin is not None,
        'has_connection_issues': False,
        'error_message': None,
        'startup_validation': startup_db_validation
    }
    
    # Check startup validation results
    if startup_db_validation['db_exists'] and not startup_db_validation['can_connect']:
        database_status['has_connection_issues'] = True
        database_status['error_message'] = startup_db_validation['error_message']
        flash(f"Database startup validation failed: {startup_db_validation['error_message']}", "error")
    
    if not chromadb_admin:
        flash("ChromaDB Admin not initialized. Please check your configuration.", "error")
        if not database_status['error_message']:
            database_status['error_message'] = "ChromaDB Admin not initialized"
    else:
        # Test current connection health
        try:
            health_check = chromadb_admin.health_check()
            if not health_check.get('healthy', False):
                database_status['has_connection_issues'] = True
                database_status['error_message'] = health_check.get('error', 'Unknown connection issue')
                flash(f"Database connection issues detected: {database_status['error_message']}", "warning")
        except Exception as e:
            database_status['has_connection_issues'] = True
            database_status['error_message'] = str(e)
            flash(f"Database health check failed: {e}", "error")
    
    return render_template('admin_dashboard.html', database_status=database_status)

@app.route('/admin/database', methods=['GET', 'POST'])
def manage_database():
    """Database-level operations"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    form = DatabaseForm()
    result = None
    
    if request.method == 'POST' and form.validate_on_submit():
        action = form.action.data
        
        try:
            if action == 'create':
                result = chromadb_admin.create_database()
            elif action == 'delete':
                result = chromadb_admin.delete_database()
            
            if result:
                if result.get('success'):
                    flash(result.get('message', 'Operation completed'), 'success')
                else:
                    flash(result.get('message', 'Operation failed'), 'error')
        except Exception as e:
            flash(f"Error during {action} operation: {str(e)}", 'error')
    
    # Get statistics with error handling
    try:
        stats = chromadb_admin.get_statistics()
    except Exception as e:
        stats = {"error": str(e)}
        flash(f"Error loading statistics: {str(e)}", 'error')
    
    return render_template('database_manager.html', form=form, result=result, stats=stats)

@app.route('/admin/collections', methods=['GET', 'POST'])
def manage_collections():
    """Collection management interface"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    form = CollectionForm()
    result = None
    
    if request.method == 'POST' and form.validate_on_submit():
        action = form.action.data
        collection_name = form.collection_name.data.strip()
        
        if not collection_name:
            flash("Collection name cannot be empty", "error")
        else:
            try:
                if action == 'create':
                    result = chromadb_admin.create_collection(collection_name)
                elif action == 'delete':
                    result = chromadb_admin.delete_collection(collection_name)
                elif action == 'clear':
                    result = chromadb_admin.clear_collection(collection_name)
                
                if result:
                    if result.get('success'):
                        flash(result.get('message', 'Operation completed'), 'success')
                    else:
                        flash(result.get('message', 'Operation failed'), 'error')
            except Exception as e:
                flash(f"Error during {action} operation: {str(e)}", 'error')
    
    # Get collections and statistics with error handling
    try:
        # Refresh client to ensure we see the latest data
        chromadb_admin.refresh_client()
        collections = chromadb_admin.list_collections()
    except Exception as e:
        collections = []
        flash(f"Error loading collections: {str(e)}", 'error')
    
    try:
        stats = chromadb_admin.get_statistics()
    except Exception as e:
        stats = {"error": str(e)}
    
    return render_template('collection_manager.html', 
                         form=form, 
                         collections=collections, 
                         stats=stats,
                         result=result)

@app.route('/debug/collections')
def debug_collections_template():
    """Debug endpoint to test collection template rendering"""
    if not chromadb_admin:
        return "ChromaDB Admin not available"
    
    try:
        collections = chromadb_admin.list_collections()
        return render_template('debug_collections.html', collections=collections)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/admin/collections/<collection_name>/contents')
def view_collection_contents(collection_name):
    """View contents of a specific collection"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    limit = request.args.get('limit', 10, type=int)
    
    try:
        contents = chromadb_admin.get_collection_contents(collection_name, limit)
    except Exception as e:
        contents = {"success": False, "message": f"Error loading contents: {str(e)}"}
        flash(f"Error loading collection contents: {str(e)}", 'error')
    
    return render_template('collection_contents.html', 
                         collection_name=collection_name,
                         contents=contents)

@app.route('/admin/query')
def query_interface():
    """RAG Query Interface"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Get available collections
        collections = chromadb_admin.list_collections()
        collection_names = [col['name'] for col in collections]
        
        return render_template('query_interface.html', 
                             collections=collection_names)
    except Exception as e:
        flash(f"Error loading query interface: {str(e)}", "error")
        return redirect(url_for('admin_dashboard'))

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for RAG queries"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        data = request.get_json()
        query_text = data.get('query', '').strip()
        collection_name = data.get('collection', None)
        query_type = data.get('query_type', 'standard')
        max_results = data.get('max_results', 5)
        
        if not query_text:
            return jsonify({"success": False, "error": "Query text is required"}), 400
        
        # Validate collection exists using existing ChromaDB admin instance
        if collection_name and collection_name.lower() != 'all':
            collections = chromadb_admin.list_collections()
            collection_names = [col['name'] for col in collections]
            if collection_name not in collection_names:
                return jsonify({
                    "success": False, 
                    "error": f"Collection '{collection_name}' not found. Available collections: {collection_names}"
                }), 400
        
        # Use ChromaDB admin instance for querying instead of ResumeQuerySystem
        # This avoids the instance conflict issue
        return query_with_chromadb_admin(chromadb_admin, query_text, collection_name, query_type, max_results)
        
    except Exception as e:
        print(f"❌ Query API error: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/stats')
def stats_viewer():
    """Statistics viewer"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        stats = chromadb_admin.get_statistics()
    except Exception as e:
        stats = {"error": str(e)}
        flash(f"Error loading statistics: {str(e)}", 'error')
    
    return render_template('stats_viewer.html', stats=stats)

# API endpoints for AJAX calls
@app.route('/api/database/status')
def api_database_status():
    """API endpoint for database status"""
    if not chromadb_admin:
        return jsonify({
            "success": False,
            "status": "error",
            "error": "ChromaDB Admin not initialized"
        })
    
    try:
        # Force refresh to get latest data
        chromadb_admin.refresh_client()
        stats = chromadb_admin.get_statistics()
        return jsonify({
            "success": True,
            "status": "connected" if "error" not in stats else "error",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "error",
            "error": str(e)
        })

@app.route('/api/database/create', methods=['POST'])
def api_create_database():
    """API endpoint to create database"""
    if not chromadb_admin:
        return jsonify({
            "success": False,
            "error": "ChromaDB Admin not initialized"
        })
    
    try:
        result = chromadb_admin.create_database()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/database/delete', methods=['POST'])
def api_delete_database():
    """API endpoint to delete database"""
    if not chromadb_admin:
        return jsonify({
            "success": False,
            "error": "ChromaDB Admin not initialized"
        })
    
    try:
        result = chromadb_admin.delete_database()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/database/health', methods=['GET'])
def api_database_health():
    """API endpoint for database health check"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        result = chromadb_admin.get_database_health()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/database/clear-all', methods=['POST'])
def api_clear_all_collections():
    """API endpoint to clear all collections"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        result = chromadb_admin.clear_all_collections()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/database/reset', methods=['POST'])
def api_reset_database():
    """API endpoint to reset the entire database"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        result = chromadb_admin.reset_database()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/database/stats', methods=['GET'])
def api_database_stats():
    """API endpoint for database statistics"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        # Refresh client to ensure we get current stats
        chromadb_admin.refresh_client()
        result = chromadb_admin.get_statistics()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Collection API endpoints
@app.route('/api/collections', methods=['GET'])
def api_list_collections():
    """API endpoint to list all collections"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        # Refresh client to ensure we get current collections
        chromadb_admin.refresh_client()
        collections = chromadb_admin.list_collections()
        return jsonify({
            "success": True,
            "collections": collections
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/collections', methods=['POST'])
def api_create_collection():
    """API endpoint to create a new collection"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    data = request.get_json()
    collection_name = data.get('name', '').strip()
    
    if not collection_name:
        return jsonify({"success": False, "error": "Collection name is required"}), 400
    
    try:
        result = chromadb_admin.create_collection(collection_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/collections/<collection_name>', methods=['DELETE'])
def api_delete_collection(collection_name):
    """API endpoint to delete a collection"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        result = chromadb_admin.delete_collection(collection_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/collections/<collection_name>/clear', methods=['POST'])
def api_clear_collection(collection_name):
    """API endpoint to clear a collection"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        result = chromadb_admin.clear_collection(collection_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/collections/<collection_name>/contents', methods=['GET'])
def api_collection_contents(collection_name):
    """API endpoint to get collection contents"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    limit = request.args.get('limit', 10, type=int)
    
    try:
        result = chromadb_admin.get_collection_contents(collection_name, limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/collections/<collection_name>/upload', methods=['GET', 'POST'])
def bulk_upload(collection_name):
    """Bulk upload documents to a collection using the ingest pipeline"""
    if request.method == 'GET':
        return render_template('bulk_upload.html', collection_name=collection_name)
    
    if not chromadb_admin:
        flash("ChromaDB admin not available", "error")
        return redirect(url_for('manage_collections'))
    
    try:
        # Get upload directory from form
        upload_directory = request.form.get('upload_directory')
        if not upload_directory:
            flash("Please provide an upload directory", "error")
            return redirect(url_for('bulk_upload', collection_name=collection_name))
        
        upload_path = Path(upload_directory)
        if not upload_path.exists():
            flash(f"Upload directory does not exist: {upload_directory}", "error")
            return redirect(url_for('bulk_upload', collection_name=collection_name))
        
        # Import and initialize the ingest pipeline
        sys.path.append(str(current_dir.parent.parent))
        
        # Force cleanup of existing ChromaDB instances before creating pipeline
        try:
            from chromadb_factory import cleanup_chromadb_instances
            cleanup_chromadb_instances()
            print("🧹 Cleared existing ChromaDB instances before file upload")
            
            # Brief pause to allow cleanup
            import time
            time.sleep(0.5)
        except Exception as cleanup_error:
            print(f"⚠️ ChromaDB cleanup warning: {cleanup_error}")
        
        from ingest_pipeline import ResumeIngestPipeline
        
        # Initialize pipeline with specific collection
        pipeline = ResumeIngestPipeline(collection_name=collection_name)
        
        # Process files in the directory
        success_count = 0
        error_count = 0
        processed_files = []
        
        for file_path in upload_path.glob('**/*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx']:
                try:
                    result = pipeline.process_file(str(file_path))
                    if result['success']:
                        success_count += 1
                        processed_files.append({
                            'file': file_path.name,
                            'status': 'success',
                            'chunks': result.get('chunks_added', 0)
                        })
                    else:
                        error_count += 1
                        processed_files.append({
                            'file': file_path.name,
                            'status': 'error',
                            'error': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    error_count += 1
                    processed_files.append({
                        'file': file_path.name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        if success_count > 0:
            flash(f"Successfully uploaded {success_count} resume(s) to collection '{collection_name}'", "success")
        if error_count > 0:
            flash(f"{error_count} resume(s) failed to upload", "warning")
        
        return render_template('bulk_upload_results.html', 
                             collection_name=collection_name,
                             processed_files=processed_files,
                             success_count=success_count,
                             error_count=error_count)
        
    except Exception as e:
        flash(f"Bulk upload failed: {str(e)}", "error")
        return redirect(url_for('bulk_upload', collection_name=collection_name))

@app.route('/api/collections/<collection_name>/upload', methods=['POST'])
def api_bulk_upload(collection_name):
    """API endpoint for bulk upload with file upload support"""
    print("🔍 API ENDPOINT CALLED!")
    print(f"🔍 Collection: {collection_name}")
    print(f"🔍 Request method: {request.method}")
    print(f"🔍 Request form: {request.form}")
    
    if not chromadb_admin:
        print("❌ ChromaDB admin not available")
        return jsonify({"success": False, "error": "ChromaDB admin not available"}), 500
    
    try:
        upload_type = request.form.get('upload_type', 'directory')
        print(f"🔍 Upload type: {upload_type}")
        
        if upload_type == 'directory':
            # Directory upload
            upload_directory = request.form.get('upload_directory')
            print(f"🔍 Upload directory: {upload_directory}")
            if not upload_directory:
                return jsonify({"success": False, "error": "Upload directory required"}), 400
            
            upload_path = Path(upload_directory)
            if not upload_path.exists():
                return jsonify({"success": False, "error": f"Directory does not exist: {upload_directory}"}), 400
            
            # Check if directory has files
            files = list(upload_path.glob('**/*'))
            supported_files = [f for f in files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
            print(f"🔍 Found {len(supported_files)} supported files")
            
            if not supported_files:
                return jsonify({"success": False, "error": "No supported files found in directory"}), 400
            
            # Process directory with timeout handling
            sys.path.append(str(current_dir.parent.parent))
            print(f"🔍 Trying to import ResumeIngestPipeline...")
            
            # Force cleanup of existing ChromaDB instances before creating pipeline
            try:
                from chromadb_factory import cleanup_chromadb_instances
                cleanup_chromadb_instances()
                print("🧹 Cleared existing ChromaDB instances before directory upload")
                
                # Brief pause to allow cleanup
                import time
                time.sleep(0.5)
            except Exception as cleanup_error:
                print(f"⚠️ ChromaDB cleanup warning: {cleanup_error}")
            
            try:
                from ingest_pipeline import ResumeIngestPipeline
                print(f"🔍 Successfully imported ResumeIngestPipeline")
                
                print(f"🔍 Creating pipeline for collection: {collection_name}")
                pipeline = ResumeIngestPipeline(collection_name=collection_name)
                print(f"✅ Pipeline created successfully")
                
            except Exception as pipeline_error:
                print(f"❌ Pipeline creation failed: {pipeline_error}")
                return jsonify({
                    "success": False, 
                    "error": f"Failed to initialize pipeline: {str(pipeline_error)}"
                }), 500
            
            results = []
            processed_count = 0
            
            for file_path in supported_files:
                try:
                    print(f"🔍 Processing file {processed_count + 1}/{len(supported_files)}: {file_path.name}")
                    success, resume_id, chunks_added = pipeline.add_resume(str(file_path))
                    print(f"✅ Result: success={success}, resume_id={resume_id}, chunks={chunks_added}")
                    print(f"📊 Resume processed: {file_path.name} ({'✅ SUCCESS' if success else '❌ FAILED'})")
                    
                    results.append({
                        'file': file_path.name,
                        'success': success,
                        'chunks': chunks_added,
                        'resume_id': resume_id,
                        'resume_count': 1 if success else 0,  # Always 1 resume per file
                        'error': None if success else "Failed to process file"
                    })
                    processed_count += 1
                    
                except Exception as file_error:
                    print(f"❌ Error processing {file_path}: {str(file_error)}")
                    results.append({
                        'file': file_path.name,
                        'success': False,
                        'chunks': 0,
                        'resume_count': 0,  # Failed upload = 0 resumes
                        'error': str(file_error)
                    })
                    processed_count += 1
            
            success_count = sum(1 for r in results if r['success'])
            
            # Refresh ChromaDB client to ensure new data is visible
            if success_count > 0:
                print("🔄 Refreshing ChromaDB client to show new data...")
                chromadb_admin.refresh_client()
            
            # Print upload summary for directory
            print(f"\n📈 DIRECTORY UPLOAD SUMMARY:")
            print(f"   📊 Total resumes processed: {len(results)}")
            print(f"   ✅ Successful uploads: {success_count}")
            print(f"   ❌ Failed uploads: {len(results) - success_count}")
            print(f"   📦 Total chunks created: {sum(r.get('chunks', 0) for r in results)}")
            print(f"   📁 Collection: {collection_name}")
            print(f"   📂 Source directory: {upload_directory}\n")
            
            return jsonify({
                "success": True,
                "message": f"Processed {len(results)} resume(s), {success_count} successful",
                "results": results,
                "success_count": success_count,
                "error_count": len(results) - success_count,
                "resume_count": success_count,  # Clear resume count
                "total_chunks": sum(r.get('chunks', 0) for r in results)  # Total chunks for reference
            })
        
        elif upload_type == 'files':
            # File upload via form
            uploaded_files = request.files.getlist('files')
            if not uploaded_files:
                return jsonify({"error": "No files uploaded"}), 400
            
            # Use existing ChromaDB connection with pipeline to avoid conflicts
            if not chromadb_admin:
                return jsonify({"error": "ChromaDB admin not initialized"}), 500
            
            # Import the pipeline but use existing connection
            sys.path.append(str(current_dir.parent.parent))
            from ingest_pipeline import ResumeIngestPipeline
            
            # Create pipeline with existing database connection
            try:
                # Get the existing database from admin
                existing_db = chromadb_admin.get_existing_db_connection()
                
                if existing_db:
                    # Create pipeline with existing connection
                    pipeline = ResumeIngestPipeline(
                        collection_name=collection_name, 
                        persist_directory=str(chromadb_admin.db_path),
                        use_existing_db=existing_db
                    )
                    print("✅ Using existing ChromaDB connection for pipeline")
                else:
                    raise Exception("Could not get existing database connection")
                    
            except Exception as e:
                print(f"⚠️ Could not reuse connection: {e}")
                print("🧹 Cleaning up connections before creating new pipeline...")
                
                # Force cleanup of all connections before creating new one
                try:
                    from chromadb_factory import cleanup_chromadb_instances
                    cleanup_chromadb_instances()
                    
                    # Also refresh admin client to clear its connection
                    chromadb_admin.refresh_client()
                    
                    # Brief pause to allow cleanup
                    import time
                    time.sleep(1.0)
                    print("✅ Cleanup completed, creating new pipeline...")
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup warning: {cleanup_error}")
                
                # Now create new pipeline
                pipeline = ResumeIngestPipeline(collection_name=collection_name)
                
            results = []
            
            # Create temporary directory for uploaded files
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                for file in uploaded_files:
                    if file.filename and file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
                        # Save uploaded file temporarily
                        file_path = temp_path / file.filename
                        file.save(str(file_path))
                        
                        try:
                            print(f"🔍 Processing uploaded file: {file.filename}")
                            success, resume_id, chunks_added = pipeline.add_resume(str(file_path), original_filename=file.filename)
                            print(f"✅ Result: success={success}, resume_id={resume_id}, chunks={chunks_added}")
                            print(f"📊 Resume uploaded: {file.filename} ({'✅ SUCCESS' if success else '❌ FAILED'})")
                            results.append({
                                'file': file.filename,
                                'success': success,
                                'chunks': chunks_added,
                                'resume_id': resume_id,
                                'resume_count': 1 if success else 0,  # Always 1 resume per file
                                'error': None if success else "Failed to process file"
                            })
                        except Exception as file_error:
                            print(f"❌ DETAILED ERROR processing {file.filename}: {str(file_error)}")
                            print(f"❌ ERROR TYPE: {type(file_error).__name__}")
                            import traceback
                            print(f"❌ FULL TRACEBACK: {traceback.format_exc()}")
                            results.append({
                                'file': file.filename,
                                'success': False,
                                'chunks': 0,
                                'resume_count': 0,  # Failed upload = 0 resumes
                                'error': f"Error: {str(file_error)}"
                            })
            
            success_count = sum(1 for r in results if r['success'])
            
            # Clean up pipeline connections to prevent conflicts
            try:
                if hasattr(pipeline, 'db') and pipeline.db:
                    del pipeline.db
                del pipeline
                print("🧹 Cleaned up pipeline connections")
            except Exception as cleanup_error:
                print(f"⚠️ Pipeline cleanup warning: {cleanup_error}")
            
            # Refresh ChromaDB client to ensure new data is visible
            if success_count > 0:
                print("🔄 Refreshing ChromaDB client to show new data...")
                chromadb_admin.refresh_client()
            
            # Print upload summary for files
            print(f"\n📈 FILE UPLOAD SUMMARY:")
            print(f"   📊 Total resumes processed: {len(results)}")
            print(f"   ✅ Successful uploads: {success_count}")
            print(f"   ❌ Failed uploads: {len(results) - success_count}")
            print(f"   📦 Total chunks created: {sum(r.get('chunks', 0) for r in results)}")
            print(f"   📁 Collection: {collection_name}\n")
            
            return jsonify({
                "success": True,
                "message": f"Processed {len(results)} files, {success_count} successful",
                "results": results,
                "success_count": success_count,
                "error_count": len(results) - success_count
            })
        
        else:
            return jsonify({"error": "Invalid upload type"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Bulk upload failed: {str(e)}"}), 500

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('admin_dashboard.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    flash("An internal error occurred. Please try again.", "error")
    return render_template('admin_dashboard.html'), 500

def cleanup_and_exit():
    """Gracefully cleanup ChromaDB connections on exit"""
    print("\n🔄 Gracefully shutting down...")
    try:
        if chromadb_admin:
            print("🧹 Cleaning up ChromaDB connections...")
            # Use the dedicated close method
            chromadb_admin.close_client()
        
        # Also cleanup the factory cached instances
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from chromadb_factory import cleanup_chromadb_instances
            cleanup_chromadb_instances()
        except Exception as e:
            print(f"⚠️ Factory cleanup error: {e}")
            
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")
    
    # Force garbage collection to clean up any remaining references
    import gc
    gc.collect()
    print("✅ Cleanup completed")

def signal_handler(signum, frame):
    """Handle interrupt signals (Ctrl+C)"""
    print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
    cleanup_and_exit()
    print("👋 Goodbye!")
    sys.exit(0)

# Register signal handlers and cleanup functions
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
atexit.register(cleanup_and_exit)  # Called on normal exit

@app.route('/debug/template')
def debug_template():
    """Debug endpoint to check template content"""
    try:
        import os
        template_path = os.path.join(app.template_folder, 'query_interface.html')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
                # Check if our modifications are there
                has_v3_title = 'v3.0' in content
                has_status_box = 'statusRow' in content
                has_debug_marker = 'TEMPLATE DEBUG' in content
                
                return {
                    'template_path': template_path,
                    'template_exists': True,
                    'has_v3_title': has_v3_title,
                    'has_status_box': has_status_box,
                    'has_debug_marker': has_debug_marker,
                    'template_size': len(content)
                }
        else:
            return {'error': f'Template not found at {template_path}'}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':    
    # Check if templates directory exists
    templates_dir = current_dir.parent / 'templates'
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        print("Please ensure the templates directory exists with HTML files.")
        sys.exit(1)
    
    try:
        # Get port from environment variable for Azure App Service compatibility
        port = int(os.getenv('PORT', 5001))
        host = '0.0.0.0'  # Bind to all interfaces for container deployment
        
        print(f"🚀 Starting Flask app on {host}:{port}")
        app.run(debug=False, port=port, host=host, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt received")
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
    finally:
        # Ensure cleanup happens even if app.run() exits unexpectedly
        cleanup_and_exit()
        sys.exit(1)