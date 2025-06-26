import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import '../styles/PreviousYearQuestionsPage.css';

// Helper to format text
const formatBreadcrumb = (str) => {
  if (!str) return '';
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Helper to determine practice mode from URL
const getPracticeModeFromUrl = (pathname) => {
  if (pathname.includes('ncert-examples') || pathname.includes('ncert-topics')) {
    return 'NCERT Examples';
  } else if (pathname.includes('ncert-excercises')) {
    return 'NCERT Exercises';
  } else if (pathname.includes('previous-year-questions')) {
    return 'Previous Year Questions';
  } else if (pathname.includes('smart-practice')) {
    return 'Smart Practice';
  }
  return 'Previous Year Questions'; // default
};

const PreviousYearQuestionsPage = () => {
  const { subject, gradeParam, practiceMode, subtopic } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Mock Data for two questions to allow navigation
  const mockQuestions = [
    {
      id: 1,
      questionNumber: 1,
      maxMarks: 3,
      questionText: "Find the sum of the first 15 terms of the arithmetic progression: 2, 5, 8, ...",
      topic: "Sequences and Series"
    },
    {
      id: 2,
      questionNumber: 2,
      maxMarks: 6,
      questionText: "The 15th term of an arithmetic sequence is 21, and the common difference is -4. Find the first term and the 29th term.",
      topic: "Sequences and Series"
    }
  ];

  const [questionIndex, setQuestionIndex] = useState(0);
  const [chatMessage, setChatMessage] = useState('');
  const currentQuestion = mockQuestions[questionIndex];

  const handleChatSubmit = (e) => {
    e.preventDefault();
    console.log('Chat message:', chatMessage);
    setChatMessage('');
  };

  const handleSkip = () => {
    // Cycle through questions for demonstration
    setQuestionIndex((prevIndex) => (prevIndex + 1) % mockQuestions.length);
  };

  // Determine the practice mode and format the title
  const practiceModeFromUrl = getPracticeModeFromUrl(location.pathname);
  const formattedSubject = formatBreadcrumb(subject);
  
  // Use practice mode from URL params if available, otherwise derive from URL
  const practiceModeMap = {
    'ncert-examples': 'NCERT Examples',
    'ncert-excercises': 'NCERT Exercises',
    'previous-year-questions': 'Previous Year Questions',
    'smart-practice': 'Smart Practice',
  };
  
  const finalPracticeMode = practiceMode ? 
    (practiceModeMap[practiceMode] || formatBreadcrumb(practiceMode)) : practiceModeFromUrl;
  
  const formattedSubtopic = formatBreadcrumb(subtopic);
  
  // Create the main title based on available information
  const getMainTitle = () => {
    if (subtopic && subtopic !== 'direct' && finalPracticeMode) {
      // Has subtopic (from SubtopicSelectionPage): "NCERT Examples - Real Numbers"
      return `${finalPracticeMode} - ${formattedSubtopic}`;
    } else if (subtopic === 'direct' && finalPracticeMode && gradeParam) {
      // Direct route (Previous Year Questions/Smart Practice): "Previous Year Questions - Grade 10"
      const grade = gradeParam.replace('grade-', '');
      return `${finalPracticeMode} - Grade ${grade}`;
    } else if (finalPracticeMode) {
      return finalPracticeMode;
    } else {
      return 'Previous Year Questions';
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <div className="top-row">
          <button onClick={() => navigate(-1)} className="back-arrow-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        <div className="main-title">
          <h1>{getMainTitle()}</h1>
        </div>
        <div className="breadcrumbs">
          <span>{formattedSubject}</span>
          {gradeParam && (
            <>
              <span className="separator">›</span>
              <span>Grade {gradeParam.replace('grade-', '')}</span>
            </>
          )}
          {subtopic && subtopic !== 'direct' && (
            <>
              <span className="separator">›</span>
              <span>{formattedSubtopic}</span>
            </>
          )}
          <span className="separator">›</span>
          <span className="current">{finalPracticeMode}</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Left Column: Question */}
        <section className="question-display-area">
          <div className="question-content-card">
            {/* <div className="question-number-container">
              <span className="question-label">Question</span>
              <span className="question-number">{currentQuestion.questionNumber}</span>
            </div> */}
            <div className="question-details-container">
              <div className="marks-info">[Maximum mark: {currentQuestion.maxMarks}]</div>
              <p className="question-text">{currentQuestion.questionText}</p>
            </div>
          </div>
        </section>

        {/* Right Column: Actions & Chat */}
        <aside className="right-panel">
          <div className="action-buttons-panel">
            <button className="action-btn secondary">Mark Scheme</button>
            <button className="action-btn secondary">Video Solution</button>
            <button className="action-btn primary">Submit for Grading</button>
            <button className="action-btn skip" onClick={handleSkip}>Skip Question</button>
          </div>
          <div className="doubt-card">
            <header className="doubt-header">
              <div className="doubt-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 11.5C21 16.75 16.75 21 11.5 21C6.25 21 2 16.75 2 11.5C2 6.25 6.25 2 11.5 2C13.1 2 14.65 2.5 16 3.35" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16.5 6.4C17.8 7.5 18.7 9 18.7 10.8C18.7 11.4 18.6 12 18.4 12.5" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M8.5 12.5H14.5" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Ask a Doubt</h3>
            </header>
            <div className="chat-area">
              <div className="placeholder-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H5.2L4 17.2V4H20V16Z" fill="#CBD5E0"/></svg>
              </div>
              <span>Chat functionality coming soon...</span>
            </div>
            <form onSubmit={handleChatSubmit} className="chat-form">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Type your question..."
                className="chat-input"
              />
              <button type="submit" className="send-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="white"/></svg>
              </button>
            </form>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default PreviousYearQuestionsPage; 