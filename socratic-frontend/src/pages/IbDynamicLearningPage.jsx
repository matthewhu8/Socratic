import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { 
  TbMathFunction, 
  TbFlask, 
  TbBook, 
  TbLanguage,
  TbBuildingBank
} from 'react-icons/tb';
import '../styles/IbDynamicLearningPage.css';

function IbDynamicLearningPage() {
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  const [expandedSubject, setExpandedSubject] = useState('mathematics');
  const [showLockedMessage, setShowLockedMessage] = useState(false);
  const [lockedMessageContent, setLockedMessageContent] = useState('');

  // Get dynamic class title based on user's grade
  const getClassTitle = () => {
    const userGrade = currentUser?.grade;
    if (userGrade) {
      return `IB Grade ${userGrade} Practice`;
    }
    return 'IB Practice Platform';
  };

  const subjects = [
    {
      id: 'mathematics',
      name: 'Mathematics',
      icon: <TbMathFunction />,
      color: '#4285f4',
      bgColor: '#e8f0fe',
      isLocked: false,
      options: [
        { 
          id: 'aahl', 
          name: 'Analysis and Approaches HL (AA HL)',
          description: 'Advanced mathematics with calculus and analysis focus',
          isLocked: false
        },
        { 
          id: 'aasl', 
          name: 'Analysis and Approaches SL (AA SL)',
          description: 'Standard level mathematics with analytical approach',
          isLocked: true
        },
        { 
          id: 'aisl', 
          name: 'Applications and Interpretation SL (AI SL)',
          description: 'Mathematics with practical applications focus',
          isLocked: true
        },
        { 
          id: 'aihl', 
          name: 'Applications and Interpretation HL (AI HL)',
          description: 'Advanced applied mathematics and statistics',
          isLocked: true
        }
      ]
    },
    {
      id: 'sciences',
      name: 'Sciences',
      icon: <TbFlask />,
      color: '#00897b',
      bgColor: '#e0f2f1',
      isLocked: true,
      lockedMessage: "We currently don't have materials for these subjects. Leave us some feedback in the home page if you would like to see this done ASAP."
    },
    {
      id: 'individuals-societies',
      name: 'Individuals & Societies',
      icon: <TbBuildingBank />,
      color: '#ff6b6b',
      bgColor: '#ffe0e0',
      isLocked: true,
      lockedMessage: "We currently don't have materials for these subjects. Leave us some feedback in the home page if you would like to see this done ASAP."
    },
    {
      id: 'english',
      name: 'English',
      icon: <TbBook />,
      color: '#7c4dff',
      bgColor: '#f3e5ff',
      isLocked: true,
      lockedMessage: "We currently don't have materials for these subjects. Leave us some feedback in the home page if you would like to see this done ASAP."
    },
    {
      id: 'language-b',
      name: 'Language B',
      icon: <TbLanguage />,
      color: '#ffa726',
      bgColor: '#fff3e0',
      isLocked: true,
      lockedMessage: "We currently don't have materials for these subjects. Leave us some feedback in the home page if you would like to see this done ASAP."
    }
  ];

  const toggleSubject = (subject) => {
    if (subject.isLocked) {
      setLockedMessageContent(subject.lockedMessage);
      setShowLockedMessage(true);
      return;
    }
    setExpandedSubject(expandedSubject === subject.id ? null : subject.id);
  };

  const handleOptionClick = (subject, option) => {
    if (option.isLocked) {
      setLockedMessageContent("This course is coming soon. We currently only have materials for AA HL.");
      setShowLockedMessage(true);
      return;
    }
    
    // Check if user is Grade 10 and clicking AAHL
    if (currentUser?.grade === '10' && option.id === 'aahl') {
      // Navigate directly to Grade 10 temp questions for AAHL
      navigate(`/student/ib-dynamic-learning/mathematics/aahl/topics`);
    } else {
      // Navigate to the regular IB topic selection page
      navigate(`/student/ib-dynamic-learning/${subject.id}/${option.id}/topics`);
    }
  };

  const renderSubjectCard = (subject) => {
    const isExpanded = expandedSubject === subject.id;
    const isLocked = subject.isLocked;

    return (
      <div 
        key={subject.id} 
        className={`ib-subject-section ${isExpanded ? 'expanded' : ''} ${isLocked ? 'locked' : ''}`}
        title={isLocked ? subject.lockedMessage : ''}
      >
        <div 
          className="ib-subject-header"
          style={{ backgroundColor: isLocked ? '#f3f4f6' : subject.bgColor }}
          onClick={() => toggleSubject(subject)}
        >
          <div className="ib-subject-icon" style={{ color: isLocked ? '#9ca3af' : subject.color }}>
            {subject.icon}
          </div>
          <h2 style={{ color: isLocked ? '#9ca3af' : subject.color }}>{subject.name}</h2>
          {isLocked && <span className="locked-badge">🔒 Coming Soon</span>}
          {!isLocked && (
            <div className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M6 9L12 15L18 9" stroke={subject.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          )}
        </div>

        {isExpanded && !isLocked && (
          <div className="ib-subject-content">
            <div className="ib-subject-card">
              <div className="ib-card-header">
                <div className="ib-card-icon" style={{ backgroundColor: subject.color }}>
                  {subject.icon}
                </div>
                <h3>{subject.name} Courses</h3>
              </div>
              <div className="ib-options-list">
                {subject.options?.map(option => (
                  <div 
                    key={option.id} 
                    className={`ib-option-item ${option.isLocked ? 'locked-option' : ''}`}
                    onClick={() => handleOptionClick(subject, option)}
                  >
                    <div className="ib-option-content">
                      <h4>
                        {option.name}
                        {option.isLocked && <span className="locked-inline">🔒</span>}
                      </h4>
                      <p>{option.description}</p>
                    </div>
                    <svg className="arrow-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="ib-dynamic-learning-container">
      <div className="ib-dynamic-header">
        <button onClick={() => navigate('/student/curriculum-selection')} className="ib-back-button">
          ← Back to Curriculum Selection
        </button>
      </div>
      <div className="ib-hero-section">
        <h1>{getClassTitle()}</h1>
        <p>Master the IB curriculum with comprehensive practice materials and exam-style questions</p>
        <div className="ib-stats-container">
          <div className="ib-stat-item">
            <h2>IB</h2>
            <p>International Baccalaureate</p>
          </div>
          <div className="ib-stat-item">
            <h2>HL & SL</h2>
            <p>Both levels covered</p>
          </div>
        </div>
      </div>

      <div className="ib-subjects-container">
        <div className="ib-subjects-header">
          <h2>Select Your Subject</h2>
          <p>Choose a subject to begin your IB practice journey</p>
        </div>

        <div className="ib-subjects-list">
          {subjects.map(subject => renderSubjectCard(subject))}
        </div>
      </div>

      {/* Locked Message Modal */}
      {showLockedMessage && (
        <div className="ib-modal-overlay" onClick={() => setShowLockedMessage(false)}>
          <div className="ib-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Coming Soon</h3>
            <p>{lockedMessageContent}</p>
            <button className="ib-modal-close" onClick={() => setShowLockedMessage(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default IbDynamicLearningPage;