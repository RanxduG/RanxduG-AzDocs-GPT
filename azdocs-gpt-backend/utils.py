# utils.py - Utility functions
from flask import request
import datetime
from typing import Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from services import AuthService

def get_user_id_from_token(auth_service: 'AuthService') -> Optional[str]:
    """Extract user ID from JWT token in Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    decoded = auth_service.decode_jwt_token(token)
    return decoded.get("sub") if decoded else None

def generate_chat_id() -> str:
    """Generate a unique chat ID"""
    return str(datetime.datetime.utcnow().timestamp())

def format_chat_response(chat_data: Dict) -> Dict:
    """Format chat data for API response"""
    return {
        "title": chat_data["title"],
        "id": chat_data["id"],
        "messages": chat_data["messages"],
        "lastUpdated": chat_data["lastUpdated"]
    }