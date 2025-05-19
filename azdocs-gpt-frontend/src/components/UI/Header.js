import './Header.css';
import { useNavigate } from 'react-router-dom';
import { logout } from '../../services/apiService';

const Header = () => {

  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/logout'); // redirect to login or home page
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="6" fill="#0078D4"/>
            <path d="M22 12C22 14.2 20.2 16 18 16H9V12C9 9.8 10.8 8 13 8C15.2 8 17 9.8 17 12H22Z" fill="white"/>
            <path d="M23 16V20C23 22.2 21.2 24 19 24H10V20C10 17.8 11.8 16 14 16H23Z" fill="white"/>
          </svg>
          <h1>AzDocs-GPT</h1>
        </div>

        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
};

export default Header;
