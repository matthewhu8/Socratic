import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/AssessmentPage.css';

function AssessmentPage() {
  const [testCode, setTestCode] = useState('');
  const [username, setUsername] = useState('');
  const [assessmentHistory, setAssessmentHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Simulate API call to fetch assessment history
    const fetchAssessmentHistory = () => {
      setIsLoading(true);
      
      // Mock data - in a real app, this would be an API call
      setTimeout(() => {
        // Mock assessment history data
        const mockAssessments = [
          {
            id: 1,
            title: 'Algebra Midterm',
            date: '2025-02-15',
            score: 85,
            totalQuestions: 20,
            correctAnswers: 17,
            status: 'completed',
            teacher: 'Dr. Johnson',
            type: 'test'
          },
          {
            id: 2,
            title: 'Geometry Fundamentals',
            date: '2025-01-28',
            score: 92,
            totalQuestions: 15,
            correctAnswers: 14,
            status: 'completed',
            teacher: 'Ms. Garcia',
            type: 'practice-exam'
          },
          {
            id: 3,
            title: 'Physics Mechanics',
            date: '2025-01-10',
            score: 78,
            totalQuestions: 25,
            correctAnswers: 19,
            status: 'completed',
            teacher: 'Prof. Williams',
            type: 'test'
          },
          {
            id: 4,
            title: 'Calculus Prep Test',
            date: '2024-12-05',
            score: 88,
            totalQuestions: 30,
            correctAnswers: 26,
            status: 'completed',
            teacher: 'Dr. Smith',
            type: 'practice-exam'
          }
        ];
        
        setAssessmentHistory(mockAssessments);
        setIsLoading(false);
      }, 1000);
    };

    fetchAssessmentHistory();
  }, []);

  const handleTestCodeSubmit = (e) => {
    e.preventDefault();
    if (testCode.trim() && username.trim()) {
      // In a real app, validate the test code with an API call
      console.log(`Joining test with code: ${testCode} as user: ${username}`);
      // Then navigate to the test page with the code and username as parameters
      // Store username in localStorage for persistence
      localStorage.setItem('username', username);
      navigate(`/student/assessment/test/${testCode}?username=${encodeURIComponent(username)}`);
    }
  };

  const getScoreClass = (score) => {
    if (score >= 90) return 'excellent';
    if (score >= 80) return 'good';
    if (score >= 70) return 'average';
    return 'needs-improvement';
  };

  return (
    <div className="assessment-page-container">
      <div className="sticky-nav">
        <div className="nav-container">
          <Link to="/student/home" className="nav-item">
            <span className="nav-label">Home</span>
          </Link>
          <Link to="/student/dashboard" className="nav-item">
            <span className="nav-label">Dashboard</span>
          </Link>
        </div>
      </div>

      <div className="assessment-header">
        <h1>Assessments</h1>
        <p>Take tests and track your progress</p>
      </div>

      <div className="assessment-content">
        <div className="join-test-section">
          <h2>Join a Test or Practice Exam</h2>
          <p>Enter the access code provided by your teacher to start an assessment</p>
          
          <div className="info-box">
            <div className="info-box-header">
              <span className="info-icon">ℹ️</span>
              <h3>Tests vs Practice Exams</h3>
            </div>
            <div className="info-box-content">
              <p><strong>Tests:</strong> Traditional assessments that evaluate your knowledge. Your answers are submitted for grading.</p>
              <p><strong>Practice Exams:</strong> Interactive learning tools that provide immediate AI-powered feedback to help you improve. These don't affect your grades.</p>
            </div>
          </div>
          
          <form onSubmit={handleTestCodeSubmit} className="test-form">
            <div className="form-group">
              <label htmlFor="test-code">Test/Practice Exam Code:</label>
              <input
                type="text"
                id="test-code"
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                placeholder="Enter code (e.g. ABC123)"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="username">Your Name:</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your full name"
                required
              />
            </div>
            <button type="submit" className="join-button">Start Assessment</button>
          </form>
        </div>

        <div className="history-section">
          <h2>Assessment History</h2>
          
          {isLoading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading your assessment history...</p>
            </div>
          ) : assessmentHistory.length === 0 ? (
            <div className="empty-state">
              <p>You haven't taken any assessments yet.</p>
              <p className="hint">Join a test using a code from your teacher to get started.</p>
            </div>
          ) : (
            <div className="assessment-history-list">
              {assessmentHistory.map(assessment => (
                <div key={assessment.id} className="assessment-card">
                  <div className="assessment-card-header">
                    <h3>{assessment.title}</h3>
                    <span className="assessment-date">{assessment.date}</span>
                  </div>
                  
                  <div className="assessment-details">
                    <div className="score-circle">
                      <div className={`score ${getScoreClass(assessment.score)}`}>
                        {assessment.score}%
                      </div>
                    </div>
                    
                    <div className="assessment-stats">
                      <p>
                        <span className={`assessment-type ${assessment.type}`}>
                          {assessment.type === 'test' ? 'Test' : 'Practice Exam'}
                        </span>
                      </p>
                      <p>
                        <strong>Questions:</strong> {assessment.totalQuestions}
                      </p>
                      <p>
                        <strong>Correct:</strong> {assessment.correctAnswers}
                      </p>
                      <p>
                        <strong>Teacher:</strong> {assessment.teacher}
                      </p>
                    </div>
                  </div>
                  
                  <div className="assessment-actions">
                    <Link to={`/student/assessment/review/${assessment.id}`} className="review-link">
                      Review Results
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="assessment-footer">
        <Link to="/student/home" className="back-link">Back to Home</Link>
      </div>
    </div>
  );
}

export default AssessmentPage;