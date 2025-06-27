import React, { useContext, useState, useEffect, useRef } from 'react';
import { TfiYoutube } from "react-icons/tfi";
import { MdDashboard } from "react-icons/md";
import { GiBrain } from "react-icons/gi";
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import API_URL from '../config/api';
import '../styles/StudentHomePage.css';

function StudentHomePage() {
  const { currentUser, logout, setCurrentUser } = useContext(AuthContext);
  const [isUpdatingGrade, setIsUpdatingGrade] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef(null);

  const handleLogout = () => {
    logout();
  };

  const handleGradeUpdate = async (newGrade) => {
    setIsUpdatingGrade(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/student/profile`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ grade: newGrade }),
      });

      if (!response.ok) {
        throw new Error('Failed to update grade');
      }

      const data = await response.json();
      
      // Update the current user in context
      setCurrentUser(prev => ({
        ...prev,
        grade: data.user.grade
      }));

      setShowProfileMenu(false);
      
    } catch (error) {
      console.error('Error updating grade:', error);
      alert('Failed to update grade. Please try again.');
    } finally {
      setIsUpdatingGrade(false);
    }
  };

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Get user initials for avatar
  const getUserInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="student-home-container">
      {/* Header */}
      <div className="student-home-header">
        <div className="header-content">
          <div className="header-main">
            <h1>Welcome back, {currentUser?.name || 'Student'}!</h1>
            <p>What would you like to do today?</p>
          </div>
          
          <div className="header-actions">
            {/* Profile Avatar */}
            <div className="profile-menu-container" ref={profileMenuRef}>
              <button 
                className="profile-avatar"
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                title={currentUser?.name || 'User Profile'}
              >
                {getUserInitials(currentUser?.name)}
              </button>
              
              {showProfileMenu && (
                <div className="profile-dropdown">
                  <div className="profile-info">
                    <div className="profile-avatar-large">
                      {getUserInitials(currentUser?.name)}
                    </div>
                    <div className="profile-details">
                      <h4>{currentUser?.name || 'Student'}</h4>
                      <p>{currentUser?.email}</p>
                    </div>
                  </div>
                  
                  <div className="profile-divider"></div>
                  
                  <div className="profile-section">
                    <h5>Grade Level</h5>
                    <div className="grade-options">
                      {['9', '10', '11', '12'].map(grade => (
                        <button
                          key={grade}
                          className={`grade-option ${currentUser?.grade === grade ? 'active' : ''}`}
                          onClick={() => handleGradeUpdate(grade)}
                          disabled={isUpdatingGrade}
                        >
                          <span>Grade {grade}</span>
                          {currentUser?.grade === grade && <span className="checkmark">✓</span>}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="profile-divider"></div>
                  
                  <button className="profile-menu-item logout-item" onClick={handleLogout}>
                    <span>Sign out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Navigation Options */}
      <div className="navigation-options">
        <Link to="/student/dashboard" className="nav-option">
          <div className="nav-option-icon"><MdDashboard /></div>
          <h2>Dashboard</h2>
          <p>View your progress, knowledge map, and performance analytics</p>
        </Link>

        <Link to="/student/learning-modules" className="nav-option">
          <div className="nav-option-icon"><TfiYoutube /></div>
          <h2>YouTube Assisted Learning</h2>
          <p>Watch YouTube videos with AI-powered assistance and interactive learning</p>
        </Link>

        <Link to="/student/dynamic-learning" className="nav-option">
          <div className="nav-option-icon"><GiBrain /></div>
          <h2>Dynamic Learning</h2>
          <p>Adaptive AI-powered learning experiences tailored to your progress</p>
        </Link>


      </div>
    </div>
  );
}

export default StudentHomePage; 