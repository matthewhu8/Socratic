import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/DynamicLearningPage.css';

// Import icons (you may need to install react-icons if not already installed)
import { TbMathFunction } from 'react-icons/tb';
import { IoFlashOutline } from 'react-icons/io5';
import { TbFlask } from 'react-icons/tb';
import { FaHeart } from 'react-icons/fa';
import { TbBook } from 'react-icons/tb';

function DynamicLearningPage() {
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const subjects = [
    {
      id: 'mathematics',
      name: 'Mathematics',
      description: 'Interactive practice and examples',
      icon: <TbMathFunction />,
      color: '#4285f4',
      path: '/student/dynamic-learning/mathematics/select-grade'
    },
    {
      id: 'physics',
      name: 'Physics',
      description: 'Interactive practice and examples',
      icon: <IoFlashOutline />,
      color: '#9c27b0',
      path: '/student/dynamic-learning/physics/select-grade'
    },
    {
      id: 'chemistry',
      name: 'Chemistry',
      description: 'Interactive practice and examples',
      icon: <TbFlask />,
      color: '#4caf50',
      path: '/student/dynamic-learning/chemistry/select-grade'
    },
    {
      id: 'biology',
      name: 'Biology',
      description: 'Interactive practice and examples',
      icon: <FaHeart />,
      color: '#f44336',
      path: '/student/dynamic-learning/biology/select-grade'
    },
    {
      id: 'english',
      name: 'English',
      description: 'Interactive practice and examples',
      icon: <TbBook />,
      color: '#673ab7',
      path: '/student/dynamic-learning/english/select-grade'
    }
  ];

  return (
    <div className="dynamic-learning-container">
      {/* Back Button */}
      <button 
        onClick={() => navigate(-1)} 
        className="back-button"
      >
        ← Back
      </button>

      {/* Header */}
      <div className="dynamic-learning-header">
        <h1>Socratic Learning</h1>
        <p>Master concepts through interactive practice and personalized learning</p>
      </div>

      {/* Subject Cards */}
      <div className="subjects-grid">
        {subjects.map((subject) => (
          <Link 
            key={subject.id}
            to={subject.path}
            className="subject-card"
          >
            <div 
              className="subject-icon"
              style={{ backgroundColor: subject.color }}
            >
              {subject.icon}
            </div>
            <div className="subject-content">
              <h3>{subject.name}</h3>
              <p>{subject.description}</p>
            </div>
            <div className="subject-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default DynamicLearningPage; 