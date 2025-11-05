from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.admin.chromadb_admin import ChromaDBAdmin

collection_viewer = Blueprint('collection_viewer', __name__)
chroma_db_admin = ChromaDBAdmin()

@collection_viewer.route('/collections', methods=['GET', 'POST'])
def manage_collections():
    if request.method == 'POST':
        action = request.form.get('action')
        collection_name = request.form.get('collection_name')

        if action == 'create':
            chroma_db_admin.create_collection(collection_name)
            flash(f'Collection "{collection_name}" created successfully!', 'success')
        elif action == 'delete':
            chroma_db_admin.delete_collection(collection_name)
            flash(f'Collection "{collection_name}" deleted successfully!', 'success')
        elif action == 'clear':
            chroma_db_admin.clear_collection(collection_name)
            flash(f'Contents of collection "{collection_name}" cleared successfully!', 'success')

    collections = chroma_db_admin.list_collections()
    stats = chroma_db_admin.get_statistics()

    return render_template('collection_manager.html', collections=collections, stats=stats)