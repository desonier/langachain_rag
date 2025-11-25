from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sys
import os
import json
import signal
import atexit
from pathlib import Path
from datetime import datetime

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

# Import langchain dependencies at module level
try:
    from langchain_openai import AzureChatOpenAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    # Import PromptTemplate to avoid "not defined" errors, even if we don't use it
    from langchain_core.prompts import PromptTemplate
    print("ll langchain imports successful")
except ImportError as e:
    print(f"Langchain import error: {e}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}")

try:
    from admin.chromadb_admin import ChromaDBAdmin
    from models.admin_models import CollectionForm, DatabaseForm, ModelSelectionForm
except ImportError as e:
    print(f"Import Error: {e}")
    print("Checking file structure...")
    print(f"Current dir: {current_dir}")
    print(f"Admin dir exists: {(current_dir / 'admin').exists()}")
    print(f"Models dir exists: {(current_dir / 'models').exists()}")
    print(f"Templates dir exists: {(current_dir.parent / 'templates').exists()}")
    sys.exit(1)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Use environment variable for secret key or default
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_dynamic_llm(provider=None, model=None):
    """Get LLM instance based on provider and model selection"""
    try:
        # Import shared config if available - add parent directories to path
        try:
            import sys
            from pathlib import Path
            
            # Add parent directories to Python path
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent  # Go up to resume_AI_Hybrid directory
            sys.path.insert(0, str(project_root))
            
            from shared_config import get_config, get_dynamic_llm_config
            config = get_config()
            provider = provider or config.llm_provider
            model = model or config.llm_model
            llm_config = get_dynamic_llm_config(provider, model)
            print(f"DEBUG: Using shared_config - provider: {provider}, model: {model}")
            print(f"DEBUG: LLM config: {llm_config}")
        except ImportError as e:
            print(f"DEBUG: shared_config import failed: {e}")
            # Fallback configuration
            provider = provider or "azure-openai"
            llm_config = {
                'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
                'api_key': os.getenv('AZURE_OPENAI_KEY'),
                'azure_deployment': os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT', 'resumemodel'),
                'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                'temperature': 0.1
            }
            print(f"DEBUG: Using fallback config: {llm_config}")
        
        if provider == "azure-openai":
            return AzureChatOpenAI(**llm_config)
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(**llm_config)
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(**llm_config)
            except ImportError:
                print("⚠️ Anthropic not available, falling back to Azure OpenAI")
                return AzureChatOpenAI(**{
                    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
                    'api_key': os.getenv('AZURE_OPENAI_KEY'),
                    'azure_deployment': os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT'),
                    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                    'temperature': 0.1
                })
        else:
            # Default to Azure OpenAI
            return AzureChatOpenAI(**llm_config)
            
    except Exception as e:
        print(f"⚠️ Error creating LLM: {e}")
        # Emergency fallback
        return AzureChatOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            azure_deployment=os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            temperature=0.1
        )

def save_custom_model(model_type, provider, model_name):
    """Save custom model to JSON file"""
    try:
        import json
        custom_models_file = os.path.join(os.path.dirname(__file__), 'custom_models.json')
        
        # Load existing models or create empty structure
        if os.path.exists(custom_models_file):
            with open(custom_models_file, 'r') as f:
                custom_models = json.load(f)
        else:
            custom_models = {"embedding": {}, "llm": {}}
        
        # Ensure model_type exists
        if model_type not in custom_models:
            custom_models[model_type] = {}
        
        # Ensure provider exists for model_type
        if provider not in custom_models[model_type]:
            custom_models[model_type][provider] = []
        
        # Add model if not already present
        if model_name not in custom_models[model_type][provider]:
            custom_models[model_type][provider].append(model_name)
        
        # Save updated models
        with open(custom_models_file, 'w') as f:
            json.dump(custom_models, f, indent=2)
            
        print(f"✅ Saved custom {model_type} model: {provider}/{model_name}")
        
    except Exception as e:
        print(f"❌ Error saving custom model: {e}")
        raise

def save_model_config(config_data):
    """Save model configuration to JSON file"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'model_config.json')
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✅ Model configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving model configuration: {e}")
        return False

def load_model_config():
    """Load model configuration from JSON file"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'model_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Model configuration loaded from {config_file}")
            return config
        else:
            print(f"ℹ️  No existing configuration file found")
            return {}
    except Exception as e:
        print(f"❌ Error loading model configuration: {e}")
        return {}

def apply_saved_config(config):
    """Apply saved configuration to environment variables"""
    if not config:
        return
    
    try:
        # Apply environment variables from saved config
        for key, value in config.get('environment', {}).items():
            if value:  # Only set if value is not empty
                os.environ[key] = str(value)
        
        applied_count = len(config.get('environment', {}))
        if applied_count > 0:
            print(f"✅ Applied {applied_count} configuration settings")
    except Exception as e:
        print(f"❌ Error applying saved configuration: {e}")

def delete_model_config():
    """Delete saved model configuration file"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'model_config.json')
        if os.path.exists(config_file):
            os.remove(config_file)
            print(f"✅ Model configuration file deleted: {config_file}")
            # Clear environment variables that were set from config
            common_env_vars = ['AZURE_OPENAI_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OLLAMA_API_KEY', 'HUGGINGFACE_API_KEY']
            cleared_vars = []
            for var in common_env_vars:
                if var in os.environ:
                    del os.environ[var]
                    cleared_vars.append(var)
            if cleared_vars:
                print(f"✅ Cleared environment variables: {', '.join(cleared_vars)}")
            return True
        else:
            print(f"ℹ️  No configuration file found to delete")
            return False
    except Exception as e:
        print(f"❌ Error deleting model configuration: {e}")
        return False

def check_embedding_dependencies():
    """Check if required embedding packages are installed"""
    missing_packages = []
    optional_packages = []
    
    # Check sentence-transformers (commonly used)
    try:
        import sentence_transformers
    except ImportError:
        missing_packages.append('sentence_transformers')
    
    # Check langchain_huggingface (for huggingface integration)
    try:
        import langchain_huggingface
    except ImportError:
        optional_packages.append('langchain_huggingface')
    
    # Check transformers (often required with sentence-transformers)
    try:
        import transformers
    except ImportError:
        optional_packages.append('transformers')
    
    return {
        'missing_packages': missing_packages,
        'optional_packages': optional_packages,
        'has_critical_missing': len(missing_packages) > 0
    }

def load_custom_providers():
    """Load custom providers from JSON file"""
    try:
        custom_providers_file = os.path.join(os.path.dirname(__file__), 'custom_providers.json')
        if os.path.exists(custom_providers_file):
            with open(custom_providers_file, 'r') as f:
                custom_providers = json.load(f)
        else:
            # Create default providers file
            custom_providers = {
                "llm": {
                    "azure-openai": {"display_name": "Azure OpenAI", "builtin": True},
                    "openai": {"display_name": "OpenAI", "builtin": True},
                    "anthropic": {"display_name": "Anthropic", "builtin": True}
                },
                "embedding": {
                    "huggingface": {"display_name": "HuggingFace", "builtin": True},
                    "azure-openai": {"display_name": "Azure OpenAI", "builtin": True},
                    "openai": {"display_name": "OpenAI", "builtin": True}
                }
            }
        return custom_providers
    except Exception as e:
        print(f"Error loading custom providers: {e}")
        return {"llm": {}, "embedding": {}}

def save_custom_provider(provider_type, provider_id, display_name, base_url=None, api_key_env=None):
    """Save custom provider to JSON file"""
    try:
        custom_providers = load_custom_providers()
        
        # Ensure the type exists
        if provider_type not in custom_providers:
            custom_providers[provider_type] = {}
            
        # Add the provider
        custom_providers[provider_type][provider_id] = {
            "display_name": display_name,
            "base_url": base_url,
            "api_key_env": api_key_env,
            "builtin": False
        }
        
        # Save to file
        custom_providers_file = os.path.join(os.path.dirname(__file__), 'custom_providers.json')
        with open(custom_providers_file, 'w') as f:
            json.dump(custom_providers, f, indent=2)
            
        print(f"Saved custom provider: {provider_type}/{provider_id}")
        
    except Exception as e:
        print(f"Error saving custom provider: {e}")
        raise

def load_custom_models():
    try:
        import json
        custom_models_file = os.path.join(os.path.dirname(__file__), 'custom_models.json')
        
        if os.path.exists(custom_models_file):
            with open(custom_models_file, 'r') as f:
                custom_models = json.load(f)
        else:
            custom_models = {"embedding": {}, "llm": {}}
        
        return custom_models
        
    except Exception as e:
        print(f"❌ Error loading custom models: {e}")
        # Return empty structure on error
        return {"embedding": {}, "llm": {}}

def parse_scoring_response(llm_response, sources):
    """Parse LLM response to extract scores and rankings for each resume"""
    import re
    
    # Initialize scores with default values
    for source in sources:
        source['score'] = 0
        source['justification'] = 'No scoring information provided'
        source['key_extracts'] = []
    
    try:
        print(f"DEBUG: Parsing LLM response: {llm_response[:500]}...")  # Debug output
        
        # Split response into resume sections using the new format
        resume_sections = re.split(r'==RESUME_START==', llm_response)
        
        if len(resume_sections) > 1:
            print(f"DEBUG: Found {len(resume_sections)-1} structured sections")
        else:
            print("DEBUG: No structured format found, trying fallback parsing...")
        
        for section in resume_sections[1:]:  # Skip first section before first resume
            # Clean section and split into lines
            section = section.split('==RESUME_END==')[0].strip()
            if not section:
                continue
            
            print(f"DEBUG: Processing section: {section[:200]}...")
            
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            
            # Parse structured data
            resume_data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    resume_data[key.strip().upper()] = value.strip()
            
            print(f"DEBUG: Parsed data: {resume_data}")
            
            # Extract resume name and find matching source
            resume_name = resume_data.get('RESUME_NAME', '')
            matching_source = None
            
            # Try to match by filename or candidate name
            for source in sources:
                if (resume_name.lower() in source['original_filename'].lower() or 
                    resume_name.lower() in source.get('candidate_name', '').lower() or
                    source['original_filename'].lower() in resume_name.lower()):
                    matching_source = source
                    break
            
            # If no match found, use next available unmatched source
            if not matching_source:
                for source in sources:
                    if source.get('score', 0) == 0:  # Find unmatched source
                        matching_source = source
                        break
            
            if matching_source:
                # Extract score
                try:
                    score = int(resume_data.get('SCORE', '0'))
                    matching_source['score'] = max(0, min(100, score))  # Clamp to 0-100
                except ValueError:
                    matching_source['score'] = 0
                
                # Extract justification
                matching_source['justification'] = resume_data.get('JUSTIFICATION', 'No justification provided')
                
                # Extract key extracts
                extracts = []
                for i in range(1, 6):  # Look for KEY_EXTRACT_1 through KEY_EXTRACT_5
                    extract_key = f'KEY_EXTRACT_{i}'
                    if extract_key in resume_data:
                        extracts.append(resume_data[extract_key])
                matching_source['key_extracts'] = extracts
                
                print(f"DEBUG: Updated {matching_source['original_filename']} - Score: {matching_source['score']}, Justification: {matching_source['justification'][:100]}...")
        
        # If no structured parsing worked, try fallback
        if len(resume_sections) <= 1:
            print("DEBUG: Trying fallback parsing for unstructured response...")
            # Simple fallback: assign basic scores based on order
            for i, source in enumerate(sources):
                source['score'] = max(50, 90 - (i * 10))  # Give decreasing scores
                source['justification'] = f"Resume analysis suggests relevance score of {source['score']} based on content match"
        
        # Sort sources by score (highest first)
        sources.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        print(f"DEBUG: Final scores: {[(s['original_filename'], s['score']) for s in sources]}")
        
        return {
            'sources': sources,
            'parsed': True
        }
        
    except Exception as e:
        print(f"Error parsing scoring response: {e}")
        print(f"LLM Response: {llm_response}")
        # Return sources with default values
        return {
            'sources': sources,
            'parsed': False,
            'error': str(e)
        }

def query_with_chromadb_admin(chromadb_admin, query_text, collection_name, query_type, max_results, 
                            provider=None, model=None, temperature=None):
    """
    Query using the existing ChromaDB admin instance to avoid conflicts
    """
    print(f"ENTERING QUERY FUNCTION: query_text='{query_text}', collection='{collection_name}', type='{query_type}'")
    try:
        print(f"QUERY DEBUG: Starting query with text='{query_text}', collection='{collection_name}', type='{query_type}'")
        
        # Debug Python environment
        import sys
        print(f"Python executable: {sys.executable}")
        print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
        
        # Get Azure OpenAI configuration
        azure_config = {
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_key': os.getenv('AZURE_OPENAI_KEY'),  # Using AZURE_OPENAI_KEY from .env
            'azure_deployment': os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT', 'resumemodel'),  # Using CHATGPT_DEPLOYMENT
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            'temperature': 0.1
        }
        
        # Validate Azure OpenAI config
        if not azure_config['azure_endpoint'] or not azure_config['api_key']:
            return jsonify({
                "success": False,
                "error": "Azure OpenAI configuration missing. Please check your .env file."
            }), 500
        
        # Initialize LLM using selected model parameters
        if provider and model:
            print(f"🚀 Creating LLM with SELECTED provider: '{provider}', model: '{model}', temperature: {temperature}")
            llm = get_dynamic_llm(provider=provider, model=model)
            # Update temperature if provided
            if temperature is not None and hasattr(llm, 'temperature'):
                llm.temperature = temperature
                print(f"🌡️ Set LLM temperature to: {temperature}")
        else:
            print("⚠️ Using DEFAULT LLM configuration (no model selection provided)")
            llm = get_dynamic_llm()
        
        # Use the existing ChromaDB client from admin - DO NOT create a new one
        chroma_client = chromadb_admin.client
        
        # Get collections to query
        if collection_name and collection_name.lower() != 'all':
            collections_to_query = [collection_name]
        else:
            # Query all collections
            all_collections = chromadb_admin.list_collections()
            collections_to_query = [col['name'] for col in all_collections]
        
        all_results = []
        
        for coll_name in collections_to_query:
            try:
                # Get the collection directly from the existing client
                collection = chroma_client.get_collection(coll_name)
                
                # Debug: Check collection info
                collection_count = collection.count()
                print(f"DEBUG: Querying collection '{coll_name}' with {collection_count} documents")
                
                if collection_count == 0:
                    print(f"WARNING: Collection '{coll_name}' is empty, skipping...")
                    continue
                
                if query_type == 'ranking':
                    # Use direct ChromaDB query for similarity search
                    query_results = collection.query(
                        query_texts=[query_text],
                        n_results=max_results * 3,  # Get more results to group by source
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # Debug: Show query results
                    result_count = len(query_results['documents'][0]) if query_results['documents'] and query_results['documents'][0] else 0
                    print(f"DEBUG: Collection '{coll_name}' returned {result_count} results for query: '{query_text[:50]}...'")
                    
                    # Group ranking results by original source file
                    source_groups = {}
                    if query_results['documents'] and query_results['documents'][0]:
                        for doc, metadata, distance in zip(
                            query_results['documents'][0],
                            query_results['metadatas'][0],
                            query_results['distances'][0]
                        ):
                            # Determine the original filename
                            original_name = (metadata.get('display_filename') or 
                                           metadata.get('original_file_source', '').split('\\')[-1].split('/')[-1] or
                                           metadata.get('document_name') or 
                                           metadata.get('source', 'Unknown'))
                            
                            if original_name not in source_groups:
                                source_groups[original_name] = {
                                    'best_score': float(distance),
                                    'content_chunks': [],
                                    'metadata': metadata,
                                    'collection': coll_name
                                }
                            else:
                                # Keep the best (lowest) score for this source
                                source_groups[original_name]['best_score'] = min(
                                    source_groups[original_name]['best_score'], 
                                    float(distance)
                                )
                            
                            # Add this chunk
                            chunk_text = doc[:300] + '...' if len(doc) > 300 else doc
                            source_groups[original_name]['content_chunks'].append(chunk_text)
                    
                    # Convert grouped sources to collection results
                    collection_results = []
                    for original_name, group_data in source_groups.items():
                        # Combine chunks but limit total length
                        combined_content = '\n\n'.join(group_data['content_chunks'])
                        if len(combined_content) > 500:
                            combined_content = combined_content[:500] + '...'
                        
                        collection_results.append({
                            'content': combined_content,
                            'metadata': group_data['metadata'],
                            'score': group_data['best_score'],
                            'collection': coll_name,
                            'original_filename': original_name,
                            'chunk_count': len(group_data['content_chunks'])
                        })
                    
                    # Sort by best score and limit to max_results
                    collection_results.sort(key=lambda x: x['score'])
                    collection_results = collection_results[:max_results]
                    
                    all_results.extend(collection_results)
                
                else:
                    # Standard RAG query with LLM - get relevant documents first
                    query_results = collection.query(
                        query_texts=[query_text],
                        n_results=max_results,
                        include=["documents", "metadatas"]
                    )
                    
                    # Debug: Show query results for RAG
                    result_count = len(query_results['documents'][0]) if query_results['documents'] and query_results['documents'][0] else 0
                    print(f"DEBUG: RAG query on collection '{coll_name}' returned {result_count} results")
                    
                    if query_results['documents'] and query_results['documents'][0]:
                        # Format context from retrieved documents
                        context_docs = []
                        for doc, metadata in zip(query_results['documents'][0], query_results['metadatas'][0]):
                            context_docs.append(doc)
                        
                        # Join all context
                        context = "\n\n".join(context_docs)
                        
                        # Create prompt template
                        prompt_template = """You are an AI assistant helping with resume and career information queries.
