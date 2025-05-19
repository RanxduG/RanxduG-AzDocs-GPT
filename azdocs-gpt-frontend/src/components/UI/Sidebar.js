import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import { mockChatHistory } from '../../services/apiService'; // Mock data for chat history

const Sidebar = ({ onSelectChat, onNewChat }) => {
  const [chats, setChats] = useState([]);
  
  const [activeChat, setActiveChat] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleChatSelect = (chatId) => {
    setActiveChat(chatId);
    onSelectChat(chatId);
  };

  const handleNewChat = () => {
    const newChatId = Date.now();
    const newChat = {
      id: newChatId,
      title: `New Chat ${chats.length + 1}`,
    };
    
    setChats([...chats, newChat]);
    setActiveChat(newChatId);
    onNewChat(newChatId);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  // Load initial chat history
  useEffect(() => {
    // In a real app, you would fetch this data from a backend
    setChats(mockChatHistory);
  }, []);

  return (
    <>
      <div className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>AzDocs-GPT</h2>
          <button className="toggle-button" onClick={toggleSidebar}>
            {isSidebarOpen ? '←' : '→'}
          </button>
        </div>
        
        <button className="new-chat-button" onClick={handleNewChat}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8 0a1 1 0 0 1 1 1v6h6a1 1 0 1 1 0 2H9v6a1 1 0 1 1-2 0V9H1a1 1 0 0 1 0-2h6V1a1 1 0 0 1 1-1z"/>
          </svg>
          New Chat
        </button>
        
        <div className="chats-list">
          {chats.map(chat => (
            <div 
              key={chat.id} 
              className={`chat-item ${activeChat === chat.id ? 'active' : ''}`}
              onClick={() => handleChatSelect(chat.id)}
            >
              <span className="chat-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
                  <path d="M2.165 15.803l.02-.004c1.83-.363 2.948-.842 3.468-1.105A9.06 9.06 0 0 0 8 15c4.418 0 8-3.134 8-7s-3.582-7-8-7-8 3.134-8 7c0 1.76.743 3.37 1.97 4.6a10.437 10.437 0 0 1-.524 2.318l-.003.011a10.722 10.722 0 0 1-.244.637c-.079.186.074.394.273.362a21.673 21.673 0 0 0 .693-.125zm.8-3.108a1 1 0 0 0-.287-.801C1.618 10.83 1 9.468 1 8c0-3.192 3.004-6 7-6s7 2.808 7 6c0 3.193-3.004 6-7 6a8.06 8.06 0 0 1-2.088-.272 1 1 0 0 0-.711.074c-.387.196-1.24.57-2.634.893a10.97 10.97 0 0 0 .398-2z"/>
                </svg>
              </span>
              <span className="chat-title">{chat.title}</span>
            </div>
          ))}
        </div>
      </div>
      
      {!isSidebarOpen && (
        <button className="sidebar-toggle-button" onClick={toggleSidebar}>
          ☰
        </button>
      )}
    </>
  );
};

export default Sidebar;