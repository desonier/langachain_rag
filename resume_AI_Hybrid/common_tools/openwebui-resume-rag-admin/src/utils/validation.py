def validate_collection_name(name: str) -> bool:
    """Validate the collection name for ChromaDB."""
    if not name:
        return False
    if len(name) < 3 or len(name) > 50:
        return False
    if not name.isalnum():
        return False
    return True

def validate_database_path(path: str) -> bool:
    """Validate the database path."""
    if not path:
        return False
    if not Path(path).exists():
        return False
    return True

def validate_clear_confirmation(confirmation: str) -> bool:
    """Validate user confirmation for clearing contents."""
    return confirmation.lower() in ['yes', 'y']

def validate_statistics_request(request: dict) -> bool:
    """Validate the request for statistics."""
    required_keys = ['include_details', 'format']
    return all(key in request for key in required_keys) and isinstance(request['include_details'], bool) and request['format'] in ['json', 'text']