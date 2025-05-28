# config.py - Configuration management
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('APPSETTING_FLASK_SECRET_KEY') or 'dev-secret-key-change-in-prod'
    
    # Azure AD Configuration
    AZURE_AD_TENANT_ID = os.environ.get('APPSETTING_AZURE_AD_TENANT_ID')
    AZURE_AD_CLIENT_ID = os.environ.get('APPSETTING_AZURE_AD_CLIENT_ID')
    AZURE_AD_CLIENT_SECRET = os.environ.get('APPSETTING_AZURE_AD_CLIENT_SECRET')
    AZURE_AD_SCOPE = [os.environ.get('APPSETTING_AZURE_AD_SCOPE')]
    AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.environ.get('APPSETTING_AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT = os.environ.get('APPSETTING_AZURE_OPENAI_DEPLOYMENT')
    AZURE_OPENAI_KEY = os.environ.get('APPSETTING_AZURE_OPENAI_KEY')
    AZURE_OPENAI_API_VERSION = "2023-03-15-preview"
    
    # Azure Search Configuration
    AZURE_SEARCH_ENDPOINT = os.environ.get('APPSETTING_AZURE_SEARCH_ENDPOINT')
    AZURE_SEARCH_KEY = os.environ.get('APPSETTING_AZURE_SEARCH_KEY')
    AZURE_SEARCH_INDEX = os.environ.get('APPSETTING_AZURE_SEARCH_INDEX')
    AZURE_SEARCH_SEMANTIC_CONFIG = "azdocs-test3-semantic-configuration"
    
    # Cosmos DB Configuration
    COSMOS_ENDPOINT = os.environ.get('APPSETTING_COSMOS_ENDPOINT')
    COSMOS_KEY = os.environ.get('APPSETTING_COSMOS_KEY')
    COSMOS_DATABASE_NAME = os.environ.get('APPSETTING_COSMOS_DATABASE_NAME', 'ChatApp')
    COSMOS_CONTAINER_NAME = os.environ.get('APPSETTING_COSMOS_CONTAINER_NAME', 'UserChats')
    
    # Application Configuration
    REDIRECT_PATH = "/getAToken"
    CORS_ORIGINS = ["http://localhost:3000"]
    JWT_EXPIRATION_HOURS = 1
    SEARCH_RESULTS_COUNT = 5
    COSMOS_THROUGHPUT = 400

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    REDIRECT_URI = "http://localhost:5000/getAToken"
    FRONTEND_URL = "http://localhost:3000"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    REDIRECT_URI = "https://azdocsgpt-b4bqhrg2gjh2byhc.southeastasia-01.azurewebsites.net/getAToken"
    FRONTEND_URL = "https://your-frontend-domain.com"  # Update with actual frontend URL
    CORS_ORIGINS = ["https://your-frontend-domain.com"]

# Get configuration based on environment
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()