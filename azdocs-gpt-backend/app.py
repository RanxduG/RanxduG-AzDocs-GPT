# app.py - Main Flask application
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import logging
import sys
import datetime
from typing import List

# Import our modules
from config import get_config
from models import CosmosDBManager
from services import AzureSearchService, OpenAIService, AuthService
from utils import get_user_id_from_token, generate_chat_id, format_chat_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Initialize CORS
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    
    # Initialize services
    db_manager = CosmosDBManager(config)
    search_service = AzureSearchService(config)
    openai_service = OpenAIService(config)
    auth_service = AuthService(config)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500
    
    # Authentication routes
    @app.route("/login")
    def login():
        logger.info("Login endpoint called")
        auth_url = auth_service.get_authorization_url()
        return redirect(auth_url)
    
    @app.route(config.REDIRECT_PATH)
    def authorized():
        code = request.args.get("code")
        if not code:
            logger.warning("Authorization failed: No code provided")
            return jsonify({"error": "Authorization failed"}), 400
        
        try:
            result = auth_service.acquire_token_by_code(code)
            
            if "access_token" in result:
                user_info = result.get("id_token_claims")
                logger.info(f"User authenticated: {user_info.get('preferred_username')}")
                
                jwt_token = auth_service.create_jwt_token(user_info)
                return redirect(f"{config.FRONTEND_URL}/auth/callback?token={jwt_token}")
            
            error_desc = result.get('error_description', 'Unknown error')
            logger.error(f"Login failed: {error_desc}")
            return jsonify({"error": f"Login failed: {error_desc}"}), 400
            
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}")
            return jsonify({"error": "Authorization failed"}), 500
    
    @app.route("/logout")
    def logout():
        logout_url = f"{config.AZURE_AD_AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={config.REDIRECT_URI}"
        return redirect(logout_url)
    
    # Chat API routes
    @app.route('/api/chats', methods=['GET'])
    def get_chats():
        user_id = get_user_id_from_token(auth_service)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            chats = db_manager.get_user_chats(user_id)
            formatted_chats = [format_chat_response(chat) for chat in chats]
            return jsonify(formatted_chats)
            
        except Exception as e:
            logger.error(f"Error retrieving chats for user {user_id}: {str(e)}")
            return jsonify({"error": "Failed to retrieve chats"}), 500
    
    @app.route('/api/chats/<chat_id>', methods=['GET'])
    def get_chat(chat_id):
        user_id = get_user_id_from_token(auth_service)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            chat = db_manager.get_chat_by_id(user_id, chat_id)
            if not chat:
                return jsonify({"error": "Chat not found"}), 404
            
            return jsonify(chat)
            
        except Exception as e:
            logger.error(f"Error retrieving chat {chat_id}: {str(e)}")
            return jsonify({"error": "Failed to retrieve chat"}), 500
    
    @app.route('/api/chats/new', methods=['POST'])
    def new_chat():
        user_id = get_user_id_from_token(auth_service)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            chat_id = generate_chat_id()
            db_manager.store_user_chat(user_id, chat_id, "New Chat", [])
            return redirect(f"{config.FRONTEND_URL}/chat/{chat_id}", code=302)
            
        except Exception as e:
            logger.error(f"Error creating new chat: {str(e)}")
            return jsonify({"error": "Failed to create chat"}), 500
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        user_id = get_user_id_from_token(auth_service)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            user_message = data.get('message', '').strip()
            chat_id = data.get('chat_id', '').strip()
            
            if not user_message:
                return jsonify({"error": "No message provided"}), 400
            
            if not chat_id:
                return jsonify({"error": "No chat_id provided"}), 400
            
            logger.info(f"Processing chat message for user {user_id}, chat {chat_id}")
            
            # Get existing chat history
            existing_chat = db_manager.get_chat_by_id(user_id, chat_id)
            chat_history = existing_chat['messages'] if existing_chat else []
            
            # Build messages for OpenAI
            messages = [{"role": "system", "content": openai_service.system_prompt}]
            
            # Add chat history
            for msg in chat_history:
                role = "assistant" if msg.get("sender") == "bot" else "user"
                messages.append({"role": role, "content": msg.get("content", "")})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate search query
            query, tool_call = openai_service.generate_search_query(messages)
            
            assistant_response = ""
            references = []
            
            if query and tool_call:
                # Perform search
                search_content, references = search_service.search(query)
                
                # Generate answer with search results
                answer_messages = messages + [
                    {"role": "assistant", "content": "I'll search for information to help answer your question.", "tool_calls": [tool_call]},
                    {"role": "tool", "tool_call_id": tool_call.id, "content": search_content}
                ]
                
                assistant_response = openai_service.generate_answer(answer_messages)
            else:
                assistant_response = "I'm not sure how to answer your question without searching for more information."
            
            # Update chat history
            timestamp = datetime.datetime.utcnow().isoformat()
            next_id = len(chat_history) + 1
            
            chat_history.extend([
                {
                    "id": str(next_id),
                    "sender": "user",
                    "content": user_message,
                    "timestamp": timestamp
                },
                {
                    "id": str(next_id + 1),
                    "sender": "bot",
                    "content": assistant_response,
                    "timestamp": timestamp,
                    "references": references
                }
            ])
            
            # Determine chat name (use first user message if new chat)
            chat_name = existing_chat['title'] if existing_chat else user_message[:50]
            
            # Save to database
            db_manager.store_user_chat(user_id, chat_id, chat_name, chat_history)
            
            return jsonify({
                "text": assistant_response,
                "references": references,
                "chat_id": chat_id
            })
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"error": "Failed to process chat message"}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()})
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "message": "AzDocs-GPT API",
            "version": "1.0.0",
            "status": "running"
        })
    
    return app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    app.run(debug=False)