import React, { useContext } from 'react';
import { TfiYoutube } from "react-icons/tfi";
import { MdDashboard } from "react-icons/md";
import { GiBrain } from "react-icons/gi";
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/StudentHomePage.css';

function StudentHomePage() {
  const { currentUser, logout } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="student-home-container">
      {/* Header */}
      <div className="student-home-header">
        <div className="header-content">
          <h1>Welcome back, {currentUser?.first_name || 'Student'}!</h1>
          <p>What would you like to do today?</p>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
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