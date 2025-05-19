import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/UI/Header';
import Sidebar from '../components/UI/Sidebar';
import Chat from '../components/Chat/Chat';
import './CSS/ChatPage.css';

const ChatPage = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [activeChat, setActiveChat] = useState(chatId || null);
  const [chatHistory, setChatHistory] = useState({});
  const [user, setUser] = useState(null);
  
    useEffect(() => {
        const userData = localStorage.getItem('userInfo');
        if (userData) {
        setUser(JSON.parse(userData));
        }
    }, []);

  // Load user data when component mounts
  useEffect(() => {    
    // If there's a chatId in the URL, set it as active
    if (chatId) {
      setActiveChat(chatId);
    }
  }, [chatId]);

  // Handle chat selection from sidebar
  const handleSelectChat = (selectedChatId) => {
    setActiveChat(selectedChatId);
    navigate(`/chat/${selectedChatId}`);
    // Here you would typically load the chat history for this chat
  };

  // Handle creating a new chat
  const handleNewChat = (newChatId) => {
    setActiveChat(newChatId);
    setChatHistory({
      ...chatHistory,
      [newChatId]: [] // Initialize empty chat history
    });
    navigate(`/chat/${newChatId}`);
  };

  return (
    <div className="chat-page">
      <Sidebar 
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        activeChat={activeChat}
        user={user}
      />
      <div className="main-content">
        <Header 
          user={user}
        />
        <div className="chat-container">
          {activeChat ? (
            <Chat 
              chatId={activeChat}
              chatHistory={chatHistory[activeChat] || []}
              setChatHistory={(messages) => {
                setChatHistory({
                  ...chatHistory,
                  [activeChat]: messages
                });
              }}
            />
          ) : (
            <div className="no-chat-selected">
                {user ? (
                    <>
                    <h3>Hi {user.name}</h3> {/* or user.name, depending on your JWT claims */}
                    <h3>Welcome to the Chat App</h3>
                    </>
                ) : (
                    <h3>Loading user info...</h3>
                )}
                <p>Select a chat from the sidebar or start a new conversation</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
