import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, userType }) => {
  const { currentUser, loading } = useContext(AuthContext);
  const location = useLocation();

  if (loading) {
    // Show loading spinner or placeholder while checking authentication
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not logged in, redirect to the appropriate auth page
  if (!currentUser || !currentUser.isAuthenticated) {
    const redirectPath = location.pathname.includes('/teachers') 
      ? '/teachers/auth' 
      : '/student/auth';
      
    return <Navigate to={redirectPath} state={{ from: location }} replace />;
  }

  // If a role is required, check if the user has the right role
  if (userType && currentUser.userType !== userType) {
    // Redirect to the appropriate dashboard if they have the wrong role
    const redirectPath = currentUser.userType === 'teacher' 
      ? '/teachers/dashboard' 
      : '/student/dashboard';
      
    return <Navigate to={redirectPath} replace />;
  }

  // If authenticated and has the proper role, render the protected component
  return children;
};

export default ProtectedRoute; 