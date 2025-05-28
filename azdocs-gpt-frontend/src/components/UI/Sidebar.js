import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import { getUserChats } from '../../services/apiService'; // Mock data for chat history

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

useEffect(() => {
  const fetchChats = async () => {
    try {
      const chatData = await getUserChats();  // ✅ Await the response
      console.log('Fetched chats:', chatData);
      setChats(chatData);                     // ✅ Now it's actual data
    } catch (error) {
      console.error('Failed to load chats:', error);
    }
  };

  fetchChats(); // Call the async inner function
}, []); // ✅ empty dependency array


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
          {Array.isArray(chats) && chats.length > 0 ? (
            chats.map(chat => (
              <div key={chat.id} className={`chat-item ${activeChat === chat.id ? 'active' : ''}`} onClick={() => handleChatSelect(chat.id)}>
                <span className="chat-icon">...</span>
                <span className="chat-title">{chat.title}</span>
              </div>
            ))
          ) : (
            <p className="empty-chats">No chats found.</p>
          )}
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