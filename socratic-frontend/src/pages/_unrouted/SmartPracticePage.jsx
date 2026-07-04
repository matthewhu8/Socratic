import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../../styles/_unrouted/SmartPracticePage.css';

function SmartPracticePage() {
  const { subject, grade } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [mcpDecision, setMcpDecision] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [questionsCompleted, setQuestionsCompleted] = useState(0);

  useEffect(() => {
    // Get first question when component mounts
    fetchNextQuestion();
  }, []);

  const fetchNextQuestion = async (lastQuestionId = null, wasCorrect = null, timeSpent = null) => {
    setLoading(true);
    setShowFeedback(false);
    setUserAnswer('');

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('/api/smart-practice/next-question-mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          last_question_id: lastQuestionId,
          correct: wasCorrect,
          time_spent: timeSpent,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get next question');
      }

      const data = await response.json();

      console.log('📦 MCP Response:', data);

      setCurrentQuestion(data.question);
      setMcpDecision(data.mcp_decision);
      setSessionId(data.session_id);
      setLoading(false);

    } catch (error) {
      console.error('Error fetching question:', error);
      setLoading(false);
      // Could show error message to user
    }
  };

  const handleSubmitAnswer = () => {
    // For demo purposes, simple answer checking
    // In production, this would call your grading endpoint

    const startTime = Date.now();

    // Mock answer checking (you'd replace this with actual grading)
    const correctAnswers = {
      101: 'x = -2, x = -3',
      102: 'x = 3, x = 0.5',
      103: 'x = 1, x = -9',
      104: '41',
      105: '630'
    };

    const correct = userAnswer.toLowerCase().includes(correctAnswers[currentQuestion.id]?.toLowerCase().split(',')[0]);

    setIsCorrect(correct);
    setShowFeedback(true);
    setQuestionsCompleted(questionsCompleted + 1);
  };

  const handleNextQuestion = () => {
    const questionStartTime = sessionStorage.getItem('questionStartTime');
    const timeSpent = questionStartTime ? Math.floor((Date.now() - parseInt(questionStartTime)) / 1000) : null;

    fetchNextQuestion(currentQuestion.id, isCorrect, timeSpent);

    // Set new start time for next question
    sessionStorage.setItem('questionStartTime', Date.now().toString());
  };

  useEffect(() => {
    // Track when question starts
    if (currentQuestion) {
      sessionStorage.setItem('questionStartTime', Date.now().toString());
    }
  }, [currentQuestion]);

  if (loading) {
    return (
      <div className="smart-practice-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>🧠 Gemini is analyzing your knowledge profile...</p>
          <p className="loading-subtitle">Finding the perfect question for you</p>
        </div>
      </div>
    );
  }

  return (
    <div className="smart-practice-container">
      <button onClick={() => navigate(-1)} className="back-button">
        ← Back
      </button>

      <header className="smart-practice-header">
        <h1>🤖 MCP-Powered Smart Practice</h1>
        <div className="session-info">
          <span>Session: {sessionId?.substring(8, 16)}</span>
          <span>Questions: {questionsCompleted}</span>
        </div>
      </header>

      {/* MCP Decision Info - Educational Display */}
      {mcpDecision && (
        <div className="mcp-decision-panel">
          <h3>🧠 How Gemini Selected This Question</h3>

          <div className="decision-section">
            <label>Reasoning:</label>
            <p>{mcpDecision.reasoning}</p>
          </div>

          <div className="decision-section">
            <label>Learning Objective:</label>
            <p>{mcpDecision.learning_objective}</p>
          </div>

          {mcpDecision.difficulty_rationale && (
            <div className="decision-section">
              <label>Difficulty Selection:</label>
              <p>{mcpDecision.difficulty_rationale}</p>
            </div>
          )}

          <div className="decision-section">
            <label>Tools Used:</label>
            <div className="tools-list">
              {mcpDecision.tools_used?.map((tool, idx) => (
                <span key={idx} className="tool-badge">
                  {tool.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Question Display */}
      <div className="question-card">
        <div className="question-header">
          <span className="question-label">Question {questionsCompleted + 1}</span>
          <div className="question-meta">
            <span className="topic-badge">{currentQuestion.topic}</span>
            <span className="difficulty-badge" style={{
              backgroundColor: currentQuestion.difficulty < 0.4 ? '#4caf50' :
                             currentQuestion.difficulty < 0.7 ? '#ff9800' : '#f44336',
              color: 'white',
              padding: '4px 12px',
              borderRadius: '12px',
              fontSize: '14px'
            }}>
              {currentQuestion.difficulty < 0.4 ? 'Easy' :
               currentQuestion.difficulty < 0.7 ? 'Medium' : 'Hard'}
            </span>
          </div>
        </div>

        <div className="question-content">
          <p>{currentQuestion.question_text}</p>
        </div>

        {!showFeedback ? (
          <div className="answer-section">
            <input
              type="text"
              className="answer-input"
              placeholder="Enter your answer..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmitAnswer()}
            />
            <button
              className="submit-button"
              onClick={handleSubmitAnswer}
              disabled={!userAnswer.trim()}
            >
              Submit Answer
            </button>
          </div>
        ) : (
          <div className={`feedback-section ${isCorrect ? 'correct' : 'incorrect'}`}>
            <div className="feedback-header">
              {isCorrect ? (
                <>
                  <span className="feedback-icon">✓</span>
                  <h3>Correct! Well done!</h3>
                </>
              ) : (
                <>
                  <span className="feedback-icon">✗</span>
                  <h3>Not quite right</h3>
                </>
              )}
            </div>

            <button className="next-button" onClick={handleNextQuestion}>
              Next Question →
            </button>
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h4>💡 About MCP-Powered Practice</h4>
        <p>
          This practice mode uses <strong>Model Context Protocol (MCP)</strong> where Gemini AI
          intelligently selects questions based on your performance. Watch the "Tools Used" section
          to see which analysis tools Gemini decided to call!
        </p>
        <ul>
          <li>✓ Adaptive difficulty based on your skill level</li>
          <li>✓ Identifies knowledge gaps automatically</li>
          <li>✓ Optimizes learning trajectory in real-time</li>
        </ul>
      </div>
    </div>
  );
}

export default SmartPracticePage;
