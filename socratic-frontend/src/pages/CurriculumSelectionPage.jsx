import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { FaBook, FaGlobeAsia } from 'react-icons/fa';
import '../styles/CurriculumSelectionPage.css';

function CurriculumSelectionPage() {
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);

  const handleCurriculumSelect = (curriculum) => {
    if (curriculum === 'cbse') {
      navigate('/student/dynamic-learning');
    } else if (curriculum === 'ib') {
      navigate('/student/ib-dynamic-learning');
    }
  };

  return (
    <div className="curriculum-selection-container">
      <div className="curriculum-header">
        <button onClick={() => navigate('/student/home')} className="back-button">
          ← Back to Home
        </button>
      </div>

      <div className="curriculum-content">
        <h1>Select Your Curriculum</h1>
        <p className="subtitle">Choose your educational board to access tailored learning materials</p>

        <div className="curriculum-cards">
          <div 
            className="curriculum-card cbse-card"
            onClick={() => handleCurriculumSelect('cbse')}
          >
            <div className="card-icon">
              <FaBook />
            </div>
            <h2>CBSE</h2>
            <p className="curriculum-description">
              Central Board of Secondary Education
            </p>
            <ul className="features-list">
              <li>NCERT-based content</li>
              <li>Previous year questions</li>
              <li>Chapter-wise exercises</li>
              <li>Smart learning modules</li>
            </ul>
            <div className="select-button">
              Select CBSE →
            </div>
          </div>

          <div 
            className="curriculum-card ib-card"
            onClick={() => handleCurriculumSelect('ib')}
          >
            <div className="card-icon">
              <FaGlobeAsia />
            </div>
            <h2>IB</h2>
            <p className="curriculum-description">
              International Baccalaureate
            </p>
            <ul className="features-list">
              <li>IB curriculum aligned</li>
              <li>Topic-based practice</li>
              <li>HL & SL differentiation</li>
              <li>Exam-style questions</li>
            </ul>
            <div className="select-button">
              Select IB →
            </div>
          </div>
        </div>

        <div className="info-note">
          <p>
            Currently logged in as: <strong>{currentUser?.name || 'Student'}</strong> | 
            Grade: <strong>{currentUser?.grade || 'Not set'}</strong>
          </p>
        </div>
      </div>
    </div>
  );
}

export default CurriculumSelectionPage;