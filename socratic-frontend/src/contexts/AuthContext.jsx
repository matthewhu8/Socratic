import React, { createContext, useState, useEffect } from 'react';
import API_URL from '../config/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch user profile after token validation
  const fetchUserProfile = async (accessToken, userType) => {
    try {
      const endpoint = userType === 'student' ? '/api/auth/student/me' : '/api/auth/teacher/me';
      const response = await fetch(`${API_URL}${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        return {
          id: userData.id,              // <-- This is the real database ID
          name: userData.name,
          email: userData.email,
          userType: userType,
          isAuthenticated: true,
          // Include other user-specific data
          ...(userType === 'student' ? { grade: userData.grade } : { subject: userData.subject, school: userData.school })
        };
      }
      throw new Error('Failed to fetch user profile');
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('accessToken');  // Fixed token name
      const userType = localStorage.getItem('userType');
      
      if (accessToken && userType) {
        try {
          // Fetch real user profile with database ID
          const userData = await fetchUserProfile(accessToken, userType);
          if (userData) {
            setCurrentUser(userData);
          } else {
            // If profile fetch fails, clear tokens
            logout();
          }
        } catch (error) {
          console.error('Auth check error:', error);
          logout();
        }
      }
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const refreshToken = async () => {
    // For now, just implement a simplified version
    return false;
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userType');
    localStorage.removeItem('userName');
    setCurrentUser(null);
  };

  return (
    <AuthContext.Provider 
      value={{ 
        currentUser, 
        loading, 
        logout, 
        refreshToken, 
        setCurrentUser 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider; 