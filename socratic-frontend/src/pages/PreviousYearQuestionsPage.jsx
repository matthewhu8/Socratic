import React, { useState, useEffect, useCallback, useContext } from 'react';
import MarkScheme from '../components/MarkScheme';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import API_URL from '../config/api';
import QRGradingModal from '../components/QRGradingModal';
import '../styles/PreviousYearQuestionsPage.css';

// Helper to format text
const formatBreadcrumb = (str) => {
  if (!str) return '';
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Helper to format topic names for display
const formatTopicName = (str) => {
  if (!str) return '';
  // Convert URL-friendly format back to readable format
  // "real-numbers" -> "Real Numbers"
  // "light-reflection-and-refraction" -> "Light Reflection And Refraction"
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Mapping of URL-friendly topic names to full chapter names
const topicToChapterMapping = {
  // Mathematics Grade 10
  'real-numbers': 'Chapter 1: Real Numbers',
  'polynomials': 'Chapter 2: Polynomials',
  'pair-of-linear-equations': 'Chapter 3: Pair of Linear Equations in Two Variables',
  'quadratic-equations': 'Chapter 4: Quadratic Equations',
  'arithmetic-progressions': 'Chapter 5: Arithmetic Progressions',
  'triangles': 'Chapter 6: Triangles',
  'coordinate-geometry': 'Chapter 7: Coordinate Geometry',
  'introduction-to-trigonometry': 'Chapter 8: Introduction to Trigonometry',
  'some-applications-of-trigonometry': 'Chapter 9: Some Applications of Trigonometry',
  'circles': 'Chapter 10: Circles',
  'constructions': 'Chapter 11: Constructions',
  'areas-related-to-circles': 'Chapter 12: Areas Related to Circles',
  'surface-areas-and-volumes': 'Chapter 13: Surface Areas and Volumes',
  'statistics': 'Chapter 14: Statistics',
  'probability': 'Chapter 15: Probability',
  
  // Add more mappings for other subjects and grades as needed
  // Physics
  'light-reflection-and-refraction': 'Chapter 10: Light - Reflection and Refraction',
  'human-eye-and-colourful-world': 'Chapter 11: Human Eye and Colourful World',
  'electricity': 'Chapter 12: Electricity',
  'magnetic-effects-of-electric-current': 'Chapter 13: Magnetic Effects of Electric Current',
  'sources-of-energy': 'Chapter 14: Sources of Energy',
  
  // Add more subjects and chapters as needed
};

// Helper to get chapter name from topic
const getChapterFromTopic = (topic) => {
  if (!topic || topic === 'direct') return '';
  return topicToChapterMapping[topic] || formatTopicName(topic);
};

// Helper to determine practice mode from URL
const getPracticeModeFromUrl = (pathname) => {
  if (pathname.includes('ncert-examples') || pathname.includes('ncert-topics')) {
    return 'NCERT Examples';
  } else if (pathname.includes('ncert-exercises')) {
    return 'NCERT Exercises';
  } else if (pathname.includes('previous-year-questions')) {
    return 'Previous Year Questions';
  } else if (pathname.includes('smart-practice')) {
    return 'Smart Practice';
  }
  return 'Previous Year Questions'; // default
};

const PreviousYearQuestionsPage = () => {
  const { subject, gradeParam, practiceMode, subtopic, subSubject, topic } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser } = useContext(AuthContext);

  // Determine if we're using the new URL structure or old one
  const isNewUrlStructure = topic !== undefined;
  const currentTopic = isNewUrlStructure ? topic : subtopic;
  const currentGrade = isNewUrlStructure ? currentUser?.grade : gradeParam?.replace('grade-', '');
  const currentPracticeMode = practiceMode;
  
  // State for questions and loading
  const [questions, setQuestions] = useState([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [chatMessage, setChatMessage] = useState('');
  const [showMarkScheme, setShowMarkScheme] = useState(false);
  const [showSolution, setShowSolution] = useState(false);
  const currentQuestion = questions[questionIndex];
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for QR grading modal
  const [showQRModal, setShowQRModal] = useState(false);
  const [gradingSession, setGradingSession] = useState(null);
 

  const handleChatSubmit = (e) => {
    e.preventDefault();
    console.log('Chat message:', chatMessage);
    setChatMessage('');
  };

  const handleSkip = () => {
    // Cycle through questions
    if (questions.length > 0) {
      setQuestionIndex((prevIndex) => (prevIndex + 1) % questions.length);
      setShowSolution(false); // Reset solution display for new question
    }
  };

  const toggleSolution = () => {
    setShowSolution(!showSolution);
  };

  // Handle submit for grading
  const handleSubmitForGrading = async () => {
    if (!currentQuestion) return;

    try {
      // Map practice mode for backend consistency
      const practiceModeMapping = {
        'ncert-examples': 'ncert-examples',
        'ncert-exercises': 'ncert-exercises',
        'pyqs': 'previous-year-questions',
        'smart-learning': 'smart-practice',
        'previous-year-questions': 'previous-year-questions',
        'smart-practice': 'smart-practice'
      };

      // Get the full chapter name for the grading session
      const chapterName = getChapterFromTopic(currentTopic);

      // Create grading session
      const sessionData = {
        questionId: currentQuestion.id,
        questionText: currentQuestion.question_text,
        correctSolution: currentQuestion.solution,
        practiceMode: practiceModeMapping[currentPracticeMode] || currentPracticeMode || '',
        subject: subject || '',
        grade: currentGrade || '',
        topic: currentTopic !== 'direct' ? chapterName : null
      };

      const response = await fetch(`${API_URL}/api/create-grading-session`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sessionData)
      });

      if (!response.ok) {
        throw new Error('Failed to create grading session');
      }

      const data = await response.json();
      setGradingSession(data);
      setShowQRModal(true);
      
    } catch (error) {
      console.error('Error creating grading session:', error);
      alert('Failed to create grading session. Please try again.');
    }
  };

  // Handle grading completion
  const handleGradingComplete = (result) => {
    console.log('Grading completed:', result);
    // You can handle the grading result here (e.g., store it, show additional UI, etc.)
  };

  // Function to fetch questions from API
  const fetchQuestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Map new practice mode names to backend expected values
      const practiceModeMapping = {
        'ncert-examples': 'ncert-examples',
        'ncert-exercises': 'ncert-exercises', // Note: backend has typo
        'pyqs': 'previous-year-questions',
        'smart-learning': 'smart-practice',
        // For backward compatibility
        'previous-year-questions': 'previous-year-questions',
        'smart-practice': 'smart-practice'
      };
      
      // Get parameters for API call
      const grade = currentGrade || '';
      // Use the full chapter name for API calls
      const chapterName = getChapterFromTopic(currentTopic);
      const mode = practiceModeMapping[currentPracticeMode] || currentPracticeMode || '';
      
      // For direct routes, we don't need to filter by topic
      let apiUrl;
      if (currentTopic === 'direct') {
        // For Previous Year Questions and Smart Practice without specific topic
        apiUrl = `${API_URL}/api/questions?practice_mode=${mode}&grade=${grade}&topic=general&subject=${subject}`;
      } else {
        // For specific topics (NCERT Examples/Exercises with topic)
        // Use the full chapter name instead of just the topic
        apiUrl = `${API_URL}/api/questions?practice_mode=${mode}&grade=${grade}&topic=${encodeURIComponent(chapterName)}&subject=${subject}`;
      }
      
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setError('Please login to access questions');
        return;
      }
      
      const response = await fetch(apiUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch questions: ${response.status}`);
      }
      
      const data = await response.json();
      setQuestions(data);
      
      if (data.length === 0) {
        setError('No questions found for the selected criteria');
      }
      
    } catch (err) {
      console.error('Error fetching questions:', err);
      setError(err.message || 'Failed to load questions');
    } finally {
      setLoading(false);
    }
  }, [subject, currentGrade, currentPracticeMode, currentTopic]);

  const handleNextQuestion = () => {
    // Same functionality as skip for now
    setQuestionIndex((prevIndex) => (prevIndex + 1) % questions.length);
    // Close mark scheme and solution when moving to next question
    setShowMarkScheme(false);
    setShowSolution(false);
  };

  const handleMarkSchemeClick = () => {
    setShowMarkScheme(true);
  };

  const handleCloseMarkScheme = () => {
    setShowMarkScheme(false);
  };

  // Fetch questions when component mounts or parameters change
  useEffect(() => {
    if (subject && (currentGrade || gradeParam) && currentPracticeMode) {
      console.log('Fetching questions with params:', { subject, currentGrade, currentPracticeMode, currentTopic });
      fetchQuestions();
    }
  }, [subject, currentGrade, currentPracticeMode, currentTopic, fetchQuestions]);

  // Reset question index and solution when questions change
  useEffect(() => {
    setQuestionIndex(0);
    setShowSolution(false);
  }, [questions]);

  // Determine the practice mode and format the title
  const practiceModeFromUrl = getPracticeModeFromUrl(location.pathname);
  const formattedSubject = formatBreadcrumb(subject);
  
  // Use practice mode from URL params if available, otherwise derive from URL
  const practiceModeMap = {
    'ncert-examples': 'NCERT Examples',
    'ncert-exercises': 'NCERT Exercises', 
    'pyqs': 'Previous Year Questions',
    'smart-learning': 'Smart Learning',
    'previous-year-questions': 'Previous Year Questions', // For backward compatibility
    'smart-practice': 'Smart Practice', // For backward compatibility
  };
  
  const finalPracticeMode = currentPracticeMode ? 
    (practiceModeMap[currentPracticeMode] || formatBreadcrumb(currentPracticeMode)) : practiceModeFromUrl;
  
  const formattedCurrentTopic = getChapterFromTopic(currentTopic);
  
  // Create the main title based on available information
  const getMainTitle = () => {
    if (currentTopic && currentTopic !== 'direct' && finalPracticeMode) {
      // Has topic: "NCERT Examples - Real Numbers" or "NCERT Examples - Chapter 1"
      return `${finalPracticeMode} - ${formattedCurrentTopic}`;
    } else if (currentTopic === 'direct' && finalPracticeMode && currentGrade) {
      // Direct route: "Previous Year Questions - Grade 10"
      return `${finalPracticeMode} - Grade ${currentGrade}`;
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
          {subSubject && (
            <>
              <span className="separator">›</span>
              <span>{formatBreadcrumb(subSubject)}</span>
            </>
          )}
          {currentGrade && (
            <>
              <span className="separator">›</span>
              <span>Grade {currentGrade}</span>
            </>
          )}
          {currentTopic && currentTopic !== 'direct' && (
            <>
              <span className="separator">›</span>
              <span>{formattedCurrentTopic}</span>
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
            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading questions...</p>
              </div>
            ) : error ? (
              <div className="error-container">
                <div className="error-icon">⚠️</div>
                <h3>Error Loading Questions</h3>
                <p>{error}</p>
                <button onClick={fetchQuestions} className="retry-btn">
                  Try Again
                </button>
              </div>
            ) : questions.length === 0 ? (
              <div className="no-questions-container">
                <div className="no-questions-icon">📚</div>
                <h3>No Questions Found</h3>
                <p>No questions available for the selected criteria.</p>
              </div>
            ) : currentQuestion ? (
              <div className="question-details-container">
                <div className="question-header">
                  <div className="marks-info">[Maximum mark: {currentQuestion.max_marks}]</div>
                  {currentQuestion.question_number && (
                    <div className="question-number-info">
                      Question {currentQuestion.question_number}
                    </div>
                  )}
                  {currentQuestion.difficulty && (
                    <div className="difficulty-info">
                      Difficulty: {currentQuestion.difficulty}
                    </div>
                  )}
                  {currentQuestion.year && (
                    <div className="year-info">
                      Year: {currentQuestion.year}
                    </div>
                  )}
                </div>
                                 <p className="question-text">{currentQuestion.question_text}</p>
                 
                 {showSolution && currentQuestion.solution && (
                   <div className="solution-container">
                     <h4>Solution:</h4>
                     <div className="solution-text">{currentQuestion.solution}</div>
                   </div>
                 )}
                 
                 <div className="question-footer">
                   <span className="question-counter">
                     Question {questionIndex + 1} of {questions.length}
                   </span>
                 </div>
              </div>
            ) : null}
          </div>
        </section>

        {/* Right Column: Actions & Chat */}
        <aside className="right-panel">
          <div className="action-buttons-panel">
            <button className="action-btn secondary" onClick={handleMarkSchemeClick}>
              Mark Scheme
            </button>
            
            <button className="action-btn secondary">Video Solution</button>
            <button 
              className="action-btn primary" 
              onClick={handleSubmitForGrading}
              disabled={!currentQuestion}
            >
              Submit for Grading
            </button>
            <button 
              className="action-btn skip" 
              onClick={handleSkip}
              disabled={questions.length === 0}
            >
              {questions.length > 1 ? 'Next Question' : 'Skip Question'}
            </button>
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

      {/* QR Grading Modal */}
      {gradingSession && (
        <QRGradingModal
          isOpen={showQRModal}
          onClose={() => setShowQRModal(false)}
          sessionId={gradingSession.sessionId}
          qrCodeUrl={gradingSession.qrCodeUrl}
          expiresIn={gradingSession.expiresIn}
          onGradingComplete={handleGradingComplete}
        />
      )}
    </div>
  );
};

export default PreviousYearQuestionsPage; 