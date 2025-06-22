import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { TbBook, TbFileText, TbBrain } from 'react-icons/tb';
import '../styles/PracticeModePage.css';

// Helper to format text (e.g., 'cell-biology' -> 'Cell Biology')
const formatBreadcrumb = (str) => {
  if (!str) return '';
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

function PracticeModePage() {
  const { subject, subtopic, gradeParam } = useParams();
  const navigate = useNavigate();

  // Handle both old routing (with subtopic) and new routing (with gradeParam)
  const isGradeLevel = gradeParam && !subtopic;
  const grade = isGradeLevel ? gradeParam?.replace('grade-', '') : null;

  const practiceOptions = [
    {
      title: 'NCERT Examples',
      description: 'Practice with examples from NCERT textbooks',
      icon: <TbBook />,
      color: '#4285f4',
      bgColor: '#e8f0fe',
      path: isGradeLevel 
        ? `/student/dynamic-learning/${subject}/grade-${grade}/ncert-topics`
        : `/student/practice/${subject}/${subtopic}/ncert-examples`,
    },
    {
      title: 'Previous Year Questions',
      description: 'Solve questions from previous year exams',
      icon: <TbFileText />,
      color: '#34a853',
      bgColor: '#e6f4ea',
      path: isGradeLevel 
        ? `/student/practice/${subject}/grade-${grade}/previous-year-questions`
        : `/student/practice/${subject}/${subtopic}/previous-year-questions`,
    },
    {
      title: 'Smart Practice',
      description: 'Adaptive practice that adjusts to your level',
      icon: <TbBrain />,
      color: '#9c27b0',
      bgColor: '#f3e5f5',
      path: isGradeLevel 
        ? `/student/practice/${subject}/grade-${grade}/smart-practice`
        : `/student/practice/${subject}/${subtopic}/smart-practice`,
    },
  ];

  const formattedSubject = formatBreadcrumb(subject);
  const formattedSubtopic = formatBreadcrumb(subtopic);

  return (
    <div className="practice-mode-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="practice-mode-header">
        <div className="breadcrumbs">
          {isGradeLevel 
            ? `${formattedSubject} > Grade ${grade}`
            : `${formattedSubject} > ${formattedSubtopic}`
          }
        </div>
        <h1 className="practice-mode-title">Choose Practice Mode</h1>
      </header>

      <main className="practice-options-grid">
        {practiceOptions.map((option) => (
          <Link key={option.title} to={option.path} className="practice-option-card-link">
            <div className="practice-option-card">
              <div className="practice-option-content">
                <div 
                  className="practice-option-icon-wrapper" 
                  style={{ backgroundColor: option.bgColor, color: option.color }}
                >
                  {option.icon}
                </div>
                <div className="practice-option-details">
                  <h3>{option.title}</h3>
                  <p>{option.description}</p>
                </div>
              </div>
              <div className="practice-option-arrow">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
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

export default PracticeModePage; 