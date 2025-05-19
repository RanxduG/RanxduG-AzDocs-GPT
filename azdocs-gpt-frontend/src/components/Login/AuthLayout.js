import React from 'react';
import './AuthLayout.css';

const AuthLayout = ({ children }) => {
  return (
    <div className="auth-layout">
      <div className="auth-hero">
        <div className="hero-content">
          <div className="hero-logo">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="12" fill="#0078D4"/>
              <path d="M33 17C33 21.4 29.4 25 25 25H15V17C15 12.6 18.6 9 23 9C27.4 9 31 12.6 31 17H33Z" fill="white"/>
              <path d="M35 23V31C35 35.4 31.4 39 27 39H17V31C17 26.6 20.6 23 25 23H35Z" fill="white"/>
            </svg>
          </div>
          <h1>AzDocs-GPT</h1>
          <p>Your intelligent Azure documentation assistant powered by AI</p>
          <div className="hero-features">
            <div className="feature">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              <span>Get accurate Azure documentation in seconds</span>
            </div>
            <div className="feature">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              <span>Chat with AI about Azure solutions</span>
            </div>
            <div className="feature">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              <span>Stay updated with latest Azure features</span>
            </div>
          </div>
        </div>
      </div>
      <div className="auth-form-container">
        {children}
      </div>
    </div>
  );
};

export default AuthLayout;