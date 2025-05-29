import './Header.css';
import { useNavigate, useLocation } from 'react-router-dom';
import { logout } from '../../services/apiService';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/logout');
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  // Check if we're on upload page for full-width styling
  const isUploadPage = location.pathname === '/upload';

  return (
    <header className={`app-header ${isUploadPage ? 'fullwidth' : ''}`}>
      <div className="header-content">
        <div className="logo" onClick={() => handleNavigation('/chat')}>
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="6" fill="#0078D4"/>
            <path d="M22 12C22 14.2 20.2 16 18 16H9V12C9 9.8 10.8 8 13 8C15.2 8 17 9.8 17 12H22Z" fill="white"/>
            <path d="M23 16V20C23 22.2 21.2 24 19 24H10V20C10 17.8 11.8 16 14 16H23Z" fill="white"/>
          </svg>
          <h1>AzDocs-GPT</h1>
        </div>

        <nav className="header-nav">
          <button 
            className={`nav-button ${isActive('/chat') || isActive('/') ? 'active' : ''}`}
            onClick={() => handleNavigation('/chat')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4C22,2.89 21.1,2 20,2Z" />
            </svg>
            <span>Chat</span>
          </button>
          
          <button 
            className={`nav-button ${isActive('/upload') ? 'active' : ''}`}
            onClick={() => handleNavigation('/upload')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>
            <span>Upload</span>
          </button>
        </nav>

        <button className="logout-button" onClick={handleLogout}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16,17V14H9V10H16V7L21,12L16,17M14,2A2,2 0 0,1 16,4V6H14V4H5V20H14V18H16V20A2,2 0 0,1 14,22H5A2,2 0 0,1 3,20V4A2,2 0 0,1 5,2H14Z" />
          </svg>
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};

export default Header;