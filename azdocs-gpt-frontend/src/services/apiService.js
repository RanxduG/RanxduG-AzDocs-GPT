// Update the apiService.js file to include authentication related functions

// Replace these with your actual API endpoints
const API_URL = 'http://localhost:5000/';

// Authentication functions
export const login = async (credentials) => {
  try {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Login failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Login error:', error);
    
    // For development/testing purposes, return mock data when the API is not available
    if (!window.location.hostname.includes('localhost')) {
      throw error;
    }
    
    console.log('Using mock login response for development');
    // Mock successful login response for development
    return {
      token: 'mock-jwt-token',
      user: {
        id: 1,
        username: credentials.username,
        email: `${credentials.username}@example.com`,
        name: credentials.username,
      }
    };
  }
};

export const register = async (userData) => {
  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
  // Additional cleanup if needed
};

export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

export const isAuthenticated = () => {
  return !!getAuthToken();
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    return JSON.parse(userStr);
  }
  return null;
};

// Add authentication to your API requests
const authHeader = () => {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// Chat history related functions
export const mockChatHistory = [
  {
    id: 1,
    title: 'Azure VM Deployment',
    messages: [
      { id: 1, text: 'What is Azure?', sender: 'user' },
      { 
        id: 2, 
        text: 'Azure is a cloud computing service created by Microsoft. It offers a wide range of cloud services, including those for computing, analytics, storage, and networking. Users can pick and choose from these services to develop and scale new applications, or run existing applications in the public cloud.', 
        sender: 'bot', 
        references: [
          {
            index: 0,
            reference: {
              title: "What is Azure?",
              content: "Azure is Microsoft's cloud computing platform. It provides a range of cloud services for building, testing, deploying, and managing applications and services through Microsoft-managed data centers."
            }
          },
          {
            index: 1,
            reference: {
              title: "Azure Services Overview",
              content: "Microsoft Azure offers Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS) solutions across various domains including compute, analytics, storage, and networking."
            }
          }
        ]
      },
    ],
  },
  {
    id: 2,
    title: 'Azure Storage Services',
    messages: [
      { id: 1, text: 'How to create an Azure VM?', sender: 'user' },
      { 
        id: 2, 
        text: 'You can create an Azure VM using either the Azure portal, Azure CLI, Azure PowerShell, or ARM templates. Here are the basic steps via the Azure portal:\n\n1. Sign in to the Azure portal\n2. Click "Create a resource" and search for "Virtual Machine"\n3. Fill in the required fields (subscription, resource group, VM name, region, etc.)\n4. Select your VM image and size\n5. Configure networking, management, and advanced settings\n6. Review and create the VM', 
        sender: 'bot',
        references: [
          {
            index: 0,
            reference: {
              title: "Create an Azure VM",
              content: "To create a virtual machine in Azure, you can use the Azure portal, CLI, PowerShell, or ARM templates. The process involves specifying resource groups, regions, VM sizes, and networking configurations."
            }
          },
          {
            index: 1,
            reference: {
              title: "Azure VM Best Practices",
              content: "When creating Azure VMs, consider using managed disks, setting up proper backup solutions, and implementing appropriate security measures like Network Security Groups."
            }
          }
        ]
      }
    ],
  },
  {
    id: 3,
    title: 'Azure Networking',
    messages: [
      { id: 1, text: 'What is Azure Virtual Network?', sender: 'user' },
      { 
        id: 2, 
        text: 'Azure Virtual Network (VNet) is the fundamental building block for your private network in Azure. VNet enables many types of Azure resources, such as Azure Virtual Machines (VM), to securely communicate with each other, the internet, and on-premises networks. VNet is similar to a traditional network that you would operate in your own data center, but brings additional benefits of Azure\'s infrastructure such as scale, availability, and isolation.', 
        sender: 'bot',
        references: [
          {
            index: 0,
            reference: {
              title: "Azure Virtual Networks",
              content: "Azure Virtual Networks provide an isolated and secure environment to run your virtual machines and applications. They enable Azure resources to securely communicate with each other, the internet, and on-premises networks."
            }
          }
        ]
      }
    ],
  },
  {
    id: 4,
    title: 'Azure Security Basics',
    messages: [
      { id: 1, text: 'What is Azure Security Center?', sender: 'user' },
      { 
        id: 2, 
        text: 'Azure Security Center is now part of Microsoft Defender for Cloud. It\'s a unified infrastructure security management system that strengthens the security posture of your data centers and provides advanced threat protection across your hybrid workloads in the cloud and on-premises. Defender for Cloud provides security recommendations and threat detection capabilities to help you protect your Azure and non-Azure resources.', 
        sender: 'bot',
        references: [
          {
            index: 0,
            reference: {
              title: "Microsoft Defender for Cloud",
              content: "Microsoft Defender for Cloud (formerly Azure Security Center) is a unified security management system that strengthens the security posture of your cloud resources and provides advanced threat protection."
            }
          },
          {
            index: 1,
            reference: {
              title: "Cloud Security Best Practices",
              content: "Implementing least privilege access, regular security assessments, and enabling just-in-time VM access are recommended practices when using Microsoft Defender for Cloud."
            }
          }
        ]
      }
    ],
  }
];

export const sendMessage = async (message) => {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(), // Add authentication header
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    // Return a mock response for testing when API is not available
    return {
      text: "This is a mock response since the API is not available. In production, this would be a real response from your backend.",
      references: [
        {
          index: 0,
          reference: {
            title: "Mock Reference",
            content: "This is a mock reference to demonstrate the functionality."
          }
        }
      ]
    };
  }
};

