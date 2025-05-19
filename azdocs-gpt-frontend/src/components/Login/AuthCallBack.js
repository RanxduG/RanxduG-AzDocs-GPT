// src/components/Login/AuthCallback.jsx
import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode'; // ✅ Correct


const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const token = queryParams.get('token');

    if (token) {
      // ✅ Decode the token
      const decoded = jwtDecode(token);
      console.log('Decoded JWT:', decoded);

      // Save token and user info in localStorage
      localStorage.setItem('authToken', token);
      localStorage.setItem('userInfo', JSON.stringify(decoded));

      // Redirect to chat
      navigate('/chat');
    } else {
      // Handle error
      navigate('/login');
    }
  }, [location, navigate]);

  return <div>Authenticating...</div>;
};

export default AuthCallback;
