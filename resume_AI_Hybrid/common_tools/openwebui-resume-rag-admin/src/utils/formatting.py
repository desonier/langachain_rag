def format_chromadb_stats(stats: dict) -> str:
    """Format the statistics of the ChromaDB for display."""
    formatted_stats = [
        f"Total Collections: {stats.get('total_collections', 0)}",
        f"Total Documents: {stats.get('total_documents', 0)}",
        f"Total Size: {stats.get('total_size', '0 MB')}",
        f"Last Updated: {stats.get('last_updated', 'N/A')}"
    ]
    return "\n".join(formatted_stats)

def format_collection_list(collections: list) -> str:
    """Format the list of collections for display."""
    if not collections:
        return "No collections found."
    
    formatted_collections = ["Collections:"]
    for collection in collections:
        formatted_collections.append(f"- {collection}")
    return "\n".join(formatted_collections)

def format_operation_result(success: bool, message: str) -> str:
    """Format the result of an operation for display."""
    status = "✅ Success" if success else "❌ Failure"
    return f"{status}: {message}"

def format_clear_confirmation(collection_name: str) -> str:
    """Format the confirmation message for clearing a collection."""
    return f"Are you sure you want to clear the contents of the collection '{collection_name}'? This action cannot be undone."