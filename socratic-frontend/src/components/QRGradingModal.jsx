import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import API_URL from '../config/api';
import './QRGradingModal.css';

const QRGradingModal = ({ 
  isOpen, 
  onClose, 
  sessionId, 
  qrCodeUrl, 
  expiresIn,
  onGradingComplete 
}) => {
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(expiresIn);
  const [status, setStatus] = useState('waiting'); // waiting, connected, processing, completed
  const [gradingResult, setGradingResult] = useState(null);

  // Generate QR code
  useEffect(() => {
    if (qrCodeUrl) {
      QRCode.toDataURL(qrCodeUrl, {
        width: 300,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      })
      .then(url => setQrCodeDataUrl(url))
      .catch(err => console.error('Error generating QR code:', err));
    }
  }, [qrCodeUrl]);

  // Countdown timer
  useEffect(() => {
    if (timeRemaining > 0 && isOpen) {
      const timer = setTimeout(() => {
        setTimeRemaining(timeRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [timeRemaining, isOpen]);

  // Poll for grading results
  useEffect(() => {
    if (!sessionId || !isOpen) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/grading-session/${sessionId}/result`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.status === 'mobile_connected' && status === 'waiting') {
            setStatus('connected');
          } else if (data.status === 'image_uploaded' && status !== 'processing') {
            setStatus('processing');
          } else if (data.status === 'completed' && data.result) {
            setStatus('completed');
            setGradingResult(data.result);
            clearInterval(pollInterval);
            onGradingComplete(data.result);
          }
        }
      } catch (error) {
        console.error('Error polling for results:', error);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [sessionId, isOpen, status, onGradingComplete]);

  if (!isOpen) return null;

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="qr-modal-overlay" onClick={onClose}>
      <div className="qr-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="qr-modal-close" onClick={onClose}>×</button>
        
        {status === 'completed' && gradingResult ? (
          <div className="grading-result">
            <h2>Grading Complete!</h2>
            <div className="grade-display">
              <span className="grade-label">Score:</span>
              <span className="grade-value">{gradingResult.grade}</span>
            </div>
            <div className="feedback-section">
              <h3>Feedback</h3>
              <p>{gradingResult.feedback}</p>
            </div>
            {gradingResult.corrections && gradingResult.corrections.length > 0 && (
              <div className="corrections-section">
                <h3>Corrections</h3>
                <ul>
                  {gradingResult.corrections.map((correction, index) => (
                    <li key={index}>{correction}</li>
                  ))}
                </ul>
              </div>
            )}
            {gradingResult.strengths && gradingResult.strengths.length > 0 && (
              <div className="strengths-section">
                <h3>Strengths</h3>
                <ul>
                  {gradingResult.strengths.map((strength, index) => (
                    <li key={index}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}
            <button className="close-button" onClick={onClose}>Close</button>
          </div>
        ) : (
          <>
            <h2>Submit for Grading</h2>
            
            <div className="status-indicator">
              {status === 'waiting' && <p>Waiting for mobile device...</p>}
              {status === 'connected' && <p className="connected">📱 Mobile device connected!</p>}
              {status === 'processing' && <p className="processing">🔄 Processing your submission...</p>}
            </div>

            <div className="qr-code-container">
              {qrCodeDataUrl && (
                <img src={qrCodeDataUrl} alt="QR Code for grading" />
              )}
            </div>

            <div className="instructions">
              <h3>Instructions:</h3>
              <ol>
                <li>Scan the QR code with your phone's camera</li>
                <li>Take a clear photo of your written work</li>
                <li>Submit for instant grading</li>
              </ol>
            </div>

            <div className="timer">
              <p>Time remaining: <span className={timeRemaining < 60 ? 'urgent' : ''}>
                {formatTime(timeRemaining)}
              </span></p>
            </div>

            <div className="session-info">
              <p>Session ID: {sessionId}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QRGradingModal; 