export const getChatHistory = async (chatId) => {
  try {
    // In a real app, add authentication headers
    const headers = {
      'Content-Type': 'application/json',
      ...authHeader(), // Add authentication header
    };
    
    // For mock data during development
    const chatHistory = mockChatHistory.find(chat => chat.id === parseInt(chatId));
    
    // Return a Promise to simulate async behavior
    return new Promise((resolve) => {
      setTimeout(() => {
        if (chatHistory) {
          resolve(chatHistory.messages);
        } else {
          resolve([]);
        }
      }, 300); // Small delay to simulate API call
    });

    // In a real application, you would fetch this from your backend
    // const response = await fetch(`${API_URL}/chat/${chatId}`, {
    //   method: 'GET',
    //   headers: headers,
    // });
    //
    // if (!response.ok) {
    //   throw new Error(`API error: ${response.status}`);
    // }
    //
    // return await response.json();
  } catch (error) {
    console.error('Error fetching chat history:', error);
    throw error;
  }
};

export const getUserChats = async () => {
  try {
    // In a real app, this would call your backend API
    // const response = await fetch(`${API_URL}/chats`, {
    //   method: 'GET',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     ...authHeader(),
    //   },
    // });
    //
    // if (!response.ok) {
    //   throw new Error(`API error: ${response.status}`);
    // }
    //
    // return await response.json();
    
    // For development, return mock data
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(mockChatHistory);
      }, 300);
    });
  } catch (error) {
    console.error('Error fetching user chats:', error);
    return [];
  }
};

export const createNewChat = async (title = 'New Chat') => {
  try {
    // In a real app, this would call your backend API
    // const response = await fetch(`${API_URL}/chats`, {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     ...authHeader(),
    //   },
    //   body: JSON.stringify({ title }),
    // });
    //
    // if (!response.ok) {
    //   throw new Error(`API error: ${response.status}`);
    // }
    //
    // return await response.json();
    
    // For development, return mock data
    const newChatId = Date.now();
    return {
      id: newChatId,
      title: title,
      messages: []
    };
  } catch (error) {
    console.error('Error creating new chat:', error);
    throw error;
  }
};