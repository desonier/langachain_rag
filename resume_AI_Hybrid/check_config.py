import sys
sys.path.append('.')
from shared_config import get_config

config = get_config()
print('Current shared configuration:')
print(f'Azure endpoint: {getattr(config, "azure_endpoint", "Not set")}')
api_key = getattr(config, "api_key", "Not set")
print(f'Azure API key: {api_key[:8] if api_key != "Not set" else "Not set"}...')
print(f'Azure deployment: {getattr(config, "deployment_name", "Not set")}')
print(f'Embedding provider: {getattr(config, "embedding_provider", "Not set")}')
print(f'LLM provider: {getattr(config, "llm_provider", "Not set")}')
print(f'LLM temperature: {getattr(config, "llm_temperature", "Not set")}')