import React, { useState, useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/LearningModulesPage.css';
import API_URL from '../config/api';

function LearningModulesPage() {
  const { currentUser } = useContext(AuthContext);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [videoTitle, setVideoTitle] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [player, setPlayer] = useState(null);

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
    } else {
      setError('Please enter a valid YouTube URL');
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
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          query: currentMessage,
          video_id: videoId,
          video_url: youtubeUrl,
          timestamp: currentTimestamp
        })
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
  };

  return (
    <div className="learning-modules-container">
      {/* Header */}
      <div className="learning-modules-header">
        <div className="header-content">
          <Link to="/student/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
          <h1>Learning Modules</h1>
          <p>Watch YouTube videos and get AI-powered assistance to enhance your learning</p>
        </div>
      </div>

      {/* YouTube URL Input */}
      <div className="url-input-section">
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

      {/* Main Content Area */}
      {videoId ? (
        <div className="main-content">
          {/* Video Section */}
          <div className="video-section">
            <div className="video-header">
              <h2>{videoTitle}</h2>
              <button onClick={clearVideo} className="clear-button">
                Load New Video
              </button>
            </div>
            <div className="video-container">
              <div id="youtube-player"></div>
            </div>
          </div>

          {/* Chat Section */}
          <div className="chat-section">
            <div className="chat-header">
              <h3>Ask Questions About This Video</h3>
              <p>I can help explain concepts, provide additional context, or answer questions about the video content.</p>
            </div>
            
            <div className="chat-messages">
              {chatMessages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <div className="message-content">
                    {message.content}
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
                  placeholder="Ask a question about the video..."
                  className="chat-input"
                  disabled={isLoading}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isLoading || !currentMessage.trim()}
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-content">
            <div className="empty-state-icon">📺</div>
            <h2>Ready to Learn?</h2>
            <p>Paste a YouTube URL above to get started. Once loaded, you can watch the video and ask me questions about the content!</p>
            <div className="example-urls">
              <h4>Try these example videos:</h4>
              <button 
                onClick={() => setYoutubeUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ')}
                className="example-button"
              >
                Sample Educational Video
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LearningModulesPage; 