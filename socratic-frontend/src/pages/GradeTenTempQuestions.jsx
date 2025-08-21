import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/GradeTenTempQuestions.css';

function GradeTenTempQuestions() {
  const navigate = useNavigate();
  const [showMarkScheme, setShowMarkScheme] = useState({});
  const [showWhiteboardSolution, setShowWhiteboardSolution] = useState({});

  // Chapter 1: Number & Algebra - Sequences and Series questions
  const questions = [
    {
      id: 1,
      questionNumber: 1,
      maxMarks: 4,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'Find the sum of the first 20 terms of the arithmetic sequence: 3, 7, 11, 15, ...',
      markScheme: null
    },
    {
      id: 2,
      questionNumber: 2,
      maxMarks: 6,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'An arithmetic sequence has u₁ = 40, u₂ = 32, u₃ = 24.\n\n(a) Find the common difference, d. [2]\n(b) Find u₅. [2]\n(c) Find S₁₀. [2]',
      markScheme: null
    },
    {
      id: 3,
      questionNumber: 3,
      maxMarks: 6,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'Consider a geometric sequence with u₁ = 8 and u₄ = 1.\n\n(a) Find the common ratio, r. [2]\n(b) Find u₆. [2]\n(c) Find the sum to infinity if it exists. [2]',
      markScheme: null
    },
    {
      id: 4,
      questionNumber: 4,
      maxMarks: 5,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'The sum of the first n terms of an arithmetic sequence is given by S_n = 2n² + 3n.\n\n(a) Find the first term. [2]\n(b) Find the common difference. [2]\n(c) Find the 10th term. [1]',
      markScheme: null
    },
    {
      id: 5,
      questionNumber: 5,
      maxMarks: 7,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'A geometric sequence has first term a = 3 and common ratio r = 2.\n\n(a) Find the 8th term of the sequence. [2]\n(b) Find the sum of the first 10 terms. [3]\n(c) Another geometric sequence has the same first term but its 5th term is 48. Find its common ratio. [2]',
      markScheme: null
    },
    {
      id: 6,
      questionNumber: 6,
      maxMarks: 8,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'The first three terms of an arithmetic sequence are 2k, 3k+4, and 5k+2, where k is a constant.\n\n(a) Find the value of k. [3]\n(b) Find the common difference. [2]\n(c) Find the sum of the first 20 terms. [3]',
      markScheme: null
    },
    {
      id: 7,
      questionNumber: 7,
      maxMarks: 4,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'Find the sum of the infinite geometric series: 12 + 4 + 4/3 + 4/9 + ...',
      markScheme: null
    },
    {
      id: 8,
      questionNumber: 8,
      maxMarks: 5,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'The nth term of a sequence is given by u_n = 3n² - 2n + 1.\n\n(a) Find the first four terms. [2]\n(b) Find u₁₀. [1]\n(c) Find the value of n for which u_n = 136. [2]',
      markScheme: null
    },
    {
      id: 9,
      questionNumber: 9,
      maxMarks: 6,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'An arithmetic sequence has first term a = 5 and last term l = 95. The sum of all terms is 1000.\n\n(a) Find the number of terms n. [3]\n(b) Find the common difference d. [2]\n(c) Find the 15th term. [1]',
      markScheme: null
    },
    {
      id: 10,
      questionNumber: 10,
      maxMarks: 7,
      chapter: 'Chapter 1: Number & Algebra',
      topic: 'Topic 1: Sequences and Series',
      questionText: 'The sum of the first n terms of a series is given by S_n = n(n+1)(n+2)/3.\n\n(a) Find the first three terms of the series. [3]\n(b) Show that the nth term is n(n+1). [2]\n(c) Hence, find the sum of the series: 2 + 6 + 12 + 20 + ... + 110. [2]',
      markScheme: null
    }
  ];

  const filteredQuestions = questions;

  const toggleMarkScheme = (questionId) => {
    setShowMarkScheme(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  const toggleWhiteboardSolution = (questionId) => {
    setShowWhiteboardSolution(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  return (
    <div className="grade-ten-container">
      <div className="header-bar">
        <button onClick={() => navigate('/student/ib-dynamic-learning')} className="back-nav-button">
          ← Back to IB Subjects
        </button>
        <div className="page-title">
          <h1>Chapter 1: Number & Algebra</h1>
          <p className="chapter-subtitle">Topic 1: Sequences and Series</p>
        </div>
      </div>

      <div className="questions-list">
        {filteredQuestions.map((question) => (
          <div key={question.id} className="question-card">
            <div className="question-header">
              <div className="question-number">Question {question.questionNumber}</div>
              <div className="question-meta">
                <span className="marks-tag">{question.maxMarks} marks</span>
              </div>
            </div>

            <div className="question-info">
              <span className="info-tag topic">{question.topic}</span>
            </div>

            <div className="question-content">
              <div className="question-text">
                <div className="max-marks">[Maximum mark: {question.maxMarks}]</div>
                <div className="question-body">{question.questionText}</div>
              </div>

              <div className="question-actions">
                <button 
                  className="action-button mark-scheme"
                  onClick={() => toggleMarkScheme(question.id)}
                >
                  📋 Mark Scheme
                </button>
                <button 
                  className="action-button whiteboard-solution"
                  onClick={() => toggleWhiteboardSolution(question.id)}
                >
                  ✏️ Whiteboard Solution
                  <span className="solution-count">1</span>
                </button>
                <button className="action-button ai-feedback">
                  🤖 AI Feedback
                </button>
                <button className="action-button formula">
                  Formula Booklet
                </button>
              </div>

              {showMarkScheme[question.id] && (
                <div className="mark-scheme-content">
                  <h4>Mark Scheme</h4>
                  <p className="coming-soon">Coming soon! Mark schemes are being prepared for all questions.</p>
                </div>
              )}

              {showWhiteboardSolution[question.id] && (
                <div className="whiteboard-solution-content">
                  <p>Whiteboard solutions coming soon! This feature will provide step-by-step visual explanations.</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GradeTenTempQuestions;