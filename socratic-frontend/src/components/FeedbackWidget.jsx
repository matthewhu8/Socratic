import React, { useState } from 'react';
import './FeedbackWidget.css';
import API_URL from '../config/api';

const FeedbackWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState('suggestion');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const response = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: feedbackType,
          description,
          email,
          timestamp: new Date().toISOString(),
        }),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setTimeout(() => {
          setIsOpen(false);
          setFeedbackType('suggestion');
          setDescription('');
          setEmail('');
          setSubmitStatus(null);
        }, 2000);
      } else {
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <button 
        className="feedback-widget"
        onClick={() => setIsOpen(true)}
        aria-label="Provide feedback"
      >
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            d="M8 10H16M8 14H13M7 2C4.23858 2 2 4.23858 2 7V15C2 17.7614 4.23858 20 7 20H8L11.6464 23.6464C11.8417 23.8417 12.1583 23.8417 12.3536 23.6464L16 20H17C19.7614 20 22 17.7614 22 15V7C22 4.23858 19.7614 2 17 2H7Z" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
        <span>Feedback</span>
      </button>

      {isOpen && (
        <div className="feedback-modal-overlay" onClick={() => setIsOpen(false)}>
          <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
            <div className="feedback-modal-header">
              <h2>Send us your feedback</h2>
              <button 
                className="feedback-close-button"
                onClick={() => setIsOpen(false)}
                aria-label="Close feedback form"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="feedback-form">
              <div className="feedback-form-group">
                <label htmlFor="feedback-type">Feedback Type</label>
                <select
                  id="feedback-type"
                  value={feedbackType}
                  onChange={(e) => setFeedbackType(e.target.value)}
                  required
                >
                  <option value="suggestion">Suggestion</option>
                  <option value="feature">Feature Request</option>
                  <option value="bug">Bug Report</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="feedback-form-group">
                <label htmlFor="feedback-description">Description</label>
                <textarea
                  id="feedback-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Please describe your feedback in detail..."
                  rows="5"
                  required
                />
              </div>

              <div className="feedback-form-group">
                <label htmlFor="feedback-email">Email (optional)</label>
                <input
                  type="email"
                  id="feedback-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                />
              </div>

              {submitStatus === 'success' && (
                <div className="feedback-success">
                  Thank you for your feedback! We'll review it soon.
                </div>
              )}

              {submitStatus === 'error' && (
                <div className="feedback-error">
                  Sorry, there was an error submitting your feedback. Please try again.
                </div>
              )}

              <div className="feedback-form-actions">
                <button 
                  type="button" 
                  className="feedback-cancel-button"
                  onClick={() => setIsOpen(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="feedback-submit-button"
                  disabled={isSubmitting || !description.trim()}
                >
                  {isSubmitting ? 'Sending...' : 'Send Feedback'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackWidget;