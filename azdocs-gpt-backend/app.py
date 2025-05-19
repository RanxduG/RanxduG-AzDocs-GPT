# app.py - Flask backend for AzDocs-GPT
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import msal
import jwt
import datetime


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-key-in-prod")
CORS(app)  # Enable CORS for all routes

# Azure Configuration
load_dotenv()

AZURE_AD_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
AZURE_AD_CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
AZURE_AD_CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
REDIRECT_PATH = "/getAToken"
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = [os.getenv("AZURE_AD_SCOPE")]
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}"

# Initialize Azure services
azure_credential = DefaultAzureCredential()

openai_client = AzureOpenAI(
    api_version="2023-03-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_ad_token_provider=get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
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

@app.route("/login")
def login():
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
        print(f"User authenticated: {user_info}")

        # ✅ Create your own JWT to send to frontend
        token_payload = {
            "sub": user_info.get("oid"),  # Azure AD Object ID
            "email": user_info.get("preferred_username"),
            "name": user_info.get("name"),
            "roles": user_info.get("roles", []),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        jwt_token = jwt.encode(token_payload, app.secret_key, algorithm="HS256")

        # ✅ Redirect to frontend with token in query param
        return redirect(f"http://localhost:3000/auth/callback?token={jwt_token}")

    return f"Login failed: {result.get('error_description')}", 400

@app.route("/logout")
def logout():
    session.clear()
    return redirect(f"{AZURE_AD_AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:5000/")



# API route for chat
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Check for authorization token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized access"}), 401
        
        token = auth_header.split(' ')[1]
        # In a production app, you would validate the token here
        
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
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
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        print(f"user_message: {user_message}")
        
        # Step 1: Generate search query
        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT, 
            messages=messages, 
            tools=tools
            # parallel_tool_calls=False
        )
        # Check if the model wants to search
        if completion.choices[0].finish_reason == "tool_calls":
            for call in completion.choices[0].message.tool_calls:
                if call.function.name == "search":
                    import json
                    query = json.loads(call.function.arguments)["query"]
                    
                    # Step 2: Perform search
                    search_content, references = search_azure(query)

                    # Step 3: Generate answer based on search results
                    answer_messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": "I'll search for information to help answer your question.", "tool_calls": [call]},
                        {"role": "tool", "tool_call_id": call.id, "content": search_content}
                    ]

                    
                    answer_completion = openai_client.chat.completions.create(
                        model=AZURE_OPENAI_DEPLOYMENT,
                        messages=answer_messages
                    )
                    
                    return jsonify({
                        "text": answer_completion.choices[0].message.content,
                        "references": references
                    })
        
        # Fallback if no search was performed
        return jsonify({
            "text": "I'm not sure how to answer your question without searching for more information.",
            "references": []
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# API route for /
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the AzDocs-GPT API!"})


if __name__ == '__main__':
    app.run(debug=True)