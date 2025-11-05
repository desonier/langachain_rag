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
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

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
    success: bool
    message: str
    data: Optional[dict] = None