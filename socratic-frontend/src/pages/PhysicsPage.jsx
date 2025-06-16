import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { IoFlashOutline } from 'react-icons/io5';
import '../styles/SubjectPage.css';

const physicsTopics = [
  {
    title: 'Mechanics',
    description: "Newton's laws of motion and gravitation.",
    path: '/student/dynamic-learning/physics/mechanics',
  },
  {
    title: 'Electromagnetism',
    description: 'Electric fields, magnetic fields, and electromagnetic waves.',
    path: '/student/dynamic-learning/physics/electromagnetism',
  },
];

function PhysicsPage() {
  const navigate = useNavigate();

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: '#f3e5f5', color: '#9c27b0' }}>
          <IoFlashOutline />
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: '#9c27b0' }}>Physics</h1>
          <p>Choose a chapter to begin</p>
        </div>
      </header>

      <main className="topics-grid">
        {physicsTopics.map((topic) => (
          <Link key={topic.title} to={topic.path} className="topic-card-link">
            <div className="topic-card-item">
              <div className="topic-details">
                <h3>{topic.title}</h3>
                <p>{topic.description}</p>
              </div>
              <div className="topic-arrow-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          </Link>
        ))}
      </main>
    </div>
  );
}

export default PhysicsPage; 