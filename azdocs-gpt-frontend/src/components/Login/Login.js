import React from 'react';
import './Login.css';

const Login = () => {
  const handleAzureLogin = () => {
    // Redirect to Flask backend's Azure AD login route
    console.log('Redirecting to Azure AD login...');
    window.location.href = 'https://azdocsgpt-b4bqhrg2gjh2byhc.southeastasia-01.azurewebsites.net/login'; // update to your backend URL if different
    // window.location.href = 'http://localhost:5000/login'; // update to your backend URL if different
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>AzDocs-GPT</h1>
          <p className="tagline">Your intelligent Azure documentation assistant</p>
        </div>

        <button 
          className="login-button" 
          onClick={handleAzureLogin}
        >
          Login with Azure Entra ID
        </button>
      </div>
    </div>
  );
};

export default Login;
