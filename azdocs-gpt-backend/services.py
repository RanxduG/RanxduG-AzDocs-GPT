# services.py - Business logic services
from openai import AzureOpenAI
from azure.identity import ClientSecretCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
import msal
import jwt
import json
import datetime
from typing import Tuple, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AzureSearchService:
    """Handles Azure AI Search operations"""
    
    def __init__(self, config):
        self.client = SearchClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            index_name=config.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(config.AZURE_SEARCH_KEY)
        )
        self.semantic_config = config.AZURE_SEARCH_SEMANTIC_CONFIG
        self.results_count = config.SEARCH_RESULTS_COUNT
    
    def search(self, query: str) -> Tuple[str, List[Dict]]:
        """Search Azure AI Search and return formatted content and references"""
        try:
            results = self.client.search(
                search_text=query,
                query_type="semantic",
                semantic_configuration_name=self.semantic_config,
                select="title,chunk",
                top=self.results_count,
                vector_queries=[VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="text_vector")]
            )
            
            references = []
            content = ""
            
            for result in results:
                content += f"[{result['title']}]: {result['chunk']}\n----\n"
                references.append({
                    "title": result['title'],
                    "content": result['chunk']
                })
            
            logger.info(f"Search completed for query: {query[:50]}... Found {len(references)} results")
            return content, references
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {str(e)}")
            raise

class OpenAIService:
    """Handles Azure OpenAI operations"""
    
    def __init__(self, config):
        self.client = AzureOpenAI(
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_KEY
        )
        self.deployment = config.AZURE_OPENAI_DEPLOYMENT
        self.system_prompt = self._get_system_prompt()
        self.search_tools = self._get_search_tools()
    
    def _get_system_prompt(self) -> str:
        return (
            "You are an expert assistant that helps developers with their questions about Azure. "
            "To answer a question or when creating searches or clarification questions, *only* use information provided by the documentation. "
            "For every statement you make, you need to provide the source from the documentation. Each search result from the documentation has its file name as a prefix in square brackets. "
            "If you can't find the answer, you can say 'I don't know' or 'I can't find the answer'. "
            "Write your answer in markdown. "
            "If you see that search results are unrelated to the product the user is talking about, point that out and say you don't have good grounding data to answer."
        )
    
    def _get_search_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the documentation to find the right data to answer the last question in this conversation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to use for the documentation."
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def generate_search_query(self, messages: List[Dict]) -> str:
        """Generate a search query using OpenAI"""
        try:
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=self.search_tools
            )
            
            if completion.choices[0].finish_reason == "tool_calls":
                for call in completion.choices[0].message.tool_calls:
                    if call.function.name == "search":
                        query_data = json.loads(call.function.arguments)
                        return query_data["query"], call
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error generating search query: {str(e)}")
            raise
    
    def generate_answer(self, messages: List[Dict]) -> str:
        """Generate answer based on search results"""
        try:
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages
            )
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

class AuthService:
    """Handles authentication operations"""
    
    def __init__(self, config):
        self.config = config
        self.msal_app = msal.ConfidentialClientApplication(
            config.AZURE_AD_CLIENT_ID,
            authority=config.AZURE_AD_AUTHORITY,
            client_credential=config.AZURE_AD_CLIENT_SECRET
        )
    
    def get_authorization_url(self) -> str:
        """Get Microsoft authorization URL"""
        return self.msal_app.get_authorization_request_url(
            scopes=self.config.AZURE_AD_SCOPE,
            redirect_uri=self.config.REDIRECT_URI
        )
    
    def acquire_token_by_code(self, code: str) -> Dict:
        """Acquire token using authorization code"""
        return self.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.config.AZURE_AD_SCOPE,
            redirect_uri=self.config.REDIRECT_URI
        )
    
    def create_jwt_token(self, user_info: Dict) -> str:
        """Create JWT token for frontend"""
        token_payload = {
            "sub": user_info.get("oid"),
            "email": user_info.get("preferred_username"),
            "name": user_info.get("name"),
            "roles": user_info.get("roles", []),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=self.config.JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(token_payload, self.config.SECRET_KEY, algorithm="HS256")
    
    def decode_jwt_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        try:
            return jwt.decode(token, self.config.SECRET_KEY, algorithms=["HS256"])
        except Exception as e:
            logger.error(f"Token decode error: {str(e)}")
            return None