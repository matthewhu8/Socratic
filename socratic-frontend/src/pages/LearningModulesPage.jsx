import React, { useState, useContext, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/LearningModulesPage.css';
import API_URL from '../config/api';

function LearningModulesPage() {
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [videoTitle, setVideoTitle] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [player, setPlayer] = useState(null);
  const [videoPanelWidth, setVideoPanelWidth] = useState(50); // Changed from videoPanelHeight to videoPanelWidth
  const mainContentRef = useRef(null);
  const chatMessagesRef = useRef(null); // Add ref for chat messages container
  const isResizing = useRef(false);

  // Quiz state
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizData, setQuizData] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [transcriptReady, setTranscriptReady] = useState(false);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatMessages, isLoading]);

  const handleMouseDown = (e) => {
    isResizing.current = true;
    document.body.style.cursor = 'col-resize'; // Changed from 'row-resize' to 'col-resize'
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.current || !mainContentRef.current) return;
      
      const mainContent = mainContentRef.current;
      const rect = mainContent.getBoundingClientRect();
      
      // Calculate the new width as a percentage of the main content area
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      
      // Add constraints to prevent panels from becoming too small
      if (newWidth > 25 && newWidth < 75) {
        setVideoPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      if (isResizing.current) {
        isResizing.current = false;
        document.body.style.cursor = 'default';
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // Load YouTube Player API
  useEffect(() => {
    const loadYouTubeAPI = () => {
      if (window.YT && window.YT.Player) {
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      document.body.appendChild(script);

      window.onYouTubeIframeAPIReady = () => {
        console.log('YouTube API ready');
      };
    };

    loadYouTubeAPI();
  }, []);

  // Initialize YouTube player when video ID changes
  useEffect(() => {
    if (videoId && window.YT && window.YT.Player) {
      const playerInstance = new window.YT.Player('youtube-player', {
        videoId: videoId,
        events: {
          onReady: (event) => {
            console.log('Player ready');
            setPlayer(event.target);
          },
          onStateChange: (event) => {
            console.log('Player state changed:', event.data);
          }
        }
      });
    }
  }, [videoId]);

  // Extract YouTube video ID from URL
  const extractVideoId = (url) => {
    const regex = /(?:youtube\.com\/(?:[^/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?/\s]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
  };

  // Handle YouTube URL submission
  const handleUrlSubmit = (e) => {
    e.preventDefault();
    setError('');
    
    const extractedId = extractVideoId(youtubeUrl);
    if (extractedId) {
      setVideoId(extractedId);
      // Clear previous chat when loading new video
      setChatMessages([{
        role: 'assistant',
        content: 'Hi! I can help you understand this video. Feel free to ask me questions about the content, concepts, or anything you\'d like to learn more about!',
        timestamp: new Date().toISOString()
      }]);
      // eventually get the video title from the YouTube API
      setVideoTitle('Interactive YouTube Video');
      
      // Load and cache the transcript
      loadVideoTranscript(extractedId, youtubeUrl);
      setTranscriptReady(false); // Reset transcript ready state
    } else {
      setError('Please enter a valid YouTube URL');
    }
  };

  // Function to load and cache video transcript
  const loadVideoTranscript = async (videoId, videoUrl) => {
    try {
      const response = await fetch(`${API_URL}/api/video/load-transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          video_id: videoId,
          video_url: videoUrl
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Transcript loaded successfully:', data.message);
        setTranscriptReady(true);
      } else {
        console.error('Failed to load transcript');
        setTranscriptReady(false);
      }
    } catch (error) {
      console.error('Error loading video transcript:', error);
    }
  };

  // Function to get current video timestamp
  const getCurrentVideoTime = () => {
    if (player && typeof player.getCurrentTime === 'function') {
      try {
        return player.getCurrentTime();
      } catch (error) {
        console.log('Error getting video time:', error);
        return 0;
      }
    }
    return 0;
  };

  // Handle chat message submission
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim() || !videoId) return;

    // Get current video timestamp
    const currentTimestamp = getCurrentVideoTime();
    console.log('Current video timestamp:', currentTimestamp);

    // Ensure user is authenticated and has an ID
    if (!currentUser?.id) {
      setError('Please log in to continue chatting.');
      return;
    }

    const userMessage = {
      role: 'user',
      content: currentMessage,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMessage]);
    const messageToSend = currentMessage;
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const requestBody = {
        query: messageToSend,
        video_id: videoId,
        video_url: youtubeUrl,
        timestamp: currentTimestamp
      };

      const response = await fetch(`${API_URL}/chat-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear video and chat
  const clearVideo = () => {
    setVideoId('');
    setYoutubeUrl('');
    setVideoTitle('');
    setChatMessages([]);
    setError('');
    setPlayer(null);
    // Reset quiz state
    setShowQuiz(false);
    setQuizData(null);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setShowResults(false);
    setTranscriptReady(false);
  };

  // Generate quiz
  const generateQuiz = async () => {
    if (!videoId || !youtubeUrl) {
      setError('No video loaded to generate quiz from');
      return;
    }

    setQuizLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/youtube-video-quiz`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          video_id: videoId,
          video_url: youtubeUrl
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Quiz response:', data);
        
        // Parse the quiz JSON string
        const parsedQuiz = JSON.parse(data.quiz);
        setQuizData(parsedQuiz);
        setShowQuiz(true);
        setCurrentQuestionIndex(0);
        setSelectedAnswers({});
        setShowResults(false);
      } else {
        throw new Error('Failed to generate quiz');
      }
    } catch (error) {
      console.error('Error generating quiz:', error);
      setError('Failed to generate quiz. Please try again.');
    } finally {
      setQuizLoading(false);
    }
  };

  // Handle quiz answer selection
  const handleAnswerSelect = (questionId, selectedOption) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: selectedOption
    }));
  };

  // Navigate quiz questions
  const nextQuestion = () => {
    if (currentQuestionIndex < quizData.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  // Submit quiz and show results
  const submitQuiz = () => {
    setShowResults(true);
  };

  // Calculate quiz score
  const calculateScore = () => {
    if (!quizData || !quizData.questions) return { correct: 0, total: 0, percentage: 0 };

    let correct = 0;
    const total = quizData.questions.length;

    quizData.questions.forEach(question => {
      const selectedAnswer = selectedAnswers[question.id];
      if (selectedAnswer === question.correct_answer) {
        correct++;
      }
    });

    return {
      correct,
      total,
      percentage: Math.round((correct / total) * 100)
    };
  };

  // Close quiz
  const closeQuiz = () => {
    setShowQuiz(false);
    setQuizData(null);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setShowResults(false);
  };

  // Function to format AI response text
  const formatResponse = (text) => {
    if (!text) return text;
    
    // Split by line breaks and process each line
    return text.split('\n').map((line, index) => {
      // Handle bullet points
      if (line.trim().startsWith('•') || line.trim().startsWith('-') || line.trim().startsWith('*')) {
        return (
          <div key={index} className="bullet-point">
            {line.trim()}
          </div>
        );
      }
      // Handle numbered lists
      else if (/^\d+\./.test(line.trim())) {
        return (
          <div key={index} className="numbered-point">
            {line.trim()}
          </div>
        );
      }
      // Handle empty lines (add spacing)
      else if (line.trim() === '') {
        return <br key={index} />;
      }
      // Regular text
      else {
        return (
          <div key={index} className="text-line">
            {line}
          </div>
        );
      }
    });
  };

  return (
    <div className="learning-modules-container">
      {/* Back Button */}
      <button 
        onClick={() => navigate(-1)} 
        style={{ position: 'absolute', top: 24, left: 24, padding: '8px 16px', fontSize: '16px', cursor: 'pointer', borderRadius: '6px', border: '1px solid #ccc', background: '#fff' }}
      >
        ← Back
      </button>

      {/* Header - only show when video is loaded */}
      {videoId && (
        <div className="learning-modules-header">
          <div className="header-content">
            <h1>Learning Modules</h1>
            <p>Watch YouTube videos and get AI-powered assistance to enhance your learning</p>
          </div>
        </div>
      )}

      {/* YouTube URL Input - only show when no video is loaded */}
      {!videoId && (
        <div className={`url-input-section ${!videoId ? 'centered' : ''}`}>
          <div className="url-input-header">
            <h1>Learning Modules</h1>
            <p>Paste a YouTube URL below to get started with AI-powered video learning</p>
          </div>
          <form onSubmit={handleUrlSubmit} className="url-form">
            <div className="input-group">
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="Paste YouTube URL here (e.g., https://www.youtube.com/watch?v=...)"
                className="url-input"
                required
              />
              <button type="submit" className="load-button">
                Load Video
              </button>
            </div>
            {error && <div className="error-message">{error}</div>}
          </form>
        </div>
      )}

      {/* Main Content Area - only show when video is loaded */}
      {videoId && (
        <div 
          className="main-content" 
          ref={mainContentRef}
          style={{ gridTemplateColumns: `${videoPanelWidth}% auto 1fr`, userSelect: isResizing.current ? 'none' : 'auto' }}
        >
          {/* Video Section */}
          <div className="video-section">
            <div className="video-header">
              <h2>{videoTitle}</h2>
              <div className="video-header-buttons">
                <button onClick={clearVideo} className="clear-button">
                  Load New Video
                </button>
                <button 
                  onClick={generateQuiz} 
                  className="quiz-button" 
                  disabled={!transcriptReady || quizLoading}
                >
                  {quizLoading ? 'Generating...' : !transcriptReady ? 'Loading Transcript...' : 'Generate Quiz'}
                </button>
              </div>
            </div>
            <div className="video-container">
              <div id="youtube-player"></div>
            </div>
          </div>

          <div className="resizer vertical" onMouseDown={handleMouseDown}></div>

          {/* Chat Section */}
          <div className="chat-section">
            <div className="chat-header">
              <h3>Ask Questions About This Video</h3>
              <p>I can help explain concepts, provide additional context, or answer questions about the video content.</p>
            </div>
            
            <div className="chat-messages" ref={chatMessagesRef}>
              {chatMessages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <div className="message-content">
                    {formatResponse(message.content)}
                  </div>
                  <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message assistant">
                  <div className="message-content">
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
                  placeholder="Ask a question about th"
                  className="chat-input"
                  disabled={isLoading}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isLoading || !currentMessage.trim()}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quiz Overlay */}
      {showQuiz && quizData && (
        <div className="quiz-overlay">
          <div className="quiz-container">
            <div className="quiz-header">
              <h2>{quizData.quiz_title}</h2>
              <button onClick={closeQuiz} className="close-quiz-button">×</button>
            </div>
            
            {!showResults ? (
              <div className="quiz-content">
                <div className="quiz-progress">
                  Question {currentQuestionIndex + 1} of {quizData.questions.length}
                </div>
                
                {quizData.questions[currentQuestionIndex] && (
                  <div className="question-container">
                    <h3 className="question-text">
                      {quizData.questions[currentQuestionIndex].question}
                    </h3>
                    
                    <div className="options-container">
                      {['option1', 'option2', 'option3'].map((optionKey, index) => {
                        const option = quizData.questions[currentQuestionIndex][optionKey];
                        const questionId = quizData.questions[currentQuestionIndex].id;
                        const isSelected = selectedAnswers[questionId] === option;
                        
                        return (
                          <div
                            key={index}
                            className={`option ${isSelected ? 'selected' : ''}`}
                            onClick={() => handleAnswerSelect(questionId, option)}
                          >
                            <div className="option-letter">{String.fromCharCode(65 + index)}</div>
                            <div className="option-text">{option}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                <div className="quiz-navigation">
                  <button 
                    onClick={prevQuestion} 
                    disabled={currentQuestionIndex === 0}
                    className="nav-button prev-button"
                  >
                    Previous
                  </button>
                  
                  {currentQuestionIndex === quizData.questions.length - 1 ? (
                    <button onClick={submitQuiz} className="nav-button submit-button">
                      Submit Quiz
                    </button>
                  ) : (
                    <button onClick={nextQuestion} className="nav-button next-button">
                      Next
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="quiz-results">
                <h3>Quiz Results</h3>
                <div className="score-display">
                  <div className="score-circle">
                    <span className="score-percentage">{calculateScore().percentage}%</span>
                  </div>
                  <p>You got {calculateScore().correct} out of {calculateScore().total} questions correct!</p>
                </div>
                
                <div className="results-details">
                  {quizData.questions.map((question, index) => {
                    const userAnswer = selectedAnswers[question.id];
                    const isCorrect = userAnswer === question.correct_answer;
                    
                    return (
                      <div key={question.id} className={`result-item ${isCorrect ? 'correct' : 'incorrect'}`}>
                        <div className="result-header">
                          <span className="question-number">Q{index + 1}</span>
                          <span className={`result-status ${isCorrect ? 'correct' : 'incorrect'}`}>
                            {isCorrect ? '✓' : '✗'}
                          </span>
                        </div>
                        <p className="result-question">{question.question}</p>
                        <p className="result-answers">
                          <span className={`user-answer ${isCorrect ? 'correct' : 'incorrect'}`}>
                            Your answer: {userAnswer || 'Not answered'}
                          </span>
                          {!isCorrect && (
                            <span className="correct-answer">
                              Correct answer: {question.correct_answer}
                            </span>
                          )}
                        </p>
                      </div>
                    );
                  })}
                </div>
                
                <div className="results-actions">
                  <button onClick={closeQuiz} className="close-results-button">
                    Close Quiz
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default LearningModulesPage; 