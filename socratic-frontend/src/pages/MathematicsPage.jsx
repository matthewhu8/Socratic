import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { TbMathFunction } from 'react-icons/tb';
import '../styles/SubjectPage.css';

const mathematicsTopicsByGrade = {
  9: [
    {
      title: 'Linear Equations',
      description: 'Solving equations with one variable.',
      path: '/student/dynamic-learning/mathematics/grade-9/linear-equations',
    },
    {
      title: 'Quadratic Functions',
      description: 'Understanding parabolas and quadratic equations.',
      path: '/student/dynamic-learning/mathematics/grade-9/quadratic-functions',
    },
    {
      title: 'Basic Geometry',
      description: 'Properties of shapes and angles.',
      path: '/student/dynamic-learning/mathematics/grade-9/basic-geometry',
    },
  ],
  10: [
    {
      title: 'Real Numbers',
      description: 'Fundamental concepts of real numbers.',
      path: '/student/dynamic-learning/mathematics/grade-10/trigonometry-basics',
    }
  ],
  11: [
    {
      title: 'Advanced Trigonometry',
      description: 'Trigonometric identities and equations.',
      path: '/student/dynamic-learning/mathematics/grade-11/advanced-trigonometry',
    },
    {
      title: 'Logarithmic Functions',
      description: 'Properties and applications of logarithms.',
      path: '/student/dynamic-learning/mathematics/grade-11/logarithmic-functions',
    },
    {
      title: 'Sequences and Series',
      description: 'Arithmetic and geometric progressions.',
      path: '/student/dynamic-learning/mathematics/grade-11/sequences-and-series',
    },
  ],
  12: [
    {
      title: 'Calculus - Limits',
      description: 'Introduction to limits and continuity.',
      path: '/student/dynamic-learning/mathematics/grade-12/calculus-limits',
    },
    {
      title: 'Calculus - Derivatives',
      description: 'Differentiation and its applications.',
      path: '/student/dynamic-learning/mathematics/grade-12/calculus-derivatives',
    },
    {
      title: 'Calculus - Integrals',
      description: 'Integration and area under curves.',
      path: '/student/dynamic-learning/mathematics/grade-12/calculus-integrals',
    },
  ],
};

function MathematicsPage() {
  const navigate = useNavigate();
  const { gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  const topics = mathematicsTopicsByGrade[gradeNumber] || [];

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} Mathematics content coming soon!</h1>
      </div>
    );
  }

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: '#e8f0fe', color: '#4285f4' }}>
          <TbMathFunction />
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: '#4285f4' }}>Mathematics - Grade {grade}</h1>
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

export default MathematicsPage; 