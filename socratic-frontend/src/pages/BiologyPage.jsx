import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { FaHeart } from 'react-icons/fa';
import '../styles/SubjectPage.css';

const biologyTopicsByGrade = {
  9: [
    {
      title: 'Cell Structure',
      description: 'Basic structure and function of plant and animal cells.',
      path: '/student/dynamic-learning/biology/grade-9/cell-structure',
    },
    {
      title: 'Classification of Living Things',
      description: 'Five kingdom classification system.',
      path: '/student/dynamic-learning/biology/grade-9/classification',
    },
    {
      title: 'Basic Ecology',
      description: 'Ecosystems, food chains, and environmental factors.',
      path: '/student/dynamic-learning/biology/grade-9/basic-ecology',
    },
  ],
  10: [
    {
      title: 'Photosynthesis',
      description: 'Process of photosynthesis and its importance.',
      path: '/student/dynamic-learning/biology/grade-10/photosynthesis',
    },
    {
      title: 'Respiration',
      description: 'Cellular respiration and energy production.',
      path: '/student/dynamic-learning/biology/grade-10/respiration',
    },
    {
      title: 'Human Body Systems',
      description: 'Overview of major body systems.',
      path: '/student/dynamic-learning/biology/grade-10/human-body-systems',
    },
  ],
  11: [
    {
      title: 'Cell Biology',
      description: 'Advanced cell structure and function.',
      path: '/student/dynamic-learning/biology/grade-11/cell-biology',
    },
    {
      title: 'Genetics Basics',
      description: 'DNA, genes, and basic inheritance patterns.',
      path: '/student/dynamic-learning/biology/grade-11/genetics-basics',
    },
    {
      title: 'Evolution',
      description: 'Theory of evolution and natural selection.',
      path: '/student/dynamic-learning/biology/grade-11/evolution',
    },
  ],
  12: [
    {
      title: 'Advanced Genetics',
      description: 'Molecular genetics and genetic engineering.',
      path: '/student/dynamic-learning/biology/grade-12/advanced-genetics',
    },
    {
      title: 'Biotechnology',
      description: 'Applications of biology in technology.',
      path: '/student/dynamic-learning/biology/grade-12/biotechnology',
    },
    {
      title: 'Human Physiology',
      description: 'Detailed study of human body functions.',
      path: '/student/dynamic-learning/biology/grade-12/human-physiology',
    },
  ],
};

function BiologyPage() {
  const navigate = useNavigate();
  const { gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  const topics = biologyTopicsByGrade[gradeNumber] || [];

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} Biology content coming soon!</h1>
      </div>
    );
  }

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: '#ffebee', color: '#f44336' }}>
          <FaHeart />
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: '#f44336' }}>Biology - Grade {grade}</h1>
          <p>Choose a chapter to begin</p>
        </div>
      </header>

      <main className="topics-grid">
        {topics.map((topic) => (
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

export default BiologyPage; 