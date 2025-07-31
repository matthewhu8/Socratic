import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import MathText from '../components/MathText';
import QRGradingModal from '../components/QRGradingModal';
import API_URL from '../config/api';
import '../styles/SmartPracticePage.css';

const SmartPracticePage = () => {
  const { subject, gradeParam, chapter } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '10';
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  
  // Question and session state
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [aiSelection, setAiSelection] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Session tracking
  const [sessionStats, setSessionStats] = useState({
    questionsAttempted: 0,
    correctAnswers: 0,
    totalScore: 0,
    sessionStartTime: Date.now()
  });
  
  // AI reasoning display
  const [showReasoning, setShowReasoning] = useState(true);
  
  // Grading modal state
  const [showGradingModal, setShowGradingModal] = useState(false);
  const [gradingImageFile, setGradingImageFile] = useState(null);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());

  // Fetch next smart question
  const fetchNextQuestion = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setError('Please login to access Smart Practice');
        return;
      }
      
      // Build query parameters
      let queryParams = `subject=${subject}`;
      if (chapter && chapter !== 'mixed') {
        // Convert URL-friendly chapter back to full name for API
        const chapterName = chapter.split('-').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        queryParams += `&chapter=${encodeURIComponent(chapterName)}`;
      }
      
      const response = await fetch(
        `${API_URL}/api/smart-practice/next-question?${queryParams}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      setCurrentQuestion(data.question);
      setAiSelection(data.ai_selection);
      setQuestionStartTime(Date.now());
      
      // Update session stats
      setSessionStats(prev => ({
        ...prev,
        questionsAttempted: prev.questionsAttempted + 1
      }));
      
    } catch (error) {
      console.error('Error fetching smart question:', error);
      setError(`Failed to load question: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Submit attempt and get next question
  const handleSubmitAttempt = async (score, feedback = '') => {
    if (!currentQuestion) return;
    
    try {
      const token = localStorage.getItem('accessToken');
      const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);
      
      const formData = new FormData();
      formData.append('question_id', currentQuestion.id || currentQuestion.question_id);
      formData.append('source_type', currentQuestion.source_type || 'pyqs');
      formData.append('time_spent_seconds', timeSpent);
      formData.append('score', score || 0);
      formData.append('feedback', feedback);
      formData.append('student_answer', 'Photo submission'); // For now
      
      const response = await fetch(`${API_URL}/api/smart-practice/submit-attempt`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit attempt');
      }
      
      // Update session stats
      setSessionStats(prev => ({
        ...prev,
        correctAnswers: score >= 0.7 ? prev.correctAnswers + 1 : prev.correctAnswers,
        totalScore: prev.totalScore + (score || 0)
      }));
      
      // Automatically fetch next question
      await fetchNextQuestion();
      
    } catch (error) {
      console.error('Error submitting attempt:', error);
      setError(`Failed to submit attempt: ${error.message}`);
    }
  };

  // Handle grading modal results
  const handleGradingComplete = async (gradingResult) => {
    setShowGradingModal(false);
    setGradingImageFile(null);
    
    if (gradingResult && gradingResult.grade) {
      // Parse score from grade (e.g., "8/10" -> 0.8)
      const scoreParts = gradingResult.grade.split('/');
      const score = scoreParts.length === 2 ? 
        parseInt(scoreParts[0]) / parseInt(scoreParts[1]) : 0;
      
      // Submit the attempt with grading results
      await handleSubmitAttempt(score, gradingResult.feedback || '');
    }
  };

  // Initialize by fetching first question
  useEffect(() => {
    if (currentUser && subject) {
      fetchNextQuestion();
    }
  }, [currentUser, subject]);

  const formatSubject = (str) => {
    return str?.charAt(0).toUpperCase() + str?.slice(1) || '';
  };

  if (!currentUser) {
    return (
      <div className="smart-practice-container">
        <div className="error-message">Please login to access Smart Practice</div>
      </div>
    );
  }

  return (
    <div className="smart-practice-container">
      {/* Header */}
      <div className="smart-practice-header">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5"></path>
            <path d="M12 19l-7-7 7-7"></path>
          </svg>
        </button>
        
        <div className="header-content">
          <div className="breadcrumbs">
            {formatSubject(subject)} > Grade {grade} > Smart Practice
            {chapter && chapter !== 'mixed' && (
              <> > {chapter.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</>
            )}
            {chapter === 'mixed' && <> > Mixed Practice</>}
          </div>
          <h1>AI-Powered Adaptive Learning</h1>
        </div>
      </div>

      {/* Session Stats */}
      <div className="session-stats">
        <div className="stat-card">
          <div className="stat-label">Questions</div>
          <div className="stat-value">{sessionStats.questionsAttempted}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Success Rate</div>
          <div className="stat-value">
            {sessionStats.questionsAttempted > 0 
              ? Math.round((sessionStats.correctAnswers / sessionStats.questionsAttempted) * 100)
              : 0}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Score</div>
          <div className="stat-value">
            {sessionStats.questionsAttempted > 0
              ? Math.round((sessionStats.totalScore / sessionStats.questionsAttempted) * 100)
              : 0}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Session Time</div>
          <div className="stat-value">
            {Math.floor((Date.now() - sessionStats.sessionStartTime) / 60000)}m
          </div>
        </div>
      </div>

      {/* AI Reasoning Card */}
      {aiSelection && showReasoning && (
        <div className="ai-reasoning-card">
          <div className="reasoning-header">
            <div className="reasoning-title">
              <span className="ai-icon">🤖</span>
              Why this question?
            </div>
            <button 
              onClick={() => setShowReasoning(false)}
              className="close-reasoning"
            >
              ×
            </button>
          </div>
          <div className="reasoning-content">
            <p className="reasoning-text">{aiSelection.reasoning}</p>
            <div className="reasoning-details">
              <div className="detail-item">
                <span className="detail-label">Expected Difficulty:</span>
                <span className="detail-value">{aiSelection.expected_difficulty}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Target Skills:</span>
                <span className="detail-value">
                  {aiSelection.target_skills?.join(', ') || 'General practice'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Est. Time:</span>
                <span className="detail-value">
                  {Math.round(aiSelection.estimated_time_seconds / 60)} min
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">AI Confidence:</span>
                <span className={`confidence-badge confidence-${aiSelection.confidence_level}`}>
                  {aiSelection.confidence_level}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-card">
          <div className="error-title">Error</div>
          <div className="error-message">{error}</div>
          <button onClick={fetchNextQuestion} className="retry-button">
            Try Again
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">
            AI is selecting the perfect question for you...
          </div>
        </div>
      )}

      {/* Question Display */}
      {currentQuestion && !isLoading && (
        <div className="question-container">
          <div className="question-header">
            <div className="question-meta">
              <span className="question-id">Question #{currentQuestion.id}</span>
              {currentQuestion.source_type && (
                <span className="question-source">
                  {currentQuestion.source_type === 'ncert_examples' ? 'NCERT Example' : 
                   currentQuestion.source_type === 'ncert_exercises' ? 'NCERT Exercise' :
                   currentQuestion.source_type === 'generated' ? 'AI Generated' : 'Previous Year'}
                </span>
              )}
              <span className="question-difficulty">
                Difficulty: {currentQuestion.difficulty}/2.0
              </span>
              {currentQuestion.max_marks && (
                <span className="question-marks">
                  Max Marks: {currentQuestion.max_marks}
                </span>
              )}
              {currentQuestion.year && (
                <span className="question-year">Year: {currentQuestion.year}</span>
              )}
            </div>
            {currentQuestion.chapter && (
              <div className="question-chapter">{currentQuestion.chapter}</div>
            )}
          </div>

          <div className="question-content">
            <div className="question-text">
              <MathText text={currentQuestion.question_text} />
            </div>
          </div>

          <div className="question-actions">
            <button
              onClick={() => setShowGradingModal(true)}
              className="grade-work-button"
            >
              Submit Your Work
            </button>
            <button
              onClick={fetchNextQuestion}
              className="skip-button"
            >
              Skip Question
            </button>
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="toggle-reasoning-button"
            >
              {showReasoning ? 'Hide' : 'Show'} AI Reasoning
            </button>
          </div>
        </div>
      )}

      {/* Grading Modal */}
      {showGradingModal && currentQuestion && (
        <QRGradingModal
          question={currentQuestion}
          onClose={() => setShowGradingModal(false)}
          onGradingComplete={handleGradingComplete}
          practiceMode="smart-practice"
          subject={subject}
          grade={grade}
        />
      )}
    </div>
  );
};

export default SmartPracticePage;