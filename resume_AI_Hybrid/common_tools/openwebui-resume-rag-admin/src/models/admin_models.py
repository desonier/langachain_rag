from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional

class CollectionCreateModel(BaseModel):
    """Model for creating a new collection in ChromaDB."""
    name: str
    description: Optional[str] = None

class CollectionDeleteModel(BaseModel):
    """Model for deleting a collection from ChromaDB."""
    name: str

class CollectionClearModel(BaseModel):
    """Model for clearing contents of a collection in ChromaDB."""
    name: str

class CollectionListModel(BaseModel):
    """Model for listing collections in ChromaDB."""
    collections: List[str]

class DatabaseStatsModel(BaseModel):
    """Model for displaying statistics of the ChromaDB."""
    total_collections: int
    total_documents: int
    total_size_mb: float
    last_updated: str

class AdminResponseModel(BaseModel):
    """Model for standard responses in the admin interface.""""""
Admin interface models and forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, FloatField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class CollectionForm(FlaskForm):
    """Form for collection management operations"""
    collection_name = StringField(
        'Collection Name', 
        validators=[DataRequired(), Length(min=1, max=50)],
        render_kw={"placeholder": "Enter collection name"}
    )
    
    action = SelectField(
        'Action',
        choices=[
            ('create', 'Create Collection'),
            ('delete', 'Delete Collection'),
            ('clear', 'Clear Contents')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Execute Action')

class DatabaseForm(FlaskForm):
    """Form for database-level operations"""
    db_path = StringField(
        'Database Path',
        render_kw={"placeholder": "Leave empty for default path"}
    )
    
    action = SelectField(
        'Database Action',
        choices=[
            ('create', 'Create/Initialize Database'),
            ('delete', 'Delete Entire Database')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Execute Database Action')

class DocumentUploadForm(FlaskForm):
    """Form for uploading documents to collections"""
    collection_name = StringField(
        'Target Collection',
        validators=[DataRequired(), Length(min=1, max=50)],
        render_kw={"placeholder": "Collection name to upload to"}
    )
    
    document_text = TextAreaField(
        'Document Content',
        validators=[DataRequired(), Length(min=1, max=10000)],
        render_kw={
            "placeholder": "Paste document content here...",
            "rows": 10
        }
    )
    
    document_id = StringField(
        'Document ID (optional)',
        render_kw={"placeholder": "Auto-generated if left empty"}
    )
    
    metadata_source = StringField(
        'Source (optional)',
        render_kw={"placeholder": "e.g., filename.txt"}
    )
    
    metadata_type = SelectField(
        'Document Type',
        choices=[
            ('', 'Select type (optional)'),
            ('resume', 'Resume'),
            ('job_description', 'Job Description'),
            ('cover_letter', 'Cover Letter'),
            ('other', 'Other')
        ]
    )
    
    submit = SubmitField('Upload Document')

class SearchForm(FlaskForm):
    """Form for searching within collections"""
    collection_name = SelectField(
        'Search In Collection',
        choices=[],  # Will be populated dynamically
        validators=[DataRequired()]
    )
    
    query = StringField(
        'Search Query',
        validators=[DataRequired(), Length(min=1, max=500)],
        render_kw={"placeholder": "Enter search terms..."}
    )
    
    limit = SelectField(
        'Number of Results',
        choices=[
            ('5', '5 results'),
            ('10', '10 results'),
            ('20', '20 results'),
            ('50', '50 results')
        ],
        default='10'
    )
    
    submit = SubmitField('Search')

class ConfigForm(FlaskForm):
    """Form for configuration settings"""
    database_path = StringField(
        'Database Path',
        validators=[DataRequired()],
        render_kw={"placeholder": "Path to ChromaDB database"}
    )
    
    embedding_model = SelectField(
        'Embedding Model',
        choices=[
            ('default', 'Default ChromaDB'),
            ('openai', 'OpenAI Embeddings'),
            ('azure-openai', 'Azure OpenAI Embeddings')
        ],
        default='default'
    )
    
    max_collection_size = SelectField(
        'Max Collection Size',
        choices=[
            ('1000', '1,000 documents'),
            ('5000', '5,000 documents'),
            ('10000', '10,000 documents'),
            ('50000', '50,000 documents'),
            ('-1', 'Unlimited')
        ],
        default='10000'
    )
    
    auto_backup = SelectField(
        'Auto Backup',
        choices=[
            ('enabled', 'Enabled'),
            ('disabled', 'Disabled')
        ],
        default='disabled'
    )
    
    submit = SubmitField('Save Configuration')

class ModelSelectionForm(FlaskForm):
    """Form for model selection settings"""
    # LLM Configuration
    llm_provider = SelectField(
        'LLM Provider',
        choices=[
            ('azure-openai', 'Azure OpenAI'),
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic')
        ],
        default='azure-openai',
        validators=[DataRequired()]
    )
    
    llm_model = SelectField(
        'LLM Model',
        choices=[
            ('gpt-4', 'GPT-4'),
            ('gpt-4-turbo', 'GPT-4 Turbo'),
            ('gpt-35-turbo', 'GPT-3.5 Turbo'),
            ('gpt-4o', 'GPT-4o')
        ],
        default='gpt-4',
        validators=[DataRequired()]
    )
    
    # Embedding Configuration
    embedding_provider = SelectField(
        'Embedding Provider',
        choices=[
            ('huggingface', 'HuggingFace Transformers'),
            ('azure-openai', 'Azure OpenAI'),
            ('openai', 'OpenAI')
        ],
        default='huggingface',
        validators=[DataRequired()]
    )
    
    embedding_model = SelectField(
        'Embedding Model',
        choices=[
            ('sentence-transformers/all-MiniLM-L6-v2', 'all-MiniLM-L6-v2 (Fast)'),
            ('sentence-transformers/all-mpnet-base-v2', 'all-mpnet-base-v2 (Better)'),
            ('text-embedding-ada-002', 'Ada-002 (OpenAI)'),
            ('text-embedding-3-small', 'Embedding-3-Small'),
            ('text-embedding-3-large', 'Embedding-3-Large')
        ],
        default='sentence-transformers/all-MiniLM-L6-v2',
        validators=[DataRequired()]
    )
    
    # API Keys (optional overrides)
    openai_api_key = StringField(
        'OpenAI API Key (optional)',
        render_kw={"placeholder": "sk-...", "type": "password"}
    )
    
    anthropic_api_key = StringField(
        'Anthropic API Key (optional)',
        render_kw={"placeholder": "sk-ant-...", "type": "password"}
    )
    
    # Azure OpenAI Configuration
    azure_endpoint = StringField(
        'Azure OpenAI Endpoint',
        render_kw={"placeholder": "https://your-resource.openai.azure.com"}
    )
    
    azure_api_key = StringField(
        'Azure API Key',
        render_kw={"placeholder": "Your Azure OpenAI API key", "type": "password"}
    )
    
    azure_api_version = StringField(
        'Azure API Version',
        default='2024-02-15-preview',
        render_kw={"placeholder": "2024-02-15-preview"}
    )
    
    azure_llm_deployment = StringField(
        'Azure LLM Deployment Name',
        render_kw={"placeholder": "gpt-4-deployment"}
    )
    
    azure_embedding_deployment = StringField(
        'Azure Embedding Deployment Name',
        render_kw={"placeholder": "text-embedding-deployment"}
    )
    
    # OpenAI Configuration
    openai_base_url = StringField(
        'OpenAI Base URL (Optional)',
        render_kw={"placeholder": "https://api.openai.com/v1"}
    )
    
    openai_organization = StringField(
        'OpenAI Organization ID (Optional)',
        render_kw={"placeholder": "org-..."}
    )
    
    # HuggingFace Configuration
    huggingface_api_key = StringField(
        'HuggingFace API Key (Optional)',
        render_kw={"placeholder": "hf_...", "type": "password"}
    )

    huggingface_endpoint = StringField(
        'HuggingFace Inference Endpoint (Optional)',
        render_kw={"placeholder": "https://api-inference.huggingface.co"}
    )

    # Ollama Configuration
    ollama_api_key = StringField(
        'Ollama Cloud API Key (Optional)',
        render_kw={"placeholder": "your_ollama_api_key", "type": "password"}
    )

    ollama_base_url = StringField(
        'Ollama Base URL (Optional)',
        render_kw={"placeholder": "http://localhost:11434 or https://ollama.com"}
    )    # Model parameters
    temperature = FloatField(
        'Temperature',
        default=0.1,
        validators=[NumberRange(min=0.0, max=2.0)]
    )
    
    # Custom model management
    custom_llm_model_name = StringField(
        'Custom LLM Model Name',
        render_kw={"placeholder": "Enter custom model name"}
    )
    
    custom_embedding_model_name = StringField(
        'Custom Embedding Model Name',
        render_kw={"placeholder": "Enter custom embedding model name"}
    )
    
    # Custom Provider Configuration
    custom_provider_name = StringField(
        'Provider Name',
        render_kw={"placeholder": "e.g., ollama, local-llm"}
    )
    
    custom_provider_display_name = StringField(
        'Display Name',
        render_kw={"placeholder": "e.g., Local Ollama, Custom OpenAI"}
    )
    
    custom_provider_type = SelectField(
        'Provider Type',
        choices=[
            ('llm', 'LLM Provider'),
            ('embedding', 'Embedding Provider')
        ],
        default='llm'
    )
    
    custom_provider_base_url = StringField(
        'Base URL',
        render_kw={"placeholder": "e.g., http://localhost:11434/v1"}
    )
    
    custom_provider_api_key_env = StringField(
        'API Key Environment Variable',
        render_kw={"placeholder": "e.g., OLLAMA_API_KEY (optional)"}
    )
    
    submit = SubmitField('Save Model Configuration')

class ConfigForm(FlaskForm):
    """Form for configuration settings"""
    database_path = StringField(
        'Database Path',
        validators=[DataRequired()],
        render_kw={"placeholder": "Path to ChromaDB database"}
    )
    
    embedding_model = SelectField(
        'Embedding Model',
        choices=[
            ('default', 'Default ChromaDB'),
            ('openai', 'OpenAI Embeddings'),
            ('azure-openai', 'Azure OpenAI Embeddings')
        ],
        default='default'
    )
    
    max_collection_size = SelectField(
        'Max Collection Size',
        choices=[
            ('1000', '1,000 documents'),
            ('5000', '5,000 documents'),
            ('10000', '10,000 documents'),
            ('50000', '50,000 documents'),
            ('-1', 'Unlimited')
        ],
        default='10000'
    )
    
    auto_backup = SelectField(
        'Auto Backup',
        choices=[
            ('enabled', 'Enabled'),
            ('disabled', 'Disabled')
        ],
        default='disabled'
    )
    success: bool
    message: str
    data: Optional[dict] = None