import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import LoadingDots from '../UI/LoadingDots';
import { sendMessage, getChatHistory } from '../../services/apiService';


const Chat = ({ chatId }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Reset messages when chatId changes
  useEffect(() => {
    const loadChatHistory = async () => {
      if (chatId) {
        try {
          setIsLoading(true);
          const chatHistory = await getChatHistory(chatId);
          if (chatHistory) {
            setMessages(chatHistory);
          } else {
            setMessages([]);
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
          setMessages([]);
        } finally {
          setIsLoading(false);
        }
      } else {
        // Reset messages if no chatId
        setMessages([]);
      }
    };

    loadChatHistory();
  }, [chatId]);

  const handleSendMessage = async (message) => {
    if (!chatId) return; // Don't process if no active chat
    
    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsLoading(true);
    
    try {
      // Call API service
      const response = await sendMessage(chatId, message);
      
      // Add bot message to chat
      const botMessage = {
        id: Date.now() + 1,
        text: response.text,
        sender: 'bot',
        references: response.references
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error processing message:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, there was an error processing your request. Please try again later.',
        sender: 'bot',
        isError: true
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && !isLoading && (
          <div className="welcome-message">
            <h2>Welcome to AzDocs-GPT</h2>
            <p>Ask me anything about Azure services and documentation.</p>
          </div>
        )}
        
        {Array.isArray(messages) && messages.map(message => (
          <ChatMessage 
            key={message.id} 
            message={message}
          />
        ))}
        
        {isLoading && (
          <div className="loading-container">
            <LoadingDots />
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading || !chatId} />
    </div>
  );
};

export default Chat;