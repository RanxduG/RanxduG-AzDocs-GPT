# app.py - Flask backend for AzDocs-GPT
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider, ClientSecretCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import msal
import jwt
import datetime
from azure.cosmos import CosmosClient, PartitionKey
import json
import logging
import sys

# Configure logging for Azure App Service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Azure Configuration
load_dotenv()
env_vars = dict(os.environ)

AZURE_AD_TENANT_ID = env_vars.get("APPSETTING_AZURE_AD_TENANT_ID")
AZURE_AD_CLIENT_ID = env_vars.get("APPSETTING_AZURE_AD_CLIENT_ID")
AZURE_AD_CLIENT_SECRET = env_vars.get("APPSETTING_AZURE_AD_CLIENT_SECRET")
REDIRECT_PATH = "/getAToken"
REDIRECT_URI = "https://azdocsgpt-b4bqhrg2gjh2byhc.southeastasia-01.azurewebsites.net/getAToken"
SCOPE = [env_vars.get("APPSETTING_AZURE_AD_SCOPE")]
AZURE_OPENAI_ENDPOINT = env_vars.get("APPSETTING_AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = env_vars.get("APPSETTING_AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_KEY = env_vars.get("APPSETTING_AZURE_OPENAI_KEY")
AZURE_SEARCH_ENDPOINT = env_vars.get("APPSETTING_AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = env_vars.get("APPSETTING_AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = env_vars.get("APPSETTING_AZURE_SEARCH_INDEX")
AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}"
# --- Cosmos DB Setup ---
COSMOS_ENDPOINT = env_vars.get("APPSETTING_COSMOS_ENDPOINT")
COSMOS_KEY = env_vars.get("APPSETTING_COSMOS_KEY")
DATABASE_NAME = env_vars.get("APPSETTING_COSMOS_DATABASE_NAME", "ChatApp")
CONTAINER_NAME = env_vars.get("APPSETTING_COSMOS_CONTAINER_NAME", "UserChats")

app = Flask(__name__)
app.secret_key = env_vars.get("APPSETTING_FLASK_SECRET_KEY", "change-this-key-in-prod")
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Initialize Azure services
# azure_credential = DefaultAzureCredential()

azure_credential = ClientSecretCredential(
    tenant_id=AZURE_AD_TENANT_ID,
    client_id=AZURE_AD_CLIENT_ID,
    client_secret=AZURE_AD_CLIENT_SECRET
)


openai_client = AzureOpenAI(
    api_version="2023-03-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY 
    # azure_ad_token_provider=get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
)

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

# MSAL client for Azure AD authentication
msal_app = msal.ConfidentialClientApplication(
    AZURE_AD_CLIENT_ID,
    authority=AZURE_AD_AUTHORITY,
    client_credential=AZURE_AD_CLIENT_SECRET
)

# Initialize Cosmos DB client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/userId"),
    offer_throughput=400
)

# System prompt for the chatbot
SYSTEM_PROMPT = ("You are an expert assistant that helps developers with their questions about Azure. "
                "To answer a question or when creating searches or clarification questions, *only* use information provided by the documentation. "
                "For every statement you make, you need to provide the source from the documentation. Each search result from the documentation has its file name as a prefix in square brackets. "
                "If you can't find the answer, you can say 'I don't know' or 'I can't find the answer'."
                "Write your answer in markdown. "
                "If you see that search results are unrelated to the product the user is talking about, point that out and say you don't have good grounding data to answer.")

# Function to search Azure AI Search
def search_azure(query, n=5):
    results = search_client.search(
        search_text=query,
        query_type="semantic",
        semantic_configuration_name="azdocs-test3-semantic-configuration",
        select="title,chunk",
        top=n,
        vector_queries=[VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="text_vector")]
    )
    
    references = []
    content = ""
    
    for r in results:
        content += f"[{r['title']}]: {r['chunk']}\n----\n"
        references.append({
            "title": r['title'],
            "content": r['chunk']
        })
    
    return content, references

# Helper function: extract user id (subject) from JWT token.
def get_user_id_from_token():
    auth_header = request.headers.get('Authorization')
    logger.info(f"Auth Header: {auth_header}")
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    logger.info(f"Token: {token}")
    try:
        decoded = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        return decoded.get("sub")
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None

# Functions to interact with Cosmos DB
def store_user_chat(user_id, chat_id, messages):
    """
    Stores or updates a chat document for the user.
    """
    item = {
        "id": chat_id,           # Unique identifier for the chat
        "userId": user_id,       # Partition key: user ID from Azure AD
        "messages": messages,    # List of messages (each message is a dict)
        "lastUpdated": datetime.datetime.utcnow().isoformat()
    }
    container.upsert_item(item)
    return item

