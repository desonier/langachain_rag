from flask import Blueprint, render_template, request, redirect, url_for, flash
from admin.chromadb_admin import ChromaDBAdmin

admin_interface = Blueprint('admin_interface', __name__)
chromadb_admin = ChromaDBAdmin()

@admin_interface.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            collection_name = request.form.get('collection_name')
            if chromadb_admin.create_collection(collection_name):
                flash(f'Collection "{collection_name}" created successfully!', 'success')
            else:
                flash(f'Failed to create collection "{collection_name}".', 'error')
        elif action == 'delete':
            collection_name = request.form.get('collection_name')
            if chromadb_admin.delete_collection(collection_name):
                flash(f'Collection "{collection_name}" deleted successfully!', 'success')
            else:
                flash(f'Failed to delete collection "{collection_name}".', 'error')
        elif action == 'clear':
            if chromadb_admin.clear_contents():
                flash('All contents cleared successfully!', 'success')
            else:
                flash('Failed to clear contents.', 'error')

    collections = chromadb_admin.list_collections()
    stats = chromadb_admin.get_statistics()
    
    return render_template('admin_dashboard.html', collections=collections, stats=stats)