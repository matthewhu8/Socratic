import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TbMathFunction } from 'react-icons/tb';
import { IoFlashOutline } from 'react-icons/io5';
import { TbFlask } from 'react-icons/tb';
import { FaHeart } from 'react-icons/fa';
import { TbBook } from 'react-icons/tb';
import '../styles/GradeSelectionPage.css';

function GradeSelectionPage() {
  const { subject } = useParams();
  const navigate = useNavigate();

  const subjectConfig = {
    mathematics: {
      name: 'Mathematics',
      icon: <TbMathFunction />,
      color: '#4285f4',
      backgroundColor: '#e8f0fe'
    },
    physics: {
      name: 'Physics',
      icon: <IoFlashOutline />,
      color: '#9c27b0',
      backgroundColor: '#f3e5f5'
    },
    chemistry: {
      name: 'Chemistry',
      icon: <TbFlask />,
      color: '#4caf50',
      backgroundColor: '#e8f5e9'
    },
    biology: {
      name: 'Biology',
      icon: <FaHeart />,
      color: '#f44336',
      backgroundColor: '#ffebee'
    },
    english: {
      name: 'English',
      icon: <TbBook />,
      color: '#673ab7',
      backgroundColor: '#f3e5f5'
    }
  };

  const grades = [
    { grade: 9, description: 'Grade 9 curriculum' },
    { grade: 10, description: 'Grade 10 curriculum' },
    { grade: 11, description: 'Grade 11 curriculum' },
    { grade: 12, description: 'Grade 12 curriculum' }
  ];

  const currentSubject = subjectConfig[subject];

  if (!currentSubject) {
    return (
      <div className="grade-selection-container">
        <h1>Subject not found</h1>
        <button onClick={() => navigate('/student/dynamic-learning')}>
          Back to subjects
        </button>
      </div>
    );
  }

  const handleGradeSelect = (grade) => {
    navigate(`/student/practice/${subject}/grade-${grade}`);
  };

  return (
    <div className="grade-selection-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5"></path>
          <path d="M12 19l-7-7 7-7"></path>
        </svg>
      </button>

      <header className="grade-selection-header">
        <div 
          className="subject-icon-wrapper" 
          style={{ 
            backgroundColor: currentSubject.backgroundColor, 
            color: currentSubject.color 
          }}
        >
          {currentSubject.icon}
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: currentSubject.color }}>{currentSubject.name}</h1>
          <p>Select your grade level</p>
        </div>
      </header>

      <main className="grades-grid">
        {grades.map(({ grade, description }) => (
          <button
            key={grade}
            onClick={() => handleGradeSelect(grade)}
            className="grade-card"
          >
            <div className="grade-number">
              {grade}
            </div>
            <div className="grade-details">
              <h3>Grade {grade}</h3>
              <p>{description}</p>
            </div>
            <div className="grade-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </button>
        ))}
      </main>
    </div>
  );
}

export default GradeSelectionPage; 