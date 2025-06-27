import React, { useState } from 'react';
import './MarkScheme.css';

const MarkScheme = ({ question, onClose, onNextQuestion }) => {
  const [isChatMode, setIsChatMode] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Mock mark scheme data
  const mockMarkScheme = {
    totalMarks: question?.maxMarks || 3,
    markingCriteria: [
      {
        step: "1a",
        description: "Identify the arithmetic progression",
        details: "Recognize that this is an arithmetic progression with first term a = 2 and common difference d = 3",
        marks: 1,
        acceptableAnswers: [
          "a = 2, d = 3",
          "First term = 2, common difference = 3",
          "a₁ = 2, d = 5 - 2 = 3"
        ]
      },
      {
        step: "1b", 
        description: "Apply the sum formula",
        details: "Use the formula Sₙ = n/2[2a + (n-1)d] where n = 15",
        marks: 1,
        acceptableAnswers: [
          "S₁₅ = 15/2[2(2) + (15-1)(3)]",
          "S₁₅ = 15/2[4 + 14(3)]",
          "S₁₅ = 15/2[4 + 42]"
        ]
      },
      {
        step: "1c",
        description: "Calculate the final answer",
        details: "Complete the calculation to find S₁₅ = 345",
        marks: 1,
        acceptableAnswers: [
          "345",
          "S₁₅ = 345",
          "Sum = 345"
        ]
      }
    ],
    commonMistakes: [
      {
        mistake: "Using wrong common difference",
        description: "Students often calculate d = 5 - 2 = 3 incorrectly or use d = 2",
        deduction: "Lose 1 mark for incorrect d value"
      },
      {
        mistake: "Formula error",
        description: "Using Sₙ = n(a + l)/2 without finding the last term first",
        deduction: "Partial credit possible if method is shown"
      },
      {
        mistake: "Arithmetic errors",
        description: "Correct method but calculation mistakes",
        deduction: "Lose 1 mark for final answer, method marks awarded"
      }
    ],
    teacherNotes: [
      "Accept equivalent forms of the arithmetic progression formula",
      "Award method marks even if final answer is incorrect due to arithmetic errors",
      "Look for clear identification of a and d values",
      "Partial credit available for correct substitution into formula"
    ]
  };

  const handleChatToggle = () => {
    setIsChatMode(!isChatMode);
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: currentMessage,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    // Mock AI response
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        sender: 'ai',
        content: `I understand you're asking about "${currentMessage}". This mark scheme shows the step-by-step approach for solving arithmetic progression problems. Each step has specific criteria and acceptable answers. Would you like me to explain any particular step in more detail?`,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const renderMarkSchemeContent = () => (
    <div className="mark-scheme-content">
      <div className="question-reference">
        <h3>Question: {question?.questionText}</h3>
        <div className="total-marks">Total Marks: {mockMarkScheme.totalMarks}</div>
      </div>

      <div className="marking-criteria-section">
        <h4>Marking Criteria</h4>
        <div className="criteria-list">
          {mockMarkScheme.markingCriteria.map((criteria, index) => (
            <div key={index} className="criteria-item">
              <div className="criteria-header">
                <span className="step-label">Step {criteria.step}</span>
                <span className="marks-badge">{criteria.marks} mark{criteria.marks > 1 ? 's' : ''}</span>
              </div>
              <h5>{criteria.description}</h5>
              <p className="criteria-details">{criteria.details}</p>
              <div className="acceptable-answers">
                <strong>Acceptable answers:</strong>
                <ul>
                  {criteria.acceptableAnswers.map((answer, answerIndex) => (
                    <li key={answerIndex}>{answer}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="common-mistakes-section">
        <h4>Common Mistakes</h4>
        <div className="mistakes-list">
          {mockMarkScheme.commonMistakes.map((mistake, index) => (
            <div key={index} className="mistake-item">
              <h5>{mistake.mistake}</h5>
              <p>{mistake.description}</p>
              <div className="deduction-note">{mistake.deduction}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="teacher-notes-section">
        <h4>Teacher Notes</h4>
        <ul className="teacher-notes-list">
          {mockMarkScheme.teacherNotes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      </div>
    </div>
  );

  if (isChatMode) {
    return (
      <div className="mark-scheme-overlay">
        <div className="mark-scheme-chat-container">
          <div className="mark-scheme-chat-header">
            <h2>Mark Scheme Discussion</h2>
            <div className="chat-header-buttons">
              {onNextQuestion && (
                <button onClick={onNextQuestion} className="next-question-button">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M12 5L19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Next Question
                </button>
              )}
              <button onClick={handleChatToggle} className="back-to-scheme-button">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Back to Mark Scheme
              </button>
              <button onClick={onClose} className="close-button">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div className="mark-scheme-chat-content">
            {/* Left side - Mark Scheme */}
            <div className="mark-scheme-panel">
              {renderMarkSchemeContent()}
            </div>

            {/* Right side - Chat */}
            <div className="chat-panel">
              <div className="chat-header">
                <div className="chat-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 11.5C21 16.75 16.75 21 11.5 21C6.25 21 2 16.75 2 11.5C2 6.25 6.25 2 11.5 2C13.1 2 14.65 2.5 16 3.35" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M16.5 6.4C17.8 7.5 18.7 9 18.7 10.8C18.7 11.4 18.6 12 18.4 12.5" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M8.5 12.5H14.5" stroke="#4285F4" strokeWidth="1.5" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3>Ask about Mark Scheme</h3>
              </div>
              
              <div className="chat-messages">
                {chatMessages.length === 0 ? (
                  <div className="chat-placeholder">
                    <div className="placeholder-icon">
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H5.2L4 17.2V4H20V16Z" fill="#CBD5E0"/>
                      </svg>
                    </div>
                    <p>Ask me anything about this mark scheme!</p>
                  </div>
                ) : (
                  chatMessages.map((message) => (
                    <div key={message.id} className={`chat-message ${message.sender}`}>
                      <div className="message-content">
                        {message.content}
                      </div>
                      <div className="message-time">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="chat-message ai">
                    <div className="message-content typing">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleChatSubmit} className="chat-form">
                <div className="chat-input-group">
                  <input
                    type="text"
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Ask about the marking criteria, common mistakes, or anything else..."
                    className="chat-input"
                    disabled={isLoading}
                  />
                  <button 
                    type="submit" 
                    className="send-button"
                    disabled={isLoading || !currentMessage.trim()}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="white"/>
                    </svg>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mark-scheme-overlay">
      <div className="mark-scheme-container">
        <div className="mark-scheme-header">
          <h2>Mark Scheme</h2>
          <div className="header-buttons">
            <button onClick={handleChatToggle} className="chat-toggle-button">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H5.2L4 17.2V4H20V16Z" fill="currentColor"/>
              </svg>
              Ask Questions
            </button>
            <button onClick={onClose} className="close-button">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        {renderMarkSchemeContent()}
      </div>
    </div>
  );
};

export default MarkScheme; 