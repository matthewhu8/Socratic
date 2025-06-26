import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MarkScheme from '../components/MarkScheme';
import '../styles/PreviousYearQuestionsPage.css';

// Helper to format text
const formatBreadcrumb = (str) => {
  if (!str) return '';
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const PreviousYearQuestionsPage = () => {
  const { subject } = useParams();
  const navigate = useNavigate();
  
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
  const [showMarkScheme, setShowMarkScheme] = useState(false);
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

  const handleNextQuestion = () => {
    // Same functionality as skip for now
    setQuestionIndex((prevIndex) => (prevIndex + 1) % mockQuestions.length);
    // Close mark scheme when moving to next question
    setShowMarkScheme(false);
  };

  const handleMarkSchemeClick = () => {
    setShowMarkScheme(true);
  };

  const handleCloseMarkScheme = () => {
    setShowMarkScheme(false);
  };

  const formattedSubject = formatBreadcrumb(subject);

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <button onClick={() => navigate(-1)} className="back-arrow-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <div className="breadcrumbs">
          <span>{formattedSubject}</span>
          <span className="separator">›</span>
          <span>{currentQuestion.topic}</span>
          <span className="separator">›</span>
          <span className="current">Previous Year Questions</span>
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
            <button className="action-btn secondary" onClick={handleMarkSchemeClick}>
              Mark Scheme
            </button>
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
            <form onSubmit={handleChatSubmit} className="doubt-chat-form">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Type your question..."
                className="doubt-chat-input"
              />
              <button type="submit" className="doubt-send-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="white"/></svg>
              </button>
            </form>
          </div>
        </aside>
      </main>

      {/* Mark Scheme Modal */}
      {showMarkScheme && (
        <MarkScheme 
          question={currentQuestion} 
          onClose={handleCloseMarkScheme}
          onNextQuestion={handleNextQuestion}
        />
      )}
    </div>
  );
};

export default PreviousYearQuestionsPage; 