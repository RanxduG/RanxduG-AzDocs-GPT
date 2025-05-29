import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import UploadPage from './pages/UploadPage';
import AuthCallback from './components/Login/AuthCallBack';

// Protected route component to handle authentication
const ProtectedRoute = ({ children }) => {
  // Check if user is authenticated - looking for both possible token names
  const isAuthenticated = localStorage.getItem('authToken') || localStorage.getItem('token');
  
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
          {/* Default route redirects to chat for authenticated users, login for others */}
          <Route 
            path="/" 
            element={
              localStorage.getItem('authToken') || localStorage.getItem('token') 
                ? <Navigate to="/chat" replace /> 
                : <Navigate to="/login" replace />
            } 
          />
          
          {/* Login route */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Auth callback route */}
          <Route path="/auth/callback" element={<AuthCallback />} />
          
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
          
          {/* Protected upload route */}
          <Route 
            path="/upload" 
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Logout route - clears auth and redirects to login */}
          <Route 
            path="/logout" 
            element={
              <Navigate 
                to="/login" 
                replace 
                state={{ message: 'You have been logged out successfully' }}
              />
            } 
          />
          
          {/* Forgot password route (placeholder) */}
          <Route path="/forgot-password" element={<div>Forgot Password Page</div>} />
          
          {/* Catch-all for undefined routes - redirect based on auth status */}
          <Route 
            path="*" 
            element={
              localStorage.getItem('authToken') || localStorage.getItem('token')
                ? <Navigate to="/chat" replace />
                : <Navigate to="/login" replace />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;