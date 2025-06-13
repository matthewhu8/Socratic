import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/DynamicLearningPage.css';

function DynamicLearningPage() {
  const navigate = useNavigate();

  return (
    <div className="dynamic-learning-container">
      {/* Back Button */}
      <button 
        onClick={() => navigate('/student/home')} 
        style={{ 
          position: 'absolute', 
          top: 24, 
          left: 24, 
          padding: '8px 16px', 
          fontSize: '16px', 
          cursor: 'pointer', 
          borderRadius: '6px', 
          border: '1px solid #ccc', 
          background: '#fff',
          color: '#2c3e50',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = '#f8f9fa';
          e.target.style.borderColor = '#3498db';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = '#fff';
          e.target.style.borderColor = '#ccc';
        }}
      >
        ← Back to Home
      </button>

      {/* Main Content */}
      <div className="dynamic-learning-content">
        <div className="coming-soon-card">
          <div className="coming-soon-icon">🚀</div>
          <h1>Dynamic Learning</h1>
          <div className="beta-badge">Pre-Beta</div>
          <p className="coming-soon-message">
            We are currently in Pre-Beta Testing. Stay tuned for updates about this feature's release.
          </p>
          <div className="feature-preview">
            <h3>What to Expect:</h3>
            <ul>
              <li>Adaptive AI-powered learning experiences</li>
              <li>Personalized content based on your progress</li>
              <li>Interactive learning modules</li>
              <li>Real-time performance adjustments</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DynamicLearningPage; 