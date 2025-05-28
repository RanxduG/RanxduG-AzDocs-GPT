from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.cosmos import CosmosClient, PartitionKey
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from msal import ConfidentialClientApplication
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import requests
import os
from dotenv import load_dotenv
import uuid
import json
import jwt
import datetime

load_dotenv()

app = FastAPI()

# Secret key for JWT
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-key-in-prod")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Azure Config - Updated to use correct environment variable names
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME", "ChatApp")
CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "UserChats")
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
AZURE_REDIRECT_URI = os.getenv("REDIRECT_URI")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_SCOPE = [os.getenv("AZURE_AD_SCOPE")]
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
REDIRECT_PATH = "/getAToken"

# System prompt for the chatbot
SYSTEM_PROMPT = ("You are an expert assistant that helps developers with their questions about Azure. "
                "To answer a question or when creating searches or clarification questions, *only* use information provided by the documentation. "
                "For every statement you make, you need to provide the source from the documentation. Each search result from the documentation has its file name as a prefix in square brackets. "
                "If you can't find the answer, you can say 'I don't know' or 'I can't find the answer'."
                "Write your answer in markdown. "
                "If you see that search results are unrelated to the product the user is talking about, point that out and say you don't have good grounding data to answer.")

# Initialize Azure services
azure_credential = DefaultAzureCredential()

openai_client = AzureOpenAI(
    api_version="2023-03-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_ad_token_provider=get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
)

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX,
    credential=AzureKeyCredential(SEARCH_KEY)
)

# Initialize Cosmos DB client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/userId"),
    offer_throughput=400
)

msal_app = ConfidentialClientApplication(
    AZURE_CLIENT_ID,
    authority=AZURE_AUTHORITY,
    client_credential=AZURE_CLIENT_SECRET
)

# Models
class ChatRequest(BaseModel):
    message: str
    chat_id: str

class SaveChatRequest(BaseModel):
    chat_id: str
    messages: List[Dict[str, Any]]

class Message(BaseModel):
    id: str
    sender: str
    content: str
    timestamp: str
    references: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    id: str
    messages: List[Message]
    lastUpdated: str

# Helper functions
def get_user_id_from_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        return None
    
    token = authorization.split(' ')[1]
    print(f"Token: {token}")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded.get("sub")
    except Exception as e:
        print(f"Token decode error: {e}")
        return None

def search_azure(query: str, n: int = 5):
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

def store_user_chat(user_id: str, chat_id: str, messages: List[Dict]):
    """Stores or updates a chat document for the user."""
    item = {
        "id": chat_id,
        "userId": user_id,
        "messages": messages,
        "lastUpdated": datetime.datetime.utcnow().isoformat()
    }
    container.upsert_item(item)
    return item

def get_user_chats(user_id: str):
    """Retrieves all chat documents for a given user."""
    query = "SELECT * FROM c WHERE c.userId = @userId"
    parameters = [{"name": "@userId", "value": user_id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    return items

# Routes
@app.get("/")
def index():
    return {"message": "Welcome to the AzDocs-GPT API!"}

@app.get("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )
    return RedirectResponse(auth_url)

@app.get("/getAToken")
def get_token(request: Request, code: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed")
    
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )
    
    if "access_token" in result:
        user_info = result.get("id_token_claims")
        print(f"User authenticated: {user_info}")
        
        # Create JWT token
        token_payload = {
            "sub": user_info.get("oid"),
            "email": user_info.get("preferred_username"),
            "name": user_info.get("name"),
            "roles": user_info.get("roles", []),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        
        jwt_token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")
        print(f"JWT Token: {jwt_token}")
        
        return RedirectResponse(f"http://localhost:3000/auth/callback?token={jwt_token}")
    
    return JSONResponse(
        content={"error": f"Login failed: {result.get('error_description')}"},
        status_code=400
    )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(f"{AZURE_AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:5000/")

# Chat history endpoints
@app.get("/api/chats")
def get_chats(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    chats = get_user_chats(user_id)
    data = []
    for chat in chats:
        data.append({
            "id": chat["id"],
            "messages": chat["messages"],
            "lastUpdated": chat["lastUpdated"]
        })
    
    print(f"User {user_id} chats: {chats}")
    print(f"Jsonify chats: {json.dumps(chats, indent=2)}")
    return data

@app.post("/api/chats")
def save_chat(data: SaveChatRequest, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not data.chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    item = store_user_chat(user_id, data.chat_id, data.messages)
    return {"status": "success", "chat": item}

@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: str, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
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
    
    print(f"Items: {items}")
    
    if not items:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return items[0]

@app.post("/api/chats/new")
def new_chat(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Generate a new chat ID
    chat_id = str(datetime.datetime.utcnow().timestamp())
    
    # Store the new chat with an empty message list
    store_user_chat(user_id, chat_id, [])
    
    return RedirectResponse(f"http://localhost:3000/chat/{chat_id}", status_code=302)

@app.post("/api/chat")
def chat(data: ChatRequest, authorization: str = Header(None)):
    try:
        print("Chat endpoint called")
        user_id = get_user_id_from_token(authorization)
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized access")
        
        print(f"Data received: {data}")
        user_message = data.message
        chat_id = data.chat_id
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        if not chat_id:
            raise HTTPException(status_code=400, detail="No chat_id provided")
        
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
            print(f"Error fetching chat history: {e}")
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
        
        print(f"user_message: {user_message}")
        print(f"chat_id: {chat_id}")
        
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
        
        # Update chat history with new messages - matching Flask logic exactly
        index = 2
        chat_history.append({
            "id": str(index + 1),
            "sender": "user",
            "content": user_message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
        chat_history.append({
            "id": str(index + 2),
            "sender": "bot", 
            "content": assistant_response,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "references": references
        })
        
        # Save updated chat history to Cosmos DB
        try:
            store_user_chat(user_id, chat_id, chat_history)
        except Exception as e:
            print(f"Error saving chat history: {e}")
            # Continue anyway - don't fail the request if save fails
        
        return {
            "text": assistant_response,
            "references": references,
            "chat_id": chat_id
        }
        
    except Exception as e:
        print(f"Error in chat function: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)