def get_user_chats(user_id):
    """
    Retrieves all chat documents for a given user.
    """
    query = "SELECT * FROM c WHERE c.userId = @userId"
    parameters = [{"name": "@userId", "value": user_id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    return items

@app.route("/login")
def login():
    logger.info(f"Login endpoint called: {REDIRECT_URI}")
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def authorized():
    code = request.args.get("code")
    if not code:
        return "Authorization failed", 400

    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" in result:
        user_info = result.get("id_token_claims")
        logger.info(f"User authenticated: {user_info}")

        # ✅ Create your own JWT to send to frontend
        token_payload = {
            "sub": user_info.get("oid"),  # Azure AD Object ID
            "email": user_info.get("preferred_username"),
            "name": user_info.get("name"),
            "roles": user_info.get("roles", []),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        jwt_token = jwt.encode(token_payload, app.secret_key, algorithm="HS256")
        logger.info(f"JWT Token: {jwt_token}")

        # ✅ Redirect to frontend with token in query param
        return redirect(f"http://localhost:3000/auth/callback?token={jwt_token}")

    return f"Login failed: {result.get('error_description')}", 400

@app.route("/logout")
def logout():
    session.clear()
    return redirect(f"{AZURE_AD_AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri=https://azdocsgpt-b4bqhrg2gjh2byhc.southeastasia-01.azurewebsites.net/")

# --- New Chat History Endpoints ---

# Get all chats for a user
@app.route('/api/chats', methods=['GET'])
def get_chats():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    chats = get_user_chats(user_id)
    data = []
    for chat in chats:
        data.append({
            "id": chat["id"],
            "messages": chat["messages"],
            "lastUpdated": chat["lastUpdated"]
        })
    logger.info(f"User {user_id} chats: {chats}")
    logger.info(f"Jsonify chats: {json.dumps(chats, indent=2)}")
    return jsonify(data)

# Save or update a chat for a user
@app.route('/api/chats', methods=['POST'])
def save_chat():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    chat_id = data.get("chat_id")
    messages = data.get("messages", [])
    
    if not chat_id:
        return jsonify({"error": "chat_id is required"}), 400
    
    item = store_user_chat(user_id, chat_id, messages)
    return jsonify({"status": "success", "chat": item}), 200

# Get a specific chat using the chat_id
@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = "SELECT * FROM c WHERE c.userId = @userId AND c.id = @chatId"
    parameters = [
        {"name": "@userId", "value": user_id},
        {"name": "@chatId", "value": chat_id}
    ]
    
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    logger.info(f"Items: {items}")
    
    if not items:
        return jsonify({"error": "Chat not found"}), 404
    
    return jsonify(items[0]), 200

# Create a new chat
@app.route('/api/chats/new', methods=['POST'])
def new_chat():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Generate a new chat ID
    chat_id = str(datetime.datetime.utcnow().timestamp())
    
    # Store the new chat with an empty message list
    item = store_user_chat(user_id, chat_id, [])

    return redirect(f"http://localhost:3000/chat/{chat_id}", code=302)

# API route for chat
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        logger.info("Chat endpoint called")
        # Get user ID from token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({"error": "Unauthorized access"}), 401
        
        data = request.json
        logger.info(f"Data received: {data}")
        user_message = data.get('message', '')
        chat_id = data.get('chat_id', '')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        if not chat_id:
            return jsonify({"error": "No chat_id provided"}), 400
        
        # Get existing chat history or create new if doesn't exist
        try:
            query = "SELECT * FROM c WHERE c.userId = @userId AND c.id = @chatId"
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@chatId", "value": chat_id}
            ]
            
            existing_chats = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if existing_chats:
                chat_history = existing_chats[0]['messages']
            else:
                chat_history = []
                
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            chat_history = []
        
        # Generate search query using OpenAI
        tools = [
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
        
        # Build messages array including chat history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add previous chat history
        for msg in chat_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        logger.info(f"user_message: {user_message}")
        logger.info(f"chat_id: {chat_id}")
        
        # Step 1: Generate search query
        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT, 
            messages=messages, 
            tools=tools
        )
        
        assistant_response = ""
        references = []
        
        # Check if the model wants to search
        if completion.choices[0].finish_reason == "tool_calls":
            for call in completion.choices[0].message.tool_calls:
                if call.function.name == "search":
                    import json
                    query = json.loads(call.function.arguments)["query"]
                    
                    # Step 2: Perform search
                    search_content, references = search_azure(query)

                    # Step 3: Generate answer based on search results
                    answer_messages = messages + [
                        {"role": "assistant", "content": "I'll search for information to help answer your question.", "tool_calls": [call]},
                        {"role": "tool", "tool_call_id": call.id, "content": search_content}
                    ]
                    
                    answer_completion = openai_client.chat.completions.create(
                        model=AZURE_OPENAI_DEPLOYMENT,
                        messages=answer_messages
                    )
                    
                    assistant_response = answer_completion.choices[0].message.content
        else:
            # Fallback if no search was performed
            assistant_response = "I'm not sure how to answer your question without searching for more information."
        index= 2
        # Update chat history with new messages
        chat_history.append({
            "id": str(index+1),
            "sender": "user",
            "content": user_message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
        chat_history.append({
            "id": str(index+2),
            "sender": "bot", 
            "content": assistant_response,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "references": references
        })
        
        # Save updated chat history to Cosmos DB
        try:
            store_user_chat(user_id, chat_id, chat_history)
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
            # Continue anyway - don't fail the request if save fails
        
        return jsonify({
            "text": assistant_response,
            "references": references,
            "chat_id": chat_id
        })
        
    except Exception as e:
        logger.error(f"Error in chat function: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API route for /
# @app.route('/')
# def index():
#     logger.info("Index route called")
#     return jsonify({"message": "Welcome to the AzDocs-GPT API!"})

@app.route('/')
def index():
    logger.info("Index route called")
    # Return all environment variables
    env_vars = dict(os.environ)

    # Take one varibale and log
    logger.info(f"Environment variable APPSETTING_AZURE_OPENAI_KEY: {env_vars.get('APPSETTING_AZURE_OPENAI_KEY', 'Not Set')}")
    
    return jsonify(env_vars)


if __name__ == '__main__':
    app.run()