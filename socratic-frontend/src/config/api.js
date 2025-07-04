// API configuration
const API_URL = process.env.REACT_APP_API_URL || 
  process.env.NODE_ENV === 'production' 
    ? 'https://socratic-production.up.railway.app'  // Replace with your actual Railway URL
    : 'http://localhost:8000';

// Token refresh logic
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

export const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('refreshToken', data.refresh_token);
    
    return data.access_token;
  } catch (error) {
    // Clear tokens and redirect to login
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userType');
    window.location.href = '/student/auth';
    throw error;
  }
};

// Enhanced fetch with automatic token refresh
export const fetchWithAuth = async (url, options = {}) => {
  const makeRequest = async (accessToken) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`,
      },
    });
    
    return response;
  };

  let accessToken = localStorage.getItem('accessToken');
  if (!accessToken) {
    window.location.href = '/student/auth';
    throw new Error('No access token');
  }

  let response = await makeRequest(accessToken);

  // If we get a 401, try to refresh the token
  if (response.status === 401) {
    if (isRefreshing) {
      // Wait for the ongoing refresh to complete
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then(token => {
        return makeRequest(token);
      });
    }

    isRefreshing = true;

    try {
      const newToken = await refreshAccessToken();
      processQueue(null, newToken);
      isRefreshing = false;
      
      // Retry the original request with the new token
      response = await makeRequest(newToken);
    } catch (error) {
      processQueue(error, null);
      isRefreshing = false;
      throw error;
    }
  }

  return response;
};

export default API_URL; 