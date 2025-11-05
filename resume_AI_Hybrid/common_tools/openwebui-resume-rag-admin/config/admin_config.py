from pathlib import Path

class AdminConfig:
    """Configuration settings for the admin interface."""

    def __init__(self):
        self.chroma_db_path = Path("C:/Users/DamonDesonier/repos/langachain_rag/resume_vectordb/")
        self.default_collection_name = "resumes"
        self.admin_ui_title = "ChromaDB Admin Interface"
        self.enable_logging = True
        self.log_file_path = Path("logs/admin_interface.log")
        self.max_collection_size = 1000  # Maximum number of items in a collection
        self.session_timeout = 30  # Session timeout in minutes

    def get_chroma_db_path(self):
        return self.chroma_db_path

    def get_default_collection_name(self):
        return self.default_collection_name

    def get_admin_ui_title(self):
        return self.admin_ui_title

    def is_logging_enabled(self):
        return self.enable_logging

    def get_log_file_path(self):
        return self.log_file_path

    def get_max_collection_size(self):
        return self.max_collection_size

    def get_session_timeout(self):
        return self.session_timeout

admin_config = AdminConfig()