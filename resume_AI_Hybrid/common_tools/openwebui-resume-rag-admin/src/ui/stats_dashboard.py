from flask import Blueprint, render_template, request, redirect, url_for, flash
from admin.chromadb_admin import ChromaDBAdmin

class StatsDashboard:
    def __init__(self):
        self.chroma_db_admin = ChromaDBAdmin()

    def create_routes(self, app):
        @app.route('/admin/stats', methods=['GET', 'POST'])
        def stats_dashboard():
            if request.method == 'POST':
                action = request.form.get('action')
                if action == 'clear':
                    self.chroma_db_admin.clear_contents()
                    flash('Database contents cleared successfully!', 'success')
                elif action == 'delete':
                    self.chroma_db_admin.delete_database()
                    flash('Database deleted successfully!', 'success')

            stats = self.chroma_db_admin.get_statistics()
            return render_template('stats_viewer.html', stats=stats)

    def display_statistics(self):
        stats = self.chroma_db_admin.get_statistics()
        return stats

    def list_contents(self):
        contents = self.chroma_db_admin.list_contents()
        return contents

    def clear_contents(self):
        self.chroma_db_admin.clear_contents()

    def delete_database(self):
        self.chroma_db_admin.delete_database()