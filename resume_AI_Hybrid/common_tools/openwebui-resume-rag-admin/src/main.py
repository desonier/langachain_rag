from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sys
import os
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

# Use environment variable for secret key or default
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize ChromaDBAdmin with error handling
try:
    chromadb_admin = ChromaDBAdmin()
    print("✅ ChromaDBAdmin initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize ChromaDBAdmin: {e}")
    chromadb_admin = None

@app.route('/')
def index():
    """Redirect to admin dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    """Main admin dashboard"""
    if not chromadb_admin:
        flash("ChromaDB Admin not initialized. Please check your configuration.", "error")
    return render_template('admin_dashboard.html')

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
            flash(f"Successfully uploaded {success_count} files to collection '{collection_name}'", "success")
        if error_count > 0:
            flash(f"{error_count} files failed to upload", "warning")
        
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
                    
                    results.append({
                        'file': file_path.name,
                        'success': success,
                        'chunks': chunks_added,
                        'resume_id': resume_id,
                        'error': None if success else "Failed to process file"
                    })
                    processed_count += 1
                    
                except Exception as file_error:
                    print(f"❌ Error processing {file_path}: {str(file_error)}")
                    results.append({
                        'file': file_path.name,
                        'success': False,
                        'chunks': 0,
                        'error': str(file_error)
                    })
                    processed_count += 1
            
            success_count = sum(1 for r in results if r['success'])
            return jsonify({
                "success": True,
                "message": f"Processed {len(results)} files, {success_count} successful",
                "results": results,
                "success_count": success_count,
                "error_count": len(results) - success_count
            })
        
        elif upload_type == 'files':
            # File upload via form
            uploaded_files = request.files.getlist('files')
            if not uploaded_files:
                return jsonify({"error": "No files uploaded"}), 400
            
            sys.path.append(str(current_dir.parent.parent))
            from ingest_pipeline import ResumeIngestPipeline
            
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
                            results.append({
                                'file': file.filename,
                                'success': success,
                                'chunks': chunks_added,
                                'resume_id': resume_id,
                                'error': None if success else "Failed to process file"
                            })
                        except Exception as e:
                            print(f"❌ Error processing {file.filename}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            results.append({
                                'file': file.filename,
                                'success': False,
                                'chunks': 0,
                                'error': str(e)
                            })
            
            success_count = sum(1 for r in results if r['success'])
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

if __name__ == '__main__':
    print("🚀 Starting ChromaDB Admin Interface...")
    
    # Check if templates directory exists
    templates_dir = current_dir.parent / 'templates'
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        print("Please ensure the templates directory exists with HTML files.")
        sys.exit(1)
    
    print("📊 Dashboard: http://localhost:5001")
    print("🗂️ Collections: http://localhost:5001/admin/collections")
    print("📈 Statistics: http://localhost:5001/admin/stats")
    print("🛠️ Database: http://localhost:5001/admin/database")
    
    try:
        app.run(debug=False, port=5001, host='127.0.0.1', use_reloader=False)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        sys.exit(1)