# models.py - Data models and database operations
from azure.cosmos import CosmosClient, PartitionKey
from typing import List, Dict, Optional
import datetime
import logging

logger = logging.getLogger(__name__)

class CosmosDBManager:
    """Manages Cosmos DB operations for chat data"""
    
    def __init__(self, config):
        self.client = CosmosClient(config.COSMOS_ENDPOINT, config.COSMOS_KEY)
        self.database = self.client.create_database_if_not_exists(id=config.COSMOS_DATABASE_NAME)
        self.container = self.database.create_container_if_not_exists(
            id=config.COSMOS_CONTAINER_NAME,
            partition_key=PartitionKey(path="/userId"),
            offer_throughput=config.COSMOS_THROUGHPUT
        )
    
    def store_user_chat(self, user_id: str, chat_id: str, chat_name: str, messages: List[Dict]) -> Dict:
        """Store or update a chat document for the user"""
        try:
            item = {
                "title": chat_name[:100],  # Limit title length
                "id": chat_id,
                "userId": user_id,
                "messages": messages,
                "lastUpdated": datetime.datetime.utcnow().isoformat()
            }
            self.container.upsert_item(item)
            logger.info(f"Chat saved successfully for user {user_id}, chat {chat_id}")
            return item
        except Exception as e:
            logger.error(f"Error storing chat for user {user_id}: {str(e)}")
            raise
    
    def get_user_chats(self, user_id: str) -> List[Dict]:
        """Retrieve all chat documents for a given user"""
        try:
            query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.lastUpdated DESC"
            parameters = [{"name": "@userId", "value": user_id}]
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            logger.info(f"Retrieved {len(items)} chats for user {user_id}")
            return items
        except Exception as e:
            logger.error(f"Error retrieving chats for user {user_id}: {str(e)}")
            raise
    
    def get_chat_by_id(self, user_id: str, chat_id: str) -> Optional[Dict]:
        """Get a specific chat by ID"""
        try:
            query = "SELECT * FROM c WHERE c.userId = @userId AND c.id = @chatId"
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@chatId", "value": chat_id}
            ]
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error retrieving chat {chat_id} for user {user_id}: {str(e)}")
            raise