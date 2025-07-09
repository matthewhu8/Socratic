import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/StudentDashboardPage.css';
import { AuthContext } from '../contexts/AuthContext';
import API_URL from '../config/api';

function StudentDashboardPage() {
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const subjects = [
    { id: 'mathematics', name: 'Mathematics', enabled: true },
    { id: 'physics', name: 'Physics', enabled: false },
    { id: 'chemistry', name: 'Chemistry', enabled: false },
    { id: 'biology', name: 'Biology', enabled: false },
    { id: 'english', name: 'English', enabled: false }
  ];

  const handleSubjectClick = (subject) => {
    if (subject.enabled) {
      navigate('/student/math-progress');
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <button onClick={() => navigate('/student/home')} className="back-button">
          ← Back to Home
        </button>
        <h1>Knowledge Profile</h1>
        <p>Track your learning progress across subjects</p>
      </div>

      <div className="dashboard-content">
        <div className="subjects-grid">
          {subjects.map((subject) => (
            <div 
              key={subject.id}
              className={`subject-card ${subject.enabled ? 'enabled' : 'disabled'}`}
              onClick={() => handleSubjectClick(subject)}
            >
              <h3>{subject.name}</h3>
              {!subject.enabled && <span className="coming-soon">Coming Soon</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default StudentDashboardPage;