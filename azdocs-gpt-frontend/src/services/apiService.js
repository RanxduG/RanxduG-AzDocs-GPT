// const API_URL = 'http://localhost:5000';
const API_URL = 'https://azdocsgpt-b4bqhrg2gjh2byhc.southeastasia-01.azurewebsites.net';

// Authentication
export const login = async (credentials) => {
  try {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Registration failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
};

export const getAuthToken = () => localStorage.getItem('authToken');

export const isAuthenticated = () => !!getAuthToken();

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

const authHeader = () => {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// ======= Chat APIs =======

export const sendMessage = async (chatId, message) => {
  try {
    
    console.log('Sending message:', message);
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(),
      },
      body: JSON.stringify({ chat_id: chatId, message }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

export const getChatHistory = async (chatId) => {
  try {
    const response = await fetch(`${API_URL}/api/chats/${chatId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(),
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const chat = await response.json();
    return chat.messages || [];
  } catch (error) {
    console.error('Error fetching chat history:', error);
    return [];
  }
};

// Fixed getUserChats function
export const getUserChats = async () => {
  try {
    const response = await fetch(`${API_URL}/api/chats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(),
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    // Parse and return the JSON data instead of the raw response
    return await response.json();
  } catch (error) {
    console.error('Error fetching user chats:', error);
    return [];
  }
};

export const createNewChat = async (title = 'New Chat') => {
  try {
    const response = await fetch(`${API_URL}/api/chats/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(),
      },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating new chat:', error);
    throw error;
  }
};