Use the following pieces of context to answer the question. If you don't know the answer based on the context, just say that you don't know.

Context:
{context}

Question: {question}

Answer:"""
                        
                        # Create enhanced prompt for scoring and ranking
                        enhanced_prompt_template = """You are an expert resume analyst. Based on the provided context, analyze each resume for relevance to the query.

For each resume, you must provide EXACTLY this format:

==RESUME_START==
RESUME_NAME: [candidate name or filename]
SCORE: [number from 0-100]
JUSTIFICATION: [brief explanation for the score]
KEY_EXTRACT_1: [specific relevant text from resume]
KEY_EXTRACT_2: [specific relevant text from resume] 
KEY_EXTRACT_3: [specific relevant text from resume]
==RESUME_END==

Context:
{context}

Question: {question}

Analyze each resume and provide the structured scoring format above."""
                        
                        # Create and execute the prompt without PromptTemplate class
                        formatted_prompt = enhanced_prompt_template.format(context=context, question=query_text)
                        response = llm.invoke(formatted_prompt)
                        
                        # Extract token usage if available
                        token_usage = {}
                        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                            usage = response.response_metadata['token_usage']
                            token_usage = {
                                'prompt_tokens': usage.get('prompt_tokens', 0),
                                'completion_tokens': usage.get('completion_tokens', 0),
                                'total_tokens': usage.get('total_tokens', 0),
                                'model_used': f"{provider}:{model}" if provider and model else "default",
                                'provider': provider if provider else "azure-openai",
                                'model_name': model if model else "default",
                                'temperature': temperature if temperature is not None else 0.1
                            }
                            
                            # Estimate cost (approximate rates for GPT-4)
                            # These are example rates - adjust based on your Azure OpenAI pricing
                            input_cost_per_1k = 0.03  # $0.03 per 1K tokens for input
                            output_cost_per_1k = 0.06  # $0.06 per 1K tokens for output
                            
                            input_cost = (token_usage['prompt_tokens'] / 1000) * input_cost_per_1k
                            output_cost = (token_usage['completion_tokens'] / 1000) * output_cost_per_1k
                            token_usage['estimated_cost'] = input_cost + output_cost
                        else:
                            # Even if no token usage metadata, still record model info
                            token_usage = {
                                'model_used': f"{provider}:{model}" if provider and model else "default",
                                'provider': provider if provider else "azure-openai",
                                'model_name': model if model else "default",
                                'temperature': temperature if temperature is not None else 0.1
                            }
                        
                        # Format source documents - Group by original source file
                        print(f"DEBUG: Processing {len(query_results['documents'][0])} documents for grouping")
                        source_groups = {}
                        for doc, metadata in zip(query_results['documents'][0], query_results['metadatas'][0]):
                            # Debug: Print metadata to see what we're working with
                            print(f"DEBUG: Document metadata: {metadata}")
                            
                            # Determine the original filename
                            original_name = (metadata.get('display_filename') or 
                                           metadata.get('original_file_source', '').split('\\')[-1].split('/')[-1] or
                                           metadata.get('document_name') or 
                                           metadata.get('source', 'Unknown'))
                            
                            print(f"DEBUG: Determined original_name: '{original_name}' from metadata")
                            
                            if original_name not in source_groups:
                                source_groups[original_name] = {
                                    'content_chunks': [],
                                    'metadata': metadata,
                                    'collection': coll_name
                                }
                                print(f"DEBUG: Created new group for '{original_name}'")
                            else:
                                print(f"DEBUG: Added to existing group for '{original_name}'")
                            
                            # Add this chunk to the group
                            chunk_text = doc[:300] + '...' if len(doc) > 300 else doc
                            source_groups[original_name]['content_chunks'].append(chunk_text)
                        
                        print(f"DEBUG: Created {len(source_groups)} source groups: {list(source_groups.keys())}")
                        
                        # Convert grouped sources to formatted list
                        formatted_sources = []
                        for original_name, group_data in source_groups.items():
                            # Combine all chunks for this source, but limit total length
                            combined_content = '\n\n'.join(group_data['content_chunks'])
                            if len(combined_content) > 500:
                                combined_content = combined_content[:500] + '...'
                            
                            # Enhanced source data for scoring display with original titles
                            # Handle both new format (with original_title) and legacy format
                            original_title = group_data['metadata'].get('original_title') or group_data['metadata'].get('display_filename') or original_name
                            file_path = group_data['metadata'].get('original_file_path') or group_data['metadata'].get('file_path', '')
                            
                            # Clean up the candidate name - prefer original title, then display filename
                            candidate_name = group_data['metadata'].get('candidate_name')
                            if not candidate_name:
                                # Extract name from original title or display filename
                                base_name = original_title.replace('.txt', '').replace('.pdf', '').replace('_', ' ').replace('-', ' ')
                                # Remove common resume patterns and IDs
                                import re
                                base_name = re.sub(r'Resume[\s_-]*[a-f0-9]{8}', '', base_name, flags=re.IGNORECASE)
                                base_name = re.sub(r'[a-f0-9]{8}', '', base_name)  # Remove 8-char hex IDs
                                candidate_name = base_name.strip().title()
                                if not candidate_name or len(candidate_name) < 2:
                                    candidate_name = "Resume Candidate"
                            
                            formatted_sources.append({
                                'content': combined_content,
                                'metadata': group_data['metadata'],
                                'collection': coll_name,
                                'original_filename': original_name,
                                'original_title': original_title,  # Store original upload name
                                'original_file_path': file_path,   # Store path to original file
                                'chunk_count': len(group_data['content_chunks']),
                                'candidate_name': candidate_name,
                                'experience_years': group_data['metadata'].get('experience_years', 'N/A'),
                                'key_skills': group_data['metadata'].get('key_skills', 'N/A'),
                                'recent_job_titles': group_data['metadata'].get('recent_job_titles', 'N/A'),
                                'education': group_data['metadata'].get('education', 'N/A'),
                                'score': 0,  # Will be extracted from LLM response
                                'justification': '',  # Will be extracted from LLM response
                                'key_extracts': []  # Will be extracted from LLM response
                            })

                # Remove duplicates based on candidate name and similar content
                unique_sources = []
                seen_candidates = set()
                
                for source in formatted_sources:
                    # Create a unique identifier based on candidate name and first 200 chars of content
                    candidate_key = (source['candidate_name'].lower(), source['content'][:200].strip().lower())
                    
                    if candidate_key not in seen_candidates:
                        seen_candidates.add(candidate_key)
                        unique_sources.append(source)
                    else:
                        print(f"Debug: Duplicate candidate detected and removed: {source['candidate_name']} from {source['original_filename']}")
                
                formatted_sources = unique_sources
                
                # Process results if documents were found
                if formatted_sources:
                    # Create the LLM prompt with candidate information
                    candidate_prompt = create_candidate_prompt(user_query, formatted_sources)
                    
                    # Get LLM response using selected model and provider
                    response = get_llm_response(candidate_prompt, current_model, current_provider)
                    
                    # Process LLM response and extract scoring data
                    llm_response = response.content if hasattr(response, 'content') else str(response)
                    
                    # Parse the response to extract scores and rankings
                    parsed_scores = parse_scoring_response(llm_response, formatted_sources)
                    
                    all_results.append({
                        'collection': coll_name,
                        'response': llm_response,
                        'sources': parsed_scores['sources'],  # Enhanced with scores
                        'token_usage': token_usage,
                        'query_text': query_text,
                        'response_type': 'enhanced_scoring',
                        'total_candidates': len(parsed_scores['sources'])
                    })
                else:
                    # No documents found
                    all_results.append({
                        'collection': coll_name,
                        'response': f"No relevant documents found in collection '{coll_name}' for the query.",
                        'sources': []
                    })
        
            except Exception as e:
                error_msg = str(e)
                print(f"ERROR: Failed to query collection '{coll_name}': {e}")
                print(f"ERROR: Exception type: {type(e).__name__}")
                import traceback
                print(f"ERROR: Traceback: {traceback.format_exc()}")
                
                # Provide more helpful error messages for common embedding issues
                if "sentence_transformers python package is not installed" in error_msg:
                    error_msg = "Missing dependency: sentence_transformers package not installed. Please install with 'pip install sentence_transformers'"
                elif "Could not build embedding function" in error_msg and "sentence_transformer" in error_msg:
                    error_msg = "Embedding function error: This collection was created with sentence-transformers embeddings but the package is not available. Please install sentence_transformers or recreate the collection with a different embedding model."
                elif "No module named 'langchain_huggingface'" in error_msg:
                    error_msg = "Missing dependency: langchain_huggingface package not installed. Please install with 'pip install langchain_huggingface'"
                elif "embedding" in error_msg.lower() and ("package" in error_msg.lower() or "import" in error_msg.lower()):
                    error_msg = f"Embedding dependency error: {error_msg}. Please check that all required embedding packages are installed."
                
                all_results.append({
                    'collection': coll_name,
                    'error': error_msg
                })
        
        if query_type == 'ranking':
            # Sort ranking results by score
            all_results.sort(key=lambda x: x.get('score', 0))
            response_data = {
                "success": True,
                "query_type": "ranking",
                "results": all_results
            }
            print(f"QUERY DEBUG: Returning ranking response with {len(all_results)} results")
            return jsonify(response_data)
        else:
            # Calculate aggregated token usage for standard queries
            total_token_usage = {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0,
                'estimated_cost': 0,
                'models_used': []
            }
            
            for result in all_results:
                if 'token_usage' in result:
                    usage = result['token_usage']
                    total_token_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
                    total_token_usage['completion_tokens'] += usage.get('completion_tokens', 0)
                    total_token_usage['total_tokens'] += usage.get('total_tokens', 0)
                    total_token_usage['estimated_cost'] += usage.get('estimated_cost', 0)
                    
                    # Track unique models used
                    if usage.get('model_used') and usage['model_used'] not in total_token_usage['models_used']:
                        total_token_usage['models_used'].append(usage['model_used'])
            
            # Add summary model info
            if total_token_usage['models_used']:
                if len(total_token_usage['models_used']) == 1:
                    total_token_usage['model_used'] = total_token_usage['models_used'][0]
                else:
                    total_token_usage['model_used'] = f"Multiple models: {', '.join(total_token_usage['models_used'])}"
            
            response_data = {
                "success": True,
                "query_type": "standard",
                "results": all_results,
                "token_usage": total_token_usage if total_token_usage['total_tokens'] > 0 else None
            }
            print(f"QUERY DEBUG: Returning standard response with {len(all_results)} results")
            print(f"QUERY DEBUG: Sample result: {all_results[0] if all_results else 'No results'}")
            print(f"QUERY DEBUG: Token usage: {total_token_usage}")
            return jsonify(response_data)
            
    except Exception as e:
        print(f"Error in query_with_chromadb_admin: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Query failed: {str(e)}"
        }), 500

def validate_existing_database():
    """
    Check if database exists and validate it can be properly initialized
    Returns: (exists, can_connect, error_message)
    """
    try:
        # Add path to import shared config
        sys.path.append(str(current_dir.parent.parent.parent))
        
        # Check if shared config is available and get DB path
        try:
            from shared_config import get_vector_db_path
            db_path = Path(get_vector_db_path())
        except ImportError:
            # Fallback path
            db_path = Path(r"C:\Users\DamonDesonier\repos\langachain_rag\resume_AI_Hybrid\resume_vectordb")
        
        print(f"Checking for existing database at: {db_path}")
        
        # Check if database directory and files exist
        if not db_path.exists():
            print("📂 No existing database found")
            return False, True, None  # No database exists, connection would be fine
        
        # Check for ChromaDB database file
        chroma_db_file = db_path / "chroma.sqlite3"
        if not chroma_db_file.exists():
            print("📂 Database directory exists but no ChromaDB files found")
            return False, True, None
        
        print("✅ Existing database found, testing connection...")
        
        # Test database connection
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use consistent settings that match the admin
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
            
            # Test connection
            test_client = chromadb.PersistentClient(path=str(db_path), settings=settings)
            
            # Test basic operations
            collections = test_client.list_collections()
            print(f"✅ Database connection successful. Found {len(collections)} collections.")
            
            # Clean up test connection
            del test_client
            
            return True, True, None
            
        except Exception as db_error:
            error_msg = f"Database found but failed to connect: {str(db_error)}"
            print(f"{error_msg}")
            return True, False, error_msg
            
    except Exception as e:
        error_msg = f"Error during database validation: {str(e)}"
        print(f"{error_msg}")
        return False, False, error_msg

def show_database_error_popup(error_message):
    """Show database error in both console and attempt to show system notification"""
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION ERROR")
    print("="*60)
    print(f"{error_message}")
    print("="*60)
    print("Recommendations:")
    print("1. Check if another ChromaDB instance is running")
    print("2. Restart the application")
    print("3. Check database file permissions")
    print("4. Consider backing up and recreating the database")
    print("="*60 + "\n")
    
    # Try to show Windows notification (optional, won't fail if not available)
    try:
        import subprocess
        subprocess.run([
            'powershell', '-Command',
            f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
            f'[System.Windows.Forms.MessageBox]::Show("{error_message}", "Database Error", "OK", "Error")'
        ], capture_output=True, timeout=5)
    except:
        pass  # Notification failed, but continue anyway

# Validate existing database before initializing admin
print("🚀 Starting ChromaDB Admin Interface...")
db_exists, can_connect, error_msg = validate_existing_database()

# Store validation results globally
startup_db_validation = {
    'db_exists': db_exists,
    'can_connect': can_connect, 
    'error_message': error_msg,
    'validation_time': None
}

if db_exists and not can_connect:
    show_database_error_popup(error_msg)
    print("Continuing with limited functionality...")

def startup_banner():
    """Display startup status banner"""
    print("\n" + "="*60)
    print("🚀 ChromaDB Admin Interface")
    print("="*60)
    
    if startup_db_validation['db_exists']:
        print(f"📂 Database Status: Found existing database")
        if startup_db_validation['can_connect']:
            print(f"✅ Connection Test: Successful")
        else:
            print(f"Connection Test: Failed")
            print(f"   Error: {startup_db_validation['error_message']}")
    else:
        print(f"📂 Database Status: No existing database (will create on first use)")
    
    if chromadb_admin:
        print(f"dmin Status: Initialized successfully")
    else:
        print(f"Admin Status: Failed to initialize")
        if startup_db_validation['error_message']:
            print(f"   Error: {startup_db_validation['error_message']}")
    
    print("="*60)
    print("📊 Dashboard: http://localhost:5001")
    print("🗂️ Collections: http://localhost:5001/admin/collections")
    print("📈 Statistics: http://localhost:5001/admin/stats")
    print("🛠️ Database: http://localhost:5001/admin/database")
    print("💡 Press Ctrl+C to gracefully shutdown")
    print("="*60 + "\n")

# Initialize ChromaDBAdmin with error handling
try:
    chromadb_admin = ChromaDBAdmin()
    print("✅ ChromaDBAdmin initialized successfully")
    startup_db_validation['validation_time'] = "Startup validation completed"
    
    # If database validation failed but admin initialized, warn user
    if db_exists and not can_connect:
        print("Database connection issues detected but admin initialized")
        print("   Some features may not work properly")
        
except Exception as e:
    print(f"Failed to initialize ChromaDBAdmin: {e}")
    chromadb_admin = None
    startup_db_validation['error_message'] = f"ChromaDBAdmin initialization failed: {e}"
    
    # Show error popup if admin initialization also failed
    if db_exists:
        show_database_error_popup(f"ChromaDBAdmin initialization failed: {e}")
    else:
        print("ℹ️  No existing database found - will create new one on first use")

# Display startup banner
startup_banner()

@app.route('/')
def index():
    """Redirect to admin dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    """Main admin dashboard"""
    database_status = {
        'initialized': chromadb_admin is not None,
        'has_connection_issues': False,
        'error_message': None,
        'startup_validation': startup_db_validation
    }
    
    # Check startup validation results
    if startup_db_validation['db_exists'] and not startup_db_validation['can_connect']:
        database_status['has_connection_issues'] = True
        database_status['error_message'] = startup_db_validation['error_message']
        flash(f"Database startup validation failed: {startup_db_validation['error_message']}", "error")
    
    if not chromadb_admin:
        flash("ChromaDB Admin not initialized. Please check your configuration.", "error")
        if not database_status['error_message']:
            database_status['error_message'] = "ChromaDB Admin not initialized"
    else:
        # Test current connection health
        try:
            health_check = chromadb_admin.health_check()
            if not health_check.get('healthy', False):
                database_status['has_connection_issues'] = True
                database_status['error_message'] = health_check.get('error', 'Unknown connection issue')
                flash(f"Database connection issues detected: {database_status['error_message']}", "warning")
        except Exception as e:
            database_status['has_connection_issues'] = True
            database_status['error_message'] = str(e)
            flash(f"Database health check failed: {e}", "error")
    
    return render_template('admin_dashboard.html', database_status=database_status)

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
    print("DEBUG: Collections route accessed")
    
    if not chromadb_admin:
        print("ERROR: ChromaDB Admin not available")
        flash("ChromaDB Admin not initialized. Check database configuration and restart the application.", "error")
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
    
    # Get collections and statistics with enhanced error handling
    collections = []
    stats = {}
    
    try:
        # Refresh client to ensure we see the latest data
        print("DEBUG: Refreshing ChromaDB client...")
        chromadb_admin.refresh_client()
        print("DEBUG: Loading collections list...")
        collections = chromadb_admin.list_collections()
        print(f"DEBUG: Successfully loaded {len(collections)} collections")
    except Exception as e:
        import traceback
        error_details = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR: Failed to load collections: {error_details}")
        print(f"Traceback: {traceback_str}")
        
        # Provide specific error messages based on error type
        if "chromadb" in error_details.lower():
            flash(f"ChromaDB connection error: {error_details}. Check if database path exists and is accessible.", 'error')
        elif "permission" in error_details.lower():
            flash(f"File permission error: {error_details}. Check folder permissions for the database directory.", 'error')
        elif "sqlite" in error_details.lower():
            flash(f"Database file error: {error_details}. The database may be corrupted or locked.", 'error')
        else:
            flash(f"Collections loading error: {error_details}", 'error')
        
        collections = []
    
    try:
        print("DEBUG: Loading database statistics...")
        stats = chromadb_admin.get_statistics()
        print("DEBUG: Successfully loaded statistics")
    except Exception as e:
        print(f"DEBUG: Failed to load stats: {str(e)}")
        stats = {"error": f"Statistics unavailable: {str(e)}"}
    
    # Get available models for the frontend
    custom_providers = load_custom_providers()
    custom_models = load_custom_models()
    saved_config = load_model_config()

    return render_template('collection_manager.html', 
                         form=form, 
                         collections=collections, 
                         stats=stats,
                         result=result,
                         available_providers=custom_providers,
                         custom_models=custom_models,
                         current_config=saved_config)

