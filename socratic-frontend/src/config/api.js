// API configuration
const API_URL = process.env.REACT_APP_API_URL || 
  process.env.NODE_ENV === 'production' 
    ? 'https://socratic-production.up.railway.app'  // Replace with your actual Railway URL
    : 'http://Matthews-MacBook-Pro.local:8000';

export default API_URL; 