import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { TbFlask } from 'react-icons/tb';
import '../styles/SubjectPage.css';

const chemistryTopicsByGrade = {
  9: [
    {
      title: 'Atomic Structure',
      description: 'Basic structure of atoms and periodic table.',
      path: '/student/dynamic-learning/chemistry/grade-9/atomic-structure',
    },
    {
      title: 'Chemical Bonding',
      description: 'Ionic and covalent bonds.',
      path: '/student/dynamic-learning/chemistry/grade-9/chemical-bonding',
    },
    {
      title: 'Chemical Reactions',
      description: 'Types of chemical reactions and balancing equations.',
      path: '/student/dynamic-learning/chemistry/grade-9/chemical-reactions',
    },
  ],
  10: [
    {
      title: 'States of Matter',
      description: 'Solids, liquids, gases, and phase changes.',
      path: '/student/dynamic-learning/chemistry/grade-10/states-of-matter',
    },
    {
      title: 'Solutions and Mixtures',
      description: 'Concentration, solubility, and separation techniques.',
      path: '/student/dynamic-learning/chemistry/grade-10/solutions-and-mixtures',
    },
    {
      title: 'Chemical Formulas',
      description: 'Writing and interpreting chemical formulas.',
      path: '/student/dynamic-learning/chemistry/grade-10/chemical-formulas',
    },
  ],
  11: [
    {
      title: 'Acids and Bases',
      description: 'Properties, reactions, and pH scale.',
      path: '/student/dynamic-learning/chemistry/grade-11/acids-and-bases',
    },
    {
      title: 'Redox Reactions',
      description: 'Oxidation and reduction processes.',
      path: '/student/dynamic-learning/chemistry/grade-11/redox-reactions',
    },
    {
      title: 'Thermochemistry',
      description: 'Energy changes in chemical reactions.',
      path: '/student/dynamic-learning/chemistry/grade-11/thermochemistry',
    },
  ],
  12: [
    {
      title: 'Organic Chemistry',
      description: 'Basic principles and reactions of organic compounds.',
      path: '/student/dynamic-learning/chemistry/grade-12/organic-chemistry',
    },
    {
      title: 'Chemical Equilibrium',
      description: 'Dynamic equilibrium and Le Chatelier\'s principle.',
      path: '/student/dynamic-learning/chemistry/grade-12/chemical-equilibrium',
    },
    {
      title: 'Electrochemistry',
      description: 'Galvanic cells and electrolysis.',
      path: '/student/dynamic-learning/chemistry/grade-12/electrochemistry',
    },
  ],
};

function ChemistryPage() {
  const navigate = useNavigate();
  const { gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  const topics = chemistryTopicsByGrade[gradeNumber] || [];

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} Chemistry content coming soon!</h1>
      </div>
    );
  }

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
          <h1 style={{ color: '#4caf50' }}>Chemistry - Grade {grade}</h1>
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

export default ChemistryPage; 