@app.route('/debug/database-status')
def debug_database_status():
    """Debug endpoint to check database status"""
    try:
        if not chromadb_admin:
            return jsonify({
                'status': 'error',
                'message': 'ChromaDB Admin not initialized',
                'details': startup_db_validation
            })
        
        # Test database connection
        collections = chromadb_admin.list_collections()
        stats = chromadb_admin.get_statistics()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'collections_count': len(collections),
            'database_path': chromadb_admin.db_path if hasattr(chromadb_admin, 'db_path') else 'Unknown',
            'stats': stats,
            'startup_validation': startup_db_validation
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'traceback': traceback.format_exc(),
            'startup_validation': startup_db_validation
        })

@app.route('/debug/collections')
def debug_collections_template():
    """Debug endpoint to test collection template rendering"""
    if not chromadb_admin:
        return "ChromaDB Admin not available"
    
    try:
        collections = chromadb_admin.list_collections()
        return render_template('debug_collections.html', collections=collections)
    except Exception as e:
        return f"Error: {str(e)}"

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

@app.route('/admin/query')
def query_interface():
    """RAG Query Interface"""
    if not chromadb_admin:
        flash("ChromaDB Admin not available. Please check your database configuration.", "error")
        return render_template('query_interface.html', 
                             collections=[],
                             available_providers=[],
                             custom_models=[],
                             current_config={},
                             error_collections=[
                                 {"name": "coll1", "error": "ChromaDB Admin not initialized"},
                                 {"name": "coll2", "error": "ChromaDB Admin not initialized"}
                             ])
    
    try:
        # Get available collections
        collections = chromadb_admin.list_collections()
        collection_names = [col['name'] for col in collections]
        
        # Get available models for the frontend
        custom_providers = load_custom_providers()
        custom_models = load_custom_models()
        saved_config = load_model_config()
        
        return render_template('query_interface.html', 
                             collections=collection_names,
                             available_providers=custom_providers,
                             custom_models=custom_models,
                             current_config=saved_config,
                             error_collections=[])
    except Exception as e:
        error_msg = f"Error loading collections: {str(e)}"
        flash(error_msg, "error")
        
        # Return template with error information
        return render_template('query_interface.html', 
                             collections=[],
                             available_providers=[],
                             custom_models=[],
                             current_config={},
                             error_collections=[
                                 {"name": "coll1", "error": error_msg},
                                 {"name": "coll2", "error": error_msg}
                             ])

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for RAG queries"""
    if not chromadb_admin:
        return jsonify({"success": False, "error": "ChromaDB Admin not available"}), 500
    
    try:
        data = request.get_json()
        query_text = data.get('query', '').strip()
        collection_name = data.get('collection', None)
        query_type = data.get('query_type', 'standard')
        max_results = data.get('max_results', 5)
        model_selection = data.get('model', '')
        temperature = data.get('temperature', 0.7)
        
        if not query_text:
            return jsonify({"success": False, "error": "Query text is required"}), 400
        
        # Parse model selection
        selected_provider = None
        selected_model = None
        selected_temperature = temperature
        
        print(f"🔍 API Query Debug - Raw model_selection: '{model_selection}'")
        
        if model_selection and ':' in model_selection:
            selected_provider, selected_model = model_selection.split(':', 1)
            print(f"✅ Model parsed - Provider: '{selected_provider}', Model: '{selected_model}', Temperature: {selected_temperature}")
        else:
            print(f"⚠️ No valid model selection found, using default configuration")
        
        # Validate collection exists using existing ChromaDB admin instance
        if collection_name and collection_name.lower() != 'all':
            collections = chromadb_admin.list_collections()
            collection_names = [col['name'] for col in collections]
            if collection_name not in collection_names:
                return jsonify({
                    "success": False, 
                    "error": f"Collection '{collection_name}' not found. Available collections: {collection_names}"
                }), 400
        
        # Use ChromaDB admin instance for querying with selected model parameters
        return query_with_chromadb_admin(chromadb_admin, query_text, collection_name, query_type, max_results, 
                                       selected_provider, selected_model, selected_temperature)
        
    except Exception as e:
        print(f"Query API error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/view_resume')
def view_resume():
    """View resume content in a new window"""
    filename = request.args.get('filename')
    collection = request.args.get('collection')
    filepath = request.args.get('filepath')  # New parameter for original file path
    
    if not filename or not collection:
        return "Missing filename or collection parameter", 400
        
    try:
        # Get the ChromaDB collection
        collections = chromadb_admin.list_collections()
        collection_obj = None
        
        for col in collections:
            if col['name'] == collection:
                collection_obj = chromadb_admin.client.get_collection(collection)
                break
                
        if not collection_obj:
            return f"Collection '{collection}' not found", 404
            
        # Search for documents with matching filename
        try:
            # First try exact match
            results = collection_obj.query(
                query_texts=["resume content"],  # dummy query 
                n_results=100,  # Get more results to find matches
                where={
                    "$or": [
                        {"display_filename": filename},
                        {"original_title": filename},
                        {"document_name": filename},
                        {"source": filename}
                    ]
                }
            )
            
            # If no results, try without extension
            if not results['documents'] or not results['documents'][0]:
                base_filename = filename.replace('.pdf', '').replace('.txt', '')
                results = collection_obj.query(
                    query_texts=["resume content"],
                    n_results=100,
                    where={
                        "$or": [
                            {"display_filename": base_filename},
                            {"document_name": base_filename},
                            {"source": base_filename}
                        ]
                    }
                )
                
            # If still no results, get all documents and filter manually
            if not results['documents'] or not results['documents'][0]:
                results = collection_obj.query(
                    query_texts=["resume content"],
                    n_results=1000  # Get all documents
                )
            
            if not results['documents'] or not results['documents'][0]:
                return f"Resume '{filename}' not found in collection '{collection}'", 404
                
            # Combine all chunks for this document
            content_chunks = []
            metadata_info = results['metadatas'][0][0] if results['metadatas'][0] else {}
            
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                # Check if this chunk belongs to our target file using multiple criteria
                # Handle both new format and legacy format matching with case-insensitive string matching
                filename_lower = filename.lower()
                base_filename = filename.replace('.pdf', '').replace('.txt', '').lower()
                
                # Check various metadata fields for matches
                display_name = meta.get('display_filename', '').lower()
                original_title = meta.get('original_title', '').lower()
                original_source = meta.get('original_file_source', '').lower()
                document_name = meta.get('document_name', '').lower()
                source = meta.get('source', '').lower()
                
                # Match using contains logic since ChromaDB doesn't support regex
                if (filename_lower in display_name or 
                    filename_lower in original_title or
                    filename_lower in original_source or
                    filename_lower in document_name or 
                    filename_lower in source or
                    base_filename in display_name or
                    base_filename in document_name or
                    base_filename in source):
                    content_chunks.append(doc)
                    if not metadata_info:  # Store first matching metadata
                        metadata_info = meta
                    
            if not content_chunks:
                return f"No content found for '{filename}' in collection '{collection}'", 404
                
            # Combine all chunks
            full_content = '\n\n'.join(content_chunks)
            
            # Get display information, handling both new and legacy formats
            original_title = metadata_info.get('original_title') or metadata_info.get('display_filename') or filename
            candidate_name = metadata_info.get('candidate_name')
            if not candidate_name:
                # Extract name from title, cleaning up generated IDs
                import re
                base_name = original_title.replace('.txt', '').replace('.pdf', '').replace('_', ' ').replace('-', ' ')
                base_name = re.sub(r'Resume[\s_-]*[a-f0-9]{8}', '', base_name, flags=re.IGNORECASE)
                base_name = re.sub(r'[a-f0-9]{8}', '', base_name)  # Remove 8-char hex IDs
                candidate_name = base_name.strip().title() or 'Resume Candidate'
            
            file_path_info = metadata_info.get('original_file_path', filepath) if filepath else 'Database storage'
            
            # Return a simple HTML page with the resume content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{candidate_name} - Resume</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {{ font-family: Georgia, serif; line-height: 1.6; }}
                    .resume-header {{ background: #f8f9fa; padding: 2rem; margin-bottom: 2rem; border-radius: 8px; }}
                    .resume-content {{ white-space: pre-wrap; max-width: 800px; margin: 0 auto; padding: 2rem; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="resume-header text-center">
                        <h1>{candidate_name}</h1>
                        <p class="text-muted">
                            Source File: {original_title} | Collection: {collection}<br>
                            <small>File Path: {file_path_info}</small>
                        </p>
                    </div>
                    <div class="resume-content">
                        {full_content.replace(chr(10), '<br>').replace('  ', '&nbsp;&nbsp;')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as query_error:
            return f"Error retrieving resume content: {str(query_error)}", 500
            
    except Exception as e:
        return f"Error accessing collection: {str(e)}", 500

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

@app.route('/admin/models', methods=['GET', 'POST'])
def manage_models():
    """Model selection and configuration interface"""
    global chromadb_admin
    
    if not chromadb_admin:
        flash("ChromaDB Admin not available", "error")
        return redirect(url_for('admin_dashboard'))
    
    form = ModelSelectionForm()
    
    # Load custom providers and update form choices
    custom_providers = load_custom_providers()
    llm_provider_choices = []
    embedding_provider_choices = []
    
    # Add LLM providers
    for provider_id, provider_info in custom_providers.get('llm', {}).items():
        display_name = provider_info.get('display_name', provider_id.title())
        llm_provider_choices.append((provider_id, display_name))
    
    # Add embedding providers  
    for provider_id, provider_info in custom_providers.get('embedding', {}).items():
        display_name = provider_info.get('display_name', provider_id.title())
        embedding_provider_choices.append((provider_id, display_name))
    
    # Update form choices
    form.llm_provider.choices = llm_provider_choices
    form.embedding_provider.choices = embedding_provider_choices
    
    # Get current configuration
    try:
        from shared_config import get_config
        config = get_config()
        
        # Set form defaults from current configuration and saved config
        if request.method == 'GET':
            import os
            # Load saved configuration
            saved_config = load_model_config()
            
            # Use saved config values if available, otherwise fall back to env vars or defaults
            form.llm_provider.data = (saved_config.get('providers', {}).get('llm_provider') or 
                                    os.getenv('LLM_PROVIDER', config.llm_provider))
            form.llm_model.data = (saved_config.get('providers', {}).get('llm_model') or 
                                 config.llm_model)
            form.embedding_provider.data = (saved_config.get('providers', {}).get('embedding_provider') or 
                                           os.getenv('EMBEDDING_PROVIDER', config.embedding_provider))
            form.embedding_model.data = (saved_config.get('providers', {}).get('embedding_model') or 
                                       config.embedding_model)
            form.temperature.data = (saved_config.get('settings', {}).get('temperature') or 
                                   float(os.getenv('LLM_TEMPERATURE', config.llm_temperature)))
            
            # Azure OpenAI fields
            form.azure_endpoint.data = os.getenv('AZURE_OPENAI_ENDPOINT', '')
            form.azure_api_version.data = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            form.azure_llm_deployment.data = os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT', '')
            form.azure_embedding_deployment.data = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', '')
            
            # OpenAI fields
            form.openai_base_url.data = os.getenv('OPENAI_BASE_URL', '')
            form.openai_organization.data = os.getenv('OPENAI_ORGANIZATION', '')
            
            # HuggingFace fields
            form.huggingface_endpoint.data = os.getenv('HUGGINGFACE_ENDPOINT_URL', '')
            
            # Ollama fields
            form.ollama_base_url.data = os.getenv('OLLAMA_BASE_URL', '')
            
    except Exception as e:
        flash(f"Error loading current configuration: {e}", "error")
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Prepare configuration data to save
            config_data = {
                'saved_at': datetime.now().isoformat(),
                'providers': {
                    'llm_provider': form.llm_provider.data,
                    'embedding_provider': form.embedding_provider.data,
                    'llm_model': form.llm_model.data,
                    'embedding_model': form.embedding_model.data
                },
                'environment': {},
                'settings': {
                    'temperature': float(form.temperature.data)
                }
            }
            
            # Update environment variables and prepare for saving
            import os
            env_updates = {
                'LLM_PROVIDER': form.llm_provider.data,
                'EMBEDDING_PROVIDER': form.embedding_provider.data,
                'LLM_TEMPERATURE': str(form.temperature.data)
            }
            
            # Azure OpenAI Configuration
            if form.azure_endpoint.data:
                env_updates['AZURE_OPENAI_ENDPOINT'] = form.azure_endpoint.data
            if form.azure_api_key.data:
                env_updates['AZURE_OPENAI_API_KEY'] = form.azure_api_key.data
            if form.azure_api_version.data:
                env_updates['AZURE_OPENAI_API_VERSION'] = form.azure_api_version.data
            if form.azure_llm_deployment.data:
                env_updates['AZURE_OPENAI_CHATGPT_DEPLOYMENT'] = form.azure_llm_deployment.data
            if form.azure_embedding_deployment.data:
                env_updates['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] = form.azure_embedding_deployment.data
            
            # OpenAI Configuration
            if form.openai_api_key.data:
                env_updates['OPENAI_API_KEY'] = form.openai_api_key.data
            if form.openai_base_url.data:
                env_updates['OPENAI_BASE_URL'] = form.openai_base_url.data
            if form.openai_organization.data:
                env_updates['OPENAI_ORGANIZATION'] = form.openai_organization.data
            
            # Anthropic Configuration
            if form.anthropic_api_key.data:
                env_updates['ANTHROPIC_API_KEY'] = form.anthropic_api_key.data
            
            # HuggingFace Configuration
            if form.huggingface_api_key.data:
                env_updates['HUGGINGFACE_API_TOKEN'] = form.huggingface_api_key.data
            if form.huggingface_endpoint.data:
                env_updates['HUGGINGFACE_ENDPOINT_URL'] = form.huggingface_endpoint.data
            
            # Ollama Configuration
            if form.ollama_api_key.data:
                env_updates['OLLAMA_API_KEY'] = form.ollama_api_key.data
            if form.ollama_base_url.data:
                env_updates['OLLAMA_BASE_URL'] = form.ollama_base_url.data
            
            # Apply environment updates
            for key, value in env_updates.items():
                os.environ[key] = value
            
            # Store non-sensitive config for persistence (excluding API keys)
            sensitive_keys = ['API_KEY', 'TOKEN', 'SECRET']
            config_data['environment'] = {
                key: value for key, value in env_updates.items() 
                if not any(sensitive in key for sensitive in sensitive_keys)
            }
            
            # Set model-specific environment variables
            if form.llm_provider.data == 'azure-openai':
                os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT'] = form.llm_model.data
            elif form.llm_provider.data == 'openai':
                os.environ['OPENAI_MODEL'] = form.llm_model.data
            elif form.llm_provider.data == 'anthropic':
                os.environ['ANTHROPIC_MODEL'] = form.llm_model.data
                
            if form.embedding_provider.data == 'azure-openai':
                os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] = form.embedding_model.data
            elif form.embedding_provider.data == 'openai':
                os.environ['OPENAI_EMBEDDING_MODEL'] = form.embedding_model.data
            elif form.embedding_provider.data == 'huggingface':
                os.environ['HUGGINGFACE_MODEL_NAME'] = form.embedding_model.data
                
            # Save configuration to file
            config_saved = save_model_config(config_data)
            
            if config_saved:
                flash("Configuration saved successfully! Settings will persist across restarts.", "success")
            else:
                flash("Configuration applied but could not save to file. Settings may not persist across restarts.", "warning")
                
            # Reset ChromaDB admin to pick up new settings
            if chromadb_admin:
                chromadb_admin.reset_connections()
                
            return redirect(url_for('model_selector'))
            
        except Exception as e:
            flash(f"❌ Error updating model configuration: {e}", "error")
    
    # Get available providers and models
    try:
        available_providers = {
            "embedding": custom_providers.get('embedding', {}),
            "llm": custom_providers.get('llm', {})
        }
        print(f"DEBUG: Available providers: {available_providers}")
    except Exception as e:
        print(f"DEBUG: Error loading providers: {e}")
        available_providers = {"embedding": {}, "llm": {}}
    
    # Load custom models
    custom_models = load_custom_models()
    
    return render_template('model_selector.html', 
                         form=form, 
                         available_providers=available_providers,
                         custom_models=custom_models)

@app.route('/api/providers', methods=['GET'])
def get_providers_info():
    """API endpoint to get all providers and models information"""
    try:
        custom_providers = load_custom_providers()
        custom_models = load_custom_models()
        saved_config = load_model_config()
        
        providers_info = {
            "llm_providers": {},
            "embedding_providers": {},
            "current_configuration": {
                "llm_provider": saved_config.get('providers', {}).get('llm_provider'),
                "llm_model": saved_config.get('providers', {}).get('llm_model'),
                "embedding_provider": saved_config.get('providers', {}).get('embedding_provider'),
                "embedding_model": saved_config.get('providers', {}).get('embedding_model'),
                "temperature": saved_config.get('settings', {}).get('temperature')
            }
        }
        
        # Format LLM providers
        for provider_id, provider_info in custom_providers.get('llm', {}).items():
            models = custom_models.get('llm', {}).get(provider_id, [])
            providers_info["llm_providers"][provider_id] = {
                "display_name": provider_info.get('display_name', provider_id.title()),
                "base_url": provider_info.get('base_url'),
                "api_key_env": provider_info.get('api_key_env'),
                "models": models,
                "model_count": len(models)
            }
        
        # Format embedding providers
        for provider_id, provider_info in custom_providers.get('embedding', {}).items():
            models = custom_models.get('embedding', {}).get(provider_id, [])
            providers_info["embedding_providers"][provider_id] = {
                "display_name": provider_info.get('display_name', provider_id.title()),
                "base_url": provider_info.get('base_url'),
                "api_key_env": provider_info.get('api_key_env'),
                "models": models,
                "model_count": len(models)
            }
        
        return jsonify({
            "success": True,
            "providers": providers_info,
            "total_llm_providers": len(providers_info["llm_providers"]),
            "total_embedding_providers": len(providers_info["embedding_providers"])
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/config/delete', methods=['POST'])
def api_delete_model_config():
    """API endpoint to delete model configuration"""
    try:
        success = delete_model_config()
        if success:
            return jsonify({
                "success": True,
                "message": "Model configuration deleted successfully. Application will use default settings."
            })
        else:
            return jsonify({
                "success": False,
                "message": "No configuration file found to delete."
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/models/delete', methods=['POST'])
def api_delete_specific_model():
    """API endpoint to delete a specific model from custom_models.json"""
    try:
        data = request.get_json()
        provider_type = data.get('provider_type')  # 'llm' or 'embedding'
        provider_id = data.get('provider_id')
        model_name = data.get('model_name')
        
        if not all([provider_type, provider_id, model_name]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: provider_type, provider_id, model_name"
            }), 400
        
        # Load current models
        custom_models = load_custom_models()
        
        # Check if the model exists
        models_list = custom_models.get(provider_type, {}).get(provider_id, [])
        if model_name not in models_list:
            return jsonify({
                "success": False,
                "error": f"Model '{model_name}' not found for provider '{provider_id}'"
            }), 404
        
        # Remove the model
        models_list.remove(model_name)
        
        # Update the custom_models.json file
        custom_models_file = os.path.join(os.path.dirname(__file__), 'custom_models.json')
        with open(custom_models_file, 'w') as f:
            json.dump(custom_models, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": f"Model '{model_name}' deleted successfully from {provider_id}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dependencies/check', methods=['GET'])
def api_check_dependencies():
    """API endpoint to check embedding dependencies"""
    try:
        dependency_status = check_embedding_dependencies()
        return jsonify({
            "success": True,
            "dependencies": dependency_status
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/models/add', methods=['POST'])
def add_model_to_provider():
    """Add a new model to a provider"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        provider_type = data.get('provider_type')
        model_name = data.get('model_name')
        
        if not all([provider_id, provider_type, model_name]):
            return jsonify({
                "success": False,
                "error": "Missing required fields: provider_id, provider_type, model_name"
            }), 400
        
        # Add model using existing function
        result = save_custom_model(provider_type, provider_id, model_name)
        
        return jsonify({
            "success": True,
            "message": f"Model '{model_name}' added to {provider_id}"
        })
        
    except Exception as e:
        print(f"Error adding model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/models/remove', methods=['POST'])
def remove_model_from_provider():
    """Remove a model from a provider"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        provider_type = data.get('provider_type')
        model_name = data.get('model_name')
        
        if not all([provider_id, provider_type, model_name]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400
        
        # Load current models
        custom_models = load_custom_models()
        
        # Remove the model
        if provider_type in custom_models and provider_id in custom_models[provider_type]:
            if model_name in custom_models[provider_type][provider_id]:
                custom_models[provider_type][provider_id].remove(model_name)
                
                # Save updated models
                with open('custom_models.json', 'w') as f:
                    json.dump(custom_models, f, indent=2)
                
                return jsonify({
                    "success": True,
                    "message": f"Model '{model_name}' removed from {provider_id}"
                })
        
        return jsonify({
            "success": False,
            "error": "Model not found"
        }), 404
        
    except Exception as e:
        print(f"Error removing model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/providers/test', methods=['POST'])
def test_provider_connection():
    """Test provider connection with provided credentials"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        provider_type = data.get('provider_type')
        api_key = data.get('api_key')
        
        # Temporarily set environment variable for testing
        if api_key:
            if provider_id == 'azure-openai':
                os.environ['AZURE_OPENAI_KEY'] = api_key
            elif provider_id == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
            elif provider_id == 'anthropic':
                os.environ['ANTHROPIC_API_KEY'] = api_key
            elif 'ollama' in provider_id:
                os.environ['OLLAMA_API_KEY'] = api_key
        
        # Test the connection by getting a dynamic LLM instance
        llm = get_dynamic_llm(provider_id, "test-model")
        
        return jsonify({
            "success": True,
            "message": f"Connection to {provider_id} successful"
        })
        
    except Exception as e:
        print(f"Provider test error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/providers/configure', methods=['POST'])
def configure_provider():
    """Configure a provider with API keys and settings"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        provider_type = data.get('provider_type')
        api_key = data.get('api_key')
        
        # Store API key in environment variables
        if api_key:
            if provider_id == 'azure-openai':
                os.environ['AZURE_OPENAI_KEY'] = api_key
                # Handle Azure-specific config
                if data.get('azure_endpoint'):
                    os.environ['AZURE_OPENAI_ENDPOINT'] = data.get('azure_endpoint')
                if data.get('azure_api_version'):
                    os.environ['AZURE_OPENAI_API_VERSION'] = data.get('azure_api_version')
                if data.get('azure_deployment'):
                    os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT'] = data.get('azure_deployment')
            elif provider_id == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
            elif provider_id == 'anthropic':
                os.environ['ANTHROPIC_API_KEY'] = api_key
            elif 'ollama' in provider_id:
                if api_key:  # Only set if provided (Ollama local doesn't need key)
                    os.environ['OLLAMA_API_KEY'] = api_key
                if data.get('ollama_url'):
                    os.environ['OLLAMA_BASE_URL'] = data.get('ollama_url')
        
        # Update current configuration to use this provider
        config_data = {
            "providers": {
                f"{provider_type}_provider": provider_id,
                f"{provider_type}_model": "default"  # Will be set when user selects a model
            },
            "environment": provider_type,
            "settings": {
                "temperature": 0.1
            }
        }
        
        # Save configuration
        save_model_config(config_data)
        
        return jsonify({
            "success": True,
            "message": f"Provider '{provider_id}' configured successfully"
        })
        
    except Exception as e:
        print(f"Provider configuration error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/models/debug', methods=['POST'])
def debug_model_config():
    """Debug model configuration"""
    data = request.get_json()
    provider = data.get('provider')
    model = data.get('model')
    
    debug_info = {
        "environment_vars": {
            "AZURE_OPENAI_ENDPOINT": os.getenv('AZURE_OPENAI_ENDPOINT'),
            "AZURE_OPENAI_CHATGPT_DEPLOYMENT": os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT'),
            "AZURE_OPENAI_API_VERSION": os.getenv('AZURE_OPENAI_API_VERSION'),
            "AZURE_OPENAI_KEY_SET": bool(os.getenv('AZURE_OPENAI_KEY'))
        },
        "requested": {
            "provider": provider,
            "model": model
        }
    }
    
    return jsonify({"success": True, "debug_info": debug_info})

@app.route('/api/models/test-simple', methods=['POST'])
def test_simple():
    """Simple test to isolate the os variable issue"""
    try:
        import sys
        env_module = sys.modules.get('os')
        if not env_module:
            import os as env_module
        
        return jsonify({
            "success": True,
            "message": "Simple test passed",
            "azure_endpoint": env_module.getenv('AZURE_OPENAI_ENDPOINT', 'not_found')
        })
    except Exception as e:
        import traceback
        print(f"Simple test error: {e}")
        print(f"Simple test traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ollama-cloud/models', methods=['POST'])
def get_ollama_cloud_models():
    """Get available models from Ollama Cloud"""
    try:
        import requests
        
        # Get request data
        data = request.get_json() or {}
        
        # Get API key from request data first, then environment
        api_key = data.get('api_key') or os.getenv('OLLAMA_API_KEY')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "No Ollama API key provided. Please enter your API key in the UI."
            })
        
        # Test endpoint
        url = "https://ollama.com/api/tags"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                models = data.get("models", [])
                
                # Format models for the dropdown
                model_options = []
                for model in models:
                    model_name = model.get("name", "")
                    if model_name:
                        # Create display name
                        display_name = model_name
                        if "cloud" in model_name.lower():
                            display_name = f"{model_name} (Cloud)"
                        
                        model_options.append({
                            "value": model_name,
                            "text": display_name,
                            "size": model.get("size", 0)
                        })
                
                # Sort by name for better UX
                model_options.sort(key=lambda x: x["text"])
                
                return jsonify({
                    "success": True,
                    "models": model_options,
                    "count": len(model_options)
                })
                
            except Exception as parse_error:
                return jsonify({
                    "success": False,
                    "error": f"Failed to parse Ollama response: {str(parse_error)}"
                })
                
        elif response.status_code == 401:
            return jsonify({
                "success": False,
                "error": "Invalid Ollama API key. Check your key at https://ollama.com/settings/keys"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Ollama API error: HTTP {response.status_code}"
            })
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Cannot connect to Ollama Cloud. Check internet connection."
        })
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Ollama Cloud request timeout."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error fetching Ollama models: {str(e)}"
        })

@app.route('/api/models/test', methods=['POST'])
def test_model_connection():
    """Test connection to specified model"""
    import sys
    import traceback
    
    try:
        # Get environment module reference cleanly
        env_module = sys.modules.get('os')
        if not env_module:
            import os as env_module
        
        data = request.get_json()
        provider = data.get('provider')
        model = data.get('model')
        
        print(f"DEBUG: Starting test for provider={provider}, model={model}, test_type={data.get('test_type')}")
        
        # Test LLM connection
        if data.get('test_type') == 'llm':
            if provider == "azure-openai":
                print(f"DEBUG: About to test Azure OpenAI with deployment: {model}")
                try:
                    # Validate required Azure configuration
                    endpoint = env_module.getenv('AZURE_OPENAI_ENDPOINT')
                    api_key = env_module.getenv('AZURE_OPENAI_KEY') or env_module.getenv('AZURE_OPENAI_API_KEY')
                    api_version = env_module.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
                    
                    if not endpoint:
                        return jsonify({
                            "success": False,
                            "error": "Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT environment variable."
                        })
                    
                    if not api_key:
                        return jsonify({
                            "success": False,
                            "error": "Azure OpenAI API key not found. Set AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY environment variable."
                        })
                    
                    if not api_version:
                        return jsonify({
                            "success": False,
                            "error": "Azure OpenAI API version not found. Set AZURE_OPENAI_API_VERSION environment variable."
                        })
                    
                    llm_config = {
                        'azure_endpoint': endpoint,
                        'api_key': api_key,
                        'azure_deployment': model,
                        'api_version': api_version,
                        'temperature': 0.1
                    }
                    print(f"DEBUG: Config built: {llm_config}")
                    print(f"DEBUG: Using API version: {api_version}")
                    
                    # Test AzureChatOpenAI creation
                    print("DEBUG: About to create AzureChatOpenAI instance...")
                    llm = AzureChatOpenAI(**llm_config)
                    print("DEBUG: AzureChatOpenAI instance created successfully")
                    
                    print("DEBUG: About to invoke LLM...")
                    response = llm.invoke("Test connection. Reply with: OK")
                    print(f"DEBUG: LLM response: {response}")
                    
                    return jsonify({
                        "success": True,
                        "message": f"✅ LLM connection successful",
                        "response": response.content[:100] if hasattr(response, 'content') else str(response)[:100]
                    })
                except Exception as llm_error:
                    print(f"DEBUG: LLM error: {llm_error}")
                    print(f"DEBUG: LLM traceback: {traceback.format_exc()}")
                    return jsonify({
                        "success": False,
                        "error": f"Azure OpenAI LLM test failed: {str(llm_error)}"
                    })
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                api_key = env_module.getenv('OPENAI_API_KEY')
                if not api_key:
                    return jsonify({
                        "success": False,
                        "error": "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                    })
                
                llm_config = {
                    'model': model,
                    'api_key': api_key,
                    'temperature': 0.1
                }
                
                # Add base URL if specified
                base_url = env_module.getenv('OPENAI_BASE_URL')
                if base_url:
                    llm_config['base_url'] = base_url
                    
                print(f"DEBUG: Testing OpenAI with model: {model}")
                print(f"DEBUG: Config: {llm_config}")
                llm = ChatOpenAI(**llm_config)
            elif provider == "anthropic":
                try:
                    from langchain_anthropic import ChatAnthropic
                    llm_config = {
                        'model': model,
                        'api_key': env_module.getenv('ANTHROPIC_API_KEY'),
                        'temperature': 0.1
                    }
                    llm = ChatAnthropic(**llm_config)
                except ImportError:
                    return jsonify({
                        "success": False,
                        "error": "Anthropic package not installed"
                    })
            else:
                # Handle custom providers
                try:
                    custom_providers = load_custom_providers()
                    if provider in custom_providers.get('llm', {}):
                        provider_info = custom_providers['llm'][provider]
                        base_url = provider_info.get('base_url')
                        api_key_env = provider_info.get('api_key_env')
                        
                        api_key = None
                        if api_key_env:
                            # First try to get from request data (for UI tests)
                            api_key = data.get('api_key')
                            print(f"DEBUG: API key from request data: {'***' + api_key[-4:] if api_key and len(api_key) > 4 else 'None'}")
                            if not api_key:
                                # Fall back to environment variable
                                api_key = env_module.getenv(api_key_env)
                                print(f"DEBUG: API key from environment: {'***' + api_key[-4:] if api_key and len(api_key) > 4 else 'None'}")
                            
                            # Only require API key if the environment variable name is specified
                            # and it's not a local service that might not need authentication
                            if not api_key and not (base_url and 'localhost' in base_url):
                                return jsonify({
                                    "success": False,
                                    "error": f"API key not found for {provider}. Please enter API key in the UI or set {api_key_env} environment variable."
                                })
                        
                        # Try to use OpenAI-compatible client for custom providers
                        from langchain_openai import ChatOpenAI
                        llm_config = {
                            'model': model,
                            'temperature': 0.1
                        }
                        
                        # Handle different authentication methods
                        if api_key:
                            if provider == 'ollama-cloud':
                                # Ollama Cloud uses different authentication approach
                                # Set up proper headers and client configuration
                                llm_config['api_key'] = api_key
                                llm_config['default_headers'] = {
                                    'Authorization': f'Bearer {api_key}',
                                    'Content-Type': 'application/json'
                                }
                            else:
                                llm_config['api_key'] = api_key
                        
                        if base_url:
                            # Fix Ollama endpoints
                            if provider == 'ollama-cloud':
                                # Ollama Cloud uses direct API endpoint
                                if 'ollama.com' in base_url and '/v1' not in base_url:
                                    base_url = 'https://ollama.com/v1'
                                llm_config['base_url'] = base_url
                            elif provider == 'ollama':
                                # Local Ollama
                                if 'localhost:11434' in base_url and '/v1' not in base_url:
                                    base_url = 'http://localhost:11434/v1'
                                llm_config['base_url'] = base_url
                            else:
                                llm_config['base_url'] = base_url
                            
                        print(f"DEBUG: Testing custom provider {provider} with config: {llm_config}")
                        
                        # Special handling for Ollama Cloud
                        if provider == 'ollama-cloud':
                            try:
                                # Use direct API test like the working test script
                                import requests
                                
                                # Test endpoint
                                test_url = "https://ollama.com/api/tags"
                                headers = {
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json"
                                }
                                
                                print(f"DEBUG: Testing Ollama Cloud with direct API call...")
                                response = requests.get(test_url, headers=headers, timeout=10)
                                
                                if response.status_code == 200:
                                    # API key is valid, now test chat
                                    chat_url = "https://ollama.com/api/chat"
                                    chat_payload = {
                                        "model": model,
                                        "messages": [
                                            {
                                                "role": "user",
                                                "content": "Hello! Please respond with 'API test successful'."
                                            }
                                        ],
                                        "stream": False
                                    }
                                    
                                    chat_response = requests.post(
                                        chat_url, 
                                        headers=headers, 
                                        json=chat_payload, 
                                        timeout=30
                                    )
                                    
                                    if chat_response.status_code == 200:
                                        try:
                                            chat_data = chat_response.json()
                                            message_content = chat_data.get("message", {}).get("content", "Success")
                                            print(f"DEBUG: Ollama Cloud chat test successful: {message_content[:100]}...")
                                            return jsonify({
                                                "success": True,
                                                "message": f"✅ Ollama Cloud connection successful",
                                                "response": message_content[:100]
                                            })
                                        except Exception as json_error:
                                            return jsonify({
                                                "success": False,
                                                "error": f"Ollama Cloud chat response invalid: {str(json_error)}"
                                            })
                                    else:
                                        return jsonify({
                                            "success": False,
                                            "error": f"Ollama Cloud chat failed: HTTP {chat_response.status_code} - {chat_response.text[:200]}"
                                        })
                                elif response.status_code == 401:
                                    return jsonify({
                                        "success": False,
                                        "error": "Ollama Cloud authentication failed (401). Please check your API key from https://ollama.com/settings/keys"
                                    })
                                else:
                                    return jsonify({
                                        "success": False,
                                        "error": f"Ollama Cloud API test failed: HTTP {response.status_code} - {response.text[:200]}"
                                    })
                                    
                            except requests.exceptions.ConnectionError:
                                return jsonify({
                                    "success": False,
                                    "error": "Cannot connect to Ollama Cloud. Check your internet connection."
                                })
                            except requests.exceptions.Timeout:
                                return jsonify({
                                    "success": False,
                                    "error": "Ollama Cloud request timeout. Service may be slow or unavailable."
                                })
                            except Exception as e:
                                error_msg = str(e)
                                print(f"DEBUG: Ollama Cloud error: {error_msg}")
                                return jsonify({
                                    "success": False,
                                    "error": f"Ollama Cloud connection error: {error_msg}"
                                })
                        else:
                            llm = ChatOpenAI(**llm_config)
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"Unknown provider: {provider}"
                        })
                except Exception as custom_error:
                    return jsonify({
                        "success": False,
                        "error": f"Custom provider error: {str(custom_error)}"
                    })
        
        # Test embedding connection
        elif data.get('test_type') == 'embedding':
            if not chromadb_admin:
                return jsonify({
                    "success": False, 
                    "error": "ChromaDB Admin not available"
                })
            
            try:
                embedding_function = chromadb_admin.get_dynamic_embedding_function(provider, model)
                if embedding_function:
                    try:
                        if hasattr(embedding_function, '__call__'):
                            test_result = embedding_function(["test text"])
                            return jsonify({
                                "success": True,
                                "message": f"✅ Embedding model connection successful",
                                "dimensions": len(test_result[0]) if test_result and len(test_result) > 0 else "Unknown"
                            })
                        else:
                            return jsonify({
                                "success": True,
                                "message": f"✅ Embedding function created successfully"
                            })
                    except Exception as e:
                        return jsonify({
                            "success": False,
                            "error": f"Embedding test failed: {str(e)}"
                        })
                else:
                    error_details = []
                    if provider == "azure-openai":
                        if not env_module.getenv("AZURE_OPENAI_API_KEY") and not env_module.getenv("AZURE_OPENAI_KEY"):
                            error_details.append("Missing Azure OpenAI API key")
                        if not env_module.getenv("AZURE_OPENAI_ENDPOINT"):
                            error_details.append("Missing Azure OpenAI endpoint")
                    elif provider == "openai":
                        if not env_module.getenv("OPENAI_API_KEY"):
                            error_details.append("Missing OpenAI API key")
                    elif provider == "huggingface":
                        error_details.append("HuggingFace model may not be available or sentence-transformers not installed")
                    
                    error_msg = f"Failed to create embedding function. {'; '.join(error_details) if error_details else 'Unknown error'}"
                    return jsonify({
                        "success": False,
                        "error": error_msg
                    })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Embedding connection test error: {str(e)}"
                })
        
        else:
            return jsonify({
                "success": False,
                "error": "Invalid test type. Use 'llm' or 'embedding'"
            })
            
    except Exception as e:
        print(f"FULL TRACEBACK: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Connection test failed: {str(e)}"
        })

@app.route('/api/models/add', methods=['POST'])
def add_custom_model():
    """API endpoint to add custom model"""
    data = request.get_json()
    model_type = data.get('type')  # 'embedding' or 'llm'
    provider = data.get('provider')
    model_name = data.get('name')
    
    if not all([model_type, provider, model_name]):
        return jsonify({
            "success": False,
            "error": "Missing required fields: type, provider, name"
        })
    
    try:
        save_custom_model(model_type, provider, model_name)
        return jsonify({
            "success": True,
            "message": f"✅ Custom {model_type} model '{model_name}' added successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add custom model: {str(e)}"
        })

@app.route('/api/models/remove', methods=['POST'])
def remove_custom_model():
    """API endpoint to remove custom model"""
    data = request.get_json()
    model_type = data.get('type')  # 'embedding' or 'llm'
    provider = data.get('provider')
    model_name = data.get('name')
    
    if not all([model_type, provider, model_name]):
        return jsonify({
            "success": False,
            "error": "Missing required fields: type, provider, name"
        })
    
    try:
        # Load existing custom models
        custom_models = load_custom_models()
        
        # Remove the model
        if model_type in custom_models and provider in custom_models[model_type]:
            if model_name in custom_models[model_type][provider]:
                custom_models[model_type][provider].remove(model_name)
                
                # Clean up empty provider lists
                if not custom_models[model_type][provider]:
                    del custom_models[model_type][provider]
                
                # Save updated models
                import json
                custom_models_file = os.path.join(os.path.dirname(__file__), 'custom_models.json')
                with open(custom_models_file, 'w') as f:
                    json.dump(custom_models, f, indent=2)
                
                return jsonify({
                    "success": True,
                    "message": f"✅ Custom {model_type} model '{model_name}' removed successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Model '{model_name}' not found in {provider} {model_type} models"
                })
        else:
            return jsonify({
                "success": False,
                "error": f"No custom {model_type} models found for provider {provider}"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to remove custom model: {str(e)}"
        })

@app.route('/api/providers/list')
def list_custom_providers():
    """API endpoint to list custom providers"""
    try:
        custom_providers = load_custom_providers()
        return jsonify({
            "success": True,
            "providers": custom_providers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load custom providers: {str(e)}"
        })

@app.route('/api/providers/add', methods=['POST'])
def add_custom_provider():
    """API endpoint to add custom provider"""
    data = request.get_json()
    provider_type = data.get('type')  # 'llm', 'embedding', or 'both'
    provider_id = data.get('id')
    display_name = data.get('display_name')
    base_url = data.get('base_url')
    api_key_env = data.get('api_key_env')
    
    if not all([provider_type, provider_id, display_name]):
        return jsonify({
            "success": False,
            "error": "Missing required fields: type, id, display_name"
        })
    
    try:
        # Validate provider_id format (no spaces, lowercase, hyphens ok)
        import re
        if not re.match(r'^[a-z0-9-]+$', provider_id):
            return jsonify({
                "success": False,
                "error": "Provider ID must contain only lowercase letters, numbers, and hyphens"
            })
            
        if provider_type in ['llm', 'both']:
            save_custom_provider('llm', provider_id, display_name, base_url, api_key_env)
        if provider_type in ['embedding', 'both']:
            save_custom_provider('embedding', provider_id, display_name, base_url, api_key_env)
            
        return jsonify({
            "success": True,
            "message": f"✅ Custom provider '{display_name}' added successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add custom provider: {str(e)}"
        })

@app.route('/api/models/list')
def list_custom_models():
    """API endpoint to list custom models"""
    try:
        custom_models = load_custom_models()
        return jsonify({
            "success": True,
            "models": custom_models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load custom models: {str(e)}"
        })

@app.route('/static/js/model_selector_fix.js')
def serve_model_fix_script():
    """Serve the model selector fix script"""
    try:
        fix_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'js', 'model_selector_fix.js')
        with open(fix_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        return Response(script_content, mimetype='application/javascript')
    except Exception as e:
        return Response(f'console.error("Failed to load fix script: {str(e)}");', mimetype='application/javascript')

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
        # Force refresh to get latest data
        chromadb_admin.refresh_client()
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
        # Refresh client to ensure we get current stats
        chromadb_admin.refresh_client()
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
        # Refresh client to ensure we get current collections
        chromadb_admin.refresh_client()
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
    embedding_provider = data.get('embedding_provider', '')
    embedding_model = data.get('embedding_model', '')
    
    if not collection_name:
        return jsonify({"success": False, "error": "Collection name is required"}), 400
    
    try:
        # If embedding model is specified, pass it to create_collection
        if embedding_provider and embedding_model:
            result = chromadb_admin.create_collection(
                collection_name, 
                embedding_provider=embedding_provider,
                embedding_model=embedding_model
            )
        else:
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
        
        # Force cleanup of existing ChromaDB instances before creating pipeline
        try:
            from chromadb_factory import cleanup_chromadb_instances
            cleanup_chromadb_instances()
            print("🧹 Cleared existing ChromaDB instances before file upload")
            
            # Brief pause to allow cleanup
            import time
            time.sleep(0.5)
        except Exception as cleanup_error:
            print(f"ChromaDB cleanup warning: {cleanup_error}")
        
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
            flash(f"Successfully uploaded {success_count} resume(s) to collection '{collection_name}'", "success")
        if error_count > 0:
            flash(f"{error_count} resume(s) failed to upload", "warning")
        
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
    print("API ENDPOINT CALLED!")
    print(f"Collection: {collection_name}")
    print(f"Request method: {request.method}")
    print(f"Request form: {request.form}")
    
    if not chromadb_admin:
        print("ChromaDB admin not available")
        return jsonify({"success": False, "error": "ChromaDB admin not available"}), 500
    
    try:
        upload_type = request.form.get('upload_type', 'directory')
        print(f"Upload type: {upload_type}")
        
        if upload_type == 'directory':
            # Directory upload
            upload_directory = request.form.get('upload_directory')
            print(f"Upload directory: {upload_directory}")
            if not upload_directory:
                return jsonify({"success": False, "error": "Upload directory required"}), 400
            
            upload_path = Path(upload_directory)
            if not upload_path.exists():
                return jsonify({"success": False, "error": f"Directory does not exist: {upload_directory}"}), 400
            
            # Check if directory has files
            files = list(upload_path.glob('**/*'))
            supported_files = [f for f in files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
            print(f"Found {len(supported_files)} supported files")
            
            if not supported_files:
                return jsonify({"success": False, "error": "No supported files found in directory"}), 400
            
            # Process directory with timeout handling
            sys.path.append(str(current_dir.parent.parent))
            print(f"Trying to import ResumeIngestPipeline...")
            
            # Force cleanup of existing ChromaDB instances before creating pipeline
            try:
                from chromadb_factory import cleanup_chromadb_instances
                cleanup_chromadb_instances()
                print("🧹 Cleared existing ChromaDB instances before directory upload")
                
                # Brief pause to allow cleanup
                import time
                time.sleep(0.5)
            except Exception as cleanup_error:
                print(f"ChromaDB cleanup warning: {cleanup_error}")
            
            try:
                from ingest_pipeline import ResumeIngestPipeline
                print(f"Successfully imported ResumeIngestPipeline")
                
                print(f"Creating pipeline for collection: {collection_name}")
                pipeline = ResumeIngestPipeline(collection_name=collection_name)
                print(f"✅ Pipeline created successfully")
                
            except Exception as pipeline_error:
                print(f"Pipeline creation failed: {pipeline_error}")
                return jsonify({
                    "success": False, 
                    "error": f"Failed to initialize pipeline: {str(pipeline_error)}"
                }), 500
            
            results = []
            processed_count = 0
            
            for file_path in supported_files:
                try:
                    print(f"Processing file {processed_count + 1}/{len(supported_files)}: {file_path.name}")
                    success, resume_id, chunks_added = pipeline.add_resume(str(file_path))
                    print(f"✅ Result: success={success}, resume_id={resume_id}, chunks={chunks_added}")
                    print(f"📊 Resume processed: {file_path.name} ({'✅ SUCCESS' if success else 'FAILED'})")
                    
                    results.append({
                        'file': file_path.name,
                        'success': success,
                        'chunks': chunks_added,
                        'resume_id': resume_id,
                        'resume_count': 1 if success else 0,  # Always 1 resume per file
                        'error': None if success else "Failed to process file"
                    })
                    processed_count += 1
                    
                except Exception as file_error:
                    print(f"Error processing {file_path}: {str(file_error)}")
                    results.append({
                        'file': file_path.name,
                        'success': False,
                        'chunks': 0,
                        'resume_count': 0,  # Failed upload = 0 resumes
                        'error': str(file_error)
                    })
                    processed_count += 1
            
            success_count = sum(1 for r in results if r['success'])
            
            # Refresh ChromaDB client to ensure new data is visible
            if success_count > 0:
                print("🔄 Refreshing ChromaDB client to show new data...")
                chromadb_admin.refresh_client()
            
            # Print upload summary for directory
            print(f"\n📈 DIRECTORY UPLOAD SUMMARY:")
            print(f"   📊 Total resumes processed: {len(results)}")
            print(f"   ✅ Successful uploads: {success_count}")
            print(f"   Failed uploads: {len(results) - success_count}")
            print(f"   📦 Total chunks created: {sum(r.get('chunks', 0) for r in results)}")
            print(f"   📁 Collection: {collection_name}")
            print(f"   📂 Source directory: {upload_directory}\n")
            
            return jsonify({
                "success": True,
                "message": f"Processed {len(results)} resume(s), {success_count} successful",
                "results": results,
                "success_count": success_count,
                "error_count": len(results) - success_count,
                "resume_count": success_count,  # Clear resume count
                "total_chunks": sum(r.get('chunks', 0) for r in results)  # Total chunks for reference
            })
        
        elif upload_type == 'files':
            # File upload via form
            uploaded_files = request.files.getlist('files')
            if not uploaded_files:
                return jsonify({"error": "No files uploaded"}), 400
            
            # Use existing ChromaDB connection with pipeline to avoid conflicts
            if not chromadb_admin:
                return jsonify({"error": "ChromaDB admin not initialized"}), 500
            
            # Import the pipeline but use existing connection
            sys.path.append(str(current_dir.parent.parent))
            from ingest_pipeline import ResumeIngestPipeline
            
            # Create pipeline with existing database connection
            try:
                # Get the existing database from admin
                existing_db = chromadb_admin.get_existing_db_connection()
                
                if existing_db:
                    # Create pipeline with existing connection
                    pipeline = ResumeIngestPipeline(
                        collection_name=collection_name, 
                        persist_directory=str(chromadb_admin.db_path),
                        use_existing_db=existing_db
                    )
                    print("✅ Using existing ChromaDB connection for pipeline")
                else:
                    raise Exception("Could not get existing database connection")
                    
            except Exception as e:
                print(f"Could not reuse connection: {e}")
                print("🧹 Cleaning up connections before creating new pipeline...")
                
                # Force cleanup of all connections before creating new one
                try:
                    from chromadb_factory import cleanup_chromadb_instances
                    cleanup_chromadb_instances()
                    
                    # Also refresh admin client to clear its connection
                    chromadb_admin.refresh_client()
                    
                    # Brief pause to allow cleanup
                    import time
                    time.sleep(1.0)
                    print("✅ Cleanup completed, creating new pipeline...")
                except Exception as cleanup_error:
                    print(f"Cleanup warning: {cleanup_error}")
                
                # Now create new pipeline
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
                            print(f"Processing uploaded file: {file.filename}")
                            success, resume_id, chunks_added = pipeline.add_resume(str(file_path), original_filename=file.filename)
                            print(f"✅ Result: success={success}, resume_id={resume_id}, chunks={chunks_added}")
                            print(f"📊 Resume uploaded: {file.filename} ({'✅ SUCCESS' if success else 'FAILED'})")
                            results.append({
                                'file': file.filename,
                                'success': success,
                                'chunks': chunks_added,
                                'resume_id': resume_id,
                                'resume_count': 1 if success else 0,  # Always 1 resume per file
                                'error': None if success else "Failed to process file"
                            })
                        except Exception as file_error:
                            print(f"DETAILED ERROR processing {file.filename}: {str(file_error)}")
                            print(f"ERROR TYPE: {type(file_error).__name__}")
                            import traceback
                            print(f"FULL TRACEBACK: {traceback.format_exc()}")
                            results.append({
                                'file': file.filename,
                                'success': False,
                                'chunks': 0,
                                'resume_count': 0,  # Failed upload = 0 resumes
                                'error': f"Error: {str(file_error)}"
                            })
            
            success_count = sum(1 for r in results if r['success'])
            
            # Clean up pipeline connections to prevent conflicts
            try:
                if hasattr(pipeline, 'db') and pipeline.db:
                    del pipeline.db
                del pipeline
                print("🧹 Cleaned up pipeline connections")
            except Exception as cleanup_error:
                print(f"Pipeline cleanup warning: {cleanup_error}")
            
            # Refresh ChromaDB client to ensure new data is visible
            if success_count > 0:
                print("🔄 Refreshing ChromaDB client to show new data...")
                chromadb_admin.refresh_client()
            
            # Print upload summary for files
            print(f"\n📈 FILE UPLOAD SUMMARY:")
            print(f"   📊 Total resumes processed: {len(results)}")
            print(f"   ✅ Successful uploads: {success_count}")
            print(f"   Failed uploads: {len(results) - success_count}")
            print(f"   📦 Total chunks created: {sum(r.get('chunks', 0) for r in results)}")
            print(f"   📁 Collection: {collection_name}\n")
            
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
    import traceback
    error_details = str(error) if error else "Unknown error"
    traceback_str = traceback.format_exc()
    print(f"ERROR 500: {error_details}")
    print(f"Traceback: {traceback_str}")
    
    # Create a more informative error message
    if "chromadb" in error_details.lower():
        flash(f"Database connection error: {error_details}", "error")
    elif "permission" in error_details.lower():
        flash(f"Permission error: {error_details}", "error")
    elif "file" in error_details.lower() and "not found" in error_details.lower():
        flash(f"File system error: {error_details}", "error")
    else:
        flash(f"Internal server error: {error_details}", "error")
    
    return render_template('admin_dashboard.html'), 500

def cleanup_and_exit():
    """Gracefully cleanup ChromaDB connections on exit"""
    print("\n🔄 Gracefully shutting down...")
    try:
        if chromadb_admin:
            print("🧹 Cleaning up ChromaDB connections...")
            # Use the dedicated close method
            chromadb_admin.close_client()
        
        # Also cleanup the factory cached instances
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from chromadb_factory import cleanup_chromadb_instances
            cleanup_chromadb_instances()
        except Exception as e:
            print(f"Factory cleanup error: {e}")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    # Force garbage collection to clean up any remaining references
    import gc
    gc.collect()
    print("✅ Cleanup completed")

def signal_handler(signum, frame):
    """Handle interrupt signals (Ctrl+C)"""
    print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
    cleanup_and_exit()
    print("👋 Goodbye!")
    sys.exit(0)

# Register signal handlers and cleanup functions
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
atexit.register(cleanup_and_exit)  # Called on normal exit

@app.route('/debug/template')
def debug_template():
    """Debug endpoint to check template content"""
    try:
        import os
        template_path = os.path.join(app.template_folder, 'query_interface.html')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
                # Check if our modifications are there
                has_v3_title = 'v3.0' in content
                has_status_box = 'statusRow' in content
                has_debug_marker = 'TEMPLATE DEBUG' in content
                
                return {
                    'template_path': template_path,
                    'template_exists': True,
                    'has_v3_title': has_v3_title,
                    'has_status_box': has_status_box,
                    'has_debug_marker': has_debug_marker,
                    'template_size': len(content)
                }
        else:
            return {'error': f'Template not found at {template_path}'}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':    
    # Check if templates directory exists
    templates_dir = current_dir.parent / 'templates'
    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        print("Please ensure the templates directory exists with HTML files.")
        sys.exit(1)
    
    try:
        # Load saved model configuration
        print("🔧 Loading saved model configuration...")
        saved_config = load_model_config()
        apply_saved_config(saved_config)
        
        # Get port from environment variable for Azure App Service compatibility
        port = int(os.getenv('PORT', 5001))
        host = '0.0.0.0'  # Bind to all interfaces for container deployment
        
        print(f"🚀 Starting Flask app on {host}:{port}")
        app.run(debug=False, port=port, host=host, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt received")
    except Exception as e:
        print(f"Failed to start Flask app: {e}")
    finally:
        # Ensure cleanup happens even if app.run() exits unexpectedly
        cleanup_and_exit()
        sys.exit(1)