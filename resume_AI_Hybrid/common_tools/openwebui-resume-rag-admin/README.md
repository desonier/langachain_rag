# OpenWebUI Resume RAG Admin Interface

This project provides an admin interface for managing the ChromaDB database within the OpenWebUI Resume RAG System. The admin interface allows users to perform various operations related to the ChromaDB, including creating, deleting, clearing contents, listing collections, and displaying statistics.

## Features

- **ChromaDB Management**: Create, delete, and clear contents of the ChromaDB database.
- **Collection Management**: Add and remove collections within the ChromaDB.
- **Statistics Dashboard**: View statistics related to the ChromaDB database.
- **User-Friendly Interface**: Intuitive UI for easy navigation and management.

## Project Structure

- `src/admin/`: Contains the admin-related functionalities, including database operations and collection management.
- `src/ui/`: Contains the user interface components for the admin dashboard.
- `src/models/`: Contains data models used in the admin interface.
- `src/utils/`: Contains utility functions for validation and formatting.
- `templates/`: Contains HTML templates for the admin interface.
- `static/`: Contains static files such as CSS and JavaScript for the admin interface.
- `config/`: Contains configuration files for the admin interface and database.
- `tests/`: Contains unit tests for the admin functionalities.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd openwebui-resume-rag-admin
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying the `.env.example` to `.env` and updating the values accordingly.

## Usage

To start the application, run the following command:
```
python src/main.py
```

Access the admin interface by navigating to `http://localhost:8000/admin` in your web browser.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.