// API configuration
const API_URL = process.env.REACT_APP_API_URL || 
  process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-url.up.railway.app'  // Replace with your actual Railway URL
    : 'http://localhost:8000';

export default API_URL; 