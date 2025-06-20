import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { IoFlashOutline } from 'react-icons/io5';
import '../styles/SubjectPage.css';

const physicsTopicsByGrade = {
  9: [
    {
      title: 'Motion and Forces',
      description: 'Basic concepts of motion and Newton\'s laws.',
      path: '/student/dynamic-learning/physics/grade-9/motion-and-forces',
    },
    {
      title: 'Energy and Work',
      description: 'Understanding kinetic and potential energy.',
      path: '/student/dynamic-learning/physics/grade-9/energy-and-work',
    },
    {
      title: 'Simple Machines',
      description: 'Levers, pulleys, and mechanical advantage.',
      path: '/student/dynamic-learning/physics/grade-9/simple-machines',
    },
  ],
  10: [
    {
      title: 'Waves and Sound',
      description: 'Properties of waves and sound phenomena.',
      path: '/student/dynamic-learning/physics/grade-10/waves-and-sound',
    },
    {
      title: 'Light and Optics',
      description: 'Reflection, refraction, and lenses.',
      path: '/student/dynamic-learning/physics/grade-10/light-and-optics',
    },
    {
      title: 'Heat and Temperature',
      description: 'Thermal energy and heat transfer.',
      path: '/student/dynamic-learning/physics/grade-10/heat-and-temperature',
    },
  ],
  11: [
    {
      title: 'Electricity Basics',
      description: 'Current, voltage, and resistance.',
      path: '/student/dynamic-learning/physics/grade-11/electricity-basics',
    },
    {
      title: 'Magnetism',
      description: 'Magnetic fields and electromagnetic induction.',
      path: '/student/dynamic-learning/physics/grade-11/magnetism',
    },
    {
      title: 'Mechanics',
      description: 'Advanced motion and gravitation.',
      path: '/student/dynamic-learning/physics/grade-11/mechanics',
    },
  ],
  12: [
    {
      title: 'Electromagnetism',
      description: 'Electric and magnetic fields, electromagnetic waves.',
      path: '/student/dynamic-learning/physics/grade-12/electromagnetism',
    },
    {
      title: 'Modern Physics',
      description: 'Quantum mechanics and relativity basics.',
      path: '/student/dynamic-learning/physics/grade-12/modern-physics',
    },
    {
      title: 'Nuclear Physics',
      description: 'Atomic structure and radioactivity.',
      path: '/student/dynamic-learning/physics/grade-12/nuclear-physics',
    },
  ],
};

function PhysicsPage() {
  const navigate = useNavigate();
  const { gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  const topics = physicsTopicsByGrade[gradeNumber] || [];

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} Physics content coming soon!</h1>
      </div>
    );
  }

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
          <h1 style={{ color: '#9c27b0' }}>Physics - Grade {grade}</h1>
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

export default PhysicsPage; 