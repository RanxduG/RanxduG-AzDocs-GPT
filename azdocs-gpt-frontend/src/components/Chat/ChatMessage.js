import React, { useState } from 'react';
import './ChatMessage.css';
import GroundingReferences from './GroundingReferences';

// Function to convert markdown to HTML (very simplified version)
const convertMarkdownToHtml = (text) => {
  // Handle code blocks with ```
  let html = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  
  // Handle inline code with `
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Handle bold with ** or __
  html = html.replace(/(\*\*|__)(.*?)\1/g, '<strong>$2</strong>');
  
  // Handle italics with * or _
  html = html.replace(/(\*|_)(.*?)\1/g, '<em>$2</em>');
  
  // Handle links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // Handle headers
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
  
  // Handle paragraphs (simplistic)
  html = html.split('\n\n').map(p => `<p>${p}</p>`).join('');
  
  return html;
};

const ChatMessage = ({ message }) => {
  const [referencesExpanded, setReferencesExpanded] = useState(false);
  
  const toggleReferences = () => {
    setReferencesExpanded(!referencesExpanded);
  };
  
  const isBot = message.sender === 'bot';
  
  return (
    <div className={`message-container ${isBot ? 'bot-message' : 'user-message'}`}>
      <div className="message-header">
        <div className="message-avatar">
          {isBot ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="24" height="24" rx="12" fill="#0078D4"/>
              <path d="M16.5 8.5C16.5 10.7 14.7 12.5 12.5 12.5H7.5V8.5C7.5 6.3 9.3 4.5 11.5 4.5C13.7 4.5 15.5 6.3 15.5 8.5H16.5Z" fill="white"/>
              <path d="M17.5 11.5V15.5C17.5 17.7 15.7 19.5 13.5 19.5H8.5V15.5C8.5 13.3 10.3 11.5 12.5 11.5H17.5Z" fill="white"/>
            </svg>
          ) : (
            <div className="user-icon">U</div>
          )}
        </div>
        <div className="message-sender">
          {isBot ? 'AzDocs-GPT' : 'You'}
        </div>
      </div>
      
      <div 
        className={`message-content ${message.isError ? 'error-message' : ''}`}
        dangerouslySetInnerHTML={{ __html: isBot ? convertMarkdownToHtml(message.text) : message.text }}
      />
      
      {isBot && message.references && message.references.length > 0 && (
        <div className="references-container">
          <button 
            className="references-toggle" 
            onClick={toggleReferences}
          >
            {referencesExpanded ? 'Hide References' : 'Show References'} ({message.references.length})
          </button>
          
          {referencesExpanded && (
            <GroundingReferences references={message.references} />
          )}
        </div>
      )}
    </div>
  );
};

export default ChatMessage;