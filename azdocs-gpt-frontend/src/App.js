import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AuthCallback from './components/Login/AuthCallBack';

// Protected route component to handle authentication
const ProtectedRoute = ({ children }) => {
  // Check if user is authenticated
  const isAuthenticated = localStorage.getItem('authToken');
  
  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    console.log('User not authenticated, redirecting to login...');

    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          {/* Default route redirects to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Login route */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected chat route */}
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Specific chat ID route */}
          <Route 
            path="/chat/:chatId" 
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Forgot password route (placeholder) */}
          <Route path="/forgot-password" element={<div>Forgot Password Page</div>} />
          
          {/* Catch-all for undefined routes */}
          <Route path="*" element={<Navigate to="/login" replace />} />

          <Route path="/auth/callback" element={<AuthCallback />} />

        </Routes>
      </div>
    </Router>
  );
}

export default App;