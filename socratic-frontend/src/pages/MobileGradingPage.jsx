import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API_URL from '../config/api';
import '../styles/MobileGradingPage.css';

const MobileGradingPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
  const [sessionValid, setSessionValid] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Validate session on mount
  useEffect(() => {
    validateSession();
  }, [sessionId]);

  const validateSession = async () => {
    try {
      // Extract token from URL params
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');
      
      if (!token) {
        throw new Error('Invalid session access');
      }

      // Store token temporarily
      sessionStorage.setItem('gradingToken', token);

      // Validate session with backend
      const response = await fetch(`${API_URL}/api/validate-grading-session/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Session expired or invalid');
      }

      const data = await response.json();
      setSessionData(data);
      setSessionValid(true);
      
      // Mark session as mobile connected
      await fetch(`${API_URL}/api/grading-session/${sessionId}/connect-mobile`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

    } catch (error) {
      console.error('Session validation failed:', error);
      setError(error.message);
      setSessionValid(false);
    } finally {
      setLoading(false);
    }
  };

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      console.error('Camera access error:', error);
      setError('Unable to access camera. Please check permissions.');
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      setCameraActive(false);
    }
  };

  // Capture image
  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to blob
    canvas.toBlob((blob) => {
      setCapturedImage({
        blob: blob,
        url: canvas.toDataURL('image/jpeg', 0.9),
        size: blob.size,
        timestamp: new Date().toISOString()
      });
      stopCamera();
    }, 'image/jpeg', 0.9);
  };

  // Submit image
  const submitImage = async () => {
    if (!capturedImage) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('image', capturedImage.blob, `submission_${sessionId}.jpg`);
      formData.append('sessionId', sessionId);
      formData.append('timestamp', capturedImage.timestamp);
      formData.append('imageSize', capturedImage.size);
      
      // Add metadata
      formData.append('metadata', JSON.stringify({
        userAgent: navigator.userAgent,
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        captureTime: capturedImage.timestamp,
        sessionData: {
          questionId: sessionData.questionId,
          subject: sessionData.subject,
          grade: sessionData.grade
        }
      }));

      const token = sessionStorage.getItem('gradingToken');
      const response = await fetch(`${API_URL}/api/submit-grading-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setUploadSuccess(true);
      
      // Clear session token
      sessionStorage.removeItem('gradingToken');
      
    } catch (error) {
      console.error('Image submission failed:', error);
      setError('Failed to submit image. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // Retake photo
  const retakePhoto = () => {
    setCapturedImage(null);
    startCamera();
  };

  // Loading state
  if (loading) {
    return (
      <div className="mobile-grading-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Validating session...</p>
        </div>
      </div>
    );
  }

  // Invalid session
  if (!sessionValid) {
    return (
      <div className="mobile-grading-container">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h2>Session Invalid</h2>
          <p>{error || 'This grading session has expired or is invalid.'}</p>
        </div>
      </div>
    );
  }

  // Success state
  if (uploadSuccess) {
    return (
      <div className="mobile-grading-container">
        <div className="success-state">
          <div className="success-icon">✅</div>
          <h2>Submission Successful!</h2>
          <p>Your work has been submitted for grading.</p>
          <p>Check your computer screen for results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-grading-container">
      <header className="mobile-header">
        <h1>Submit for Grading</h1>
        {sessionData && (
          <div className="session-info">
            <p>{sessionData.subject} - Grade {sessionData.grade}</p>
            {sessionData.topic && <p>{sessionData.topic}</p>}
          </div>
        )}
      </header>

      <main className="mobile-main">
        {!cameraActive && !capturedImage && (
          <div className="start-camera-section">
            <div className="question-preview">
              <h3>Question:</h3>
              <p>{sessionData?.questionText}</p>
            </div>
            <button className="start-camera-btn" onClick={startCamera}>
              📸 Open Camera
            </button>
            <p className="instructions">Take a clear photo of your written work</p>
          </div>
        )}

        {cameraActive && !capturedImage && (
          <div className="camera-section">
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline
              className="camera-preview"
            />
            <div className="camera-controls">
              <button className="cancel-btn" onClick={stopCamera}>Cancel</button>
              <button className="capture-btn" onClick={captureImage}>
                <div className="capture-icon"></div>
              </button>
            </div>
          </div>
        )}

        {capturedImage && (
          <div className="preview-section">
            <img 
              src={capturedImage.url} 
              alt="Captured work" 
              className="captured-preview"
            />
            <div className="preview-controls">
              <button 
                className="retake-btn" 
                onClick={retakePhoto}
                disabled={uploading}
              >
                Retake
              </button>
              <button 
                className="submit-btn" 
                onClick={submitImage}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Submit'}
              </button>
            </div>
            {error && <p className="error-message">{error}</p>}
          </div>
        )}

        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </main>
    </div>
  );
};

export default MobileGradingPage; 