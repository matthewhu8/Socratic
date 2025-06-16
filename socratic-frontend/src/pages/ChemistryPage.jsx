import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TbFlask } from 'react-icons/tb';
import '../styles/SubjectPage.css';

const chemistryTopics = [
  {
    title: 'Acids and Bases',
    description: 'Properties, reactions, and titrations.',
    path: '/student/dynamic-learning/chemistry/acids-and-bases',
  },
  {
    title: 'Organic Chemistry',
    description: 'Basic principles and reactions of organic compounds.',
    path: '/student/dynamic-learning/chemistry/organic-chemistry',
  },
];

function ChemistryPage() {
  const navigate = useNavigate();

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: '#e8f5e9', color: '#4caf50' }}>
          <TbFlask />
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: '#4caf50' }}>Chemistry</h1>
          <p>Choose a chapter to begin</p>
        </div>
      </header>

      <main className="topics-grid">
        {chemistryTopics.map((topic) => (
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

export default ChemistryPage; 