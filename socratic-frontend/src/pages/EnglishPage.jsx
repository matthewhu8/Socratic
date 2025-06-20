import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { TbBook } from 'react-icons/tb';
import '../styles/SubjectPage.css';

const englishTopicsByGrade = {
  9: [
    {
      title: 'Grammar Fundamentals',
      description: 'Parts of speech, sentence structure, and punctuation.',
      path: '/student/dynamic-learning/english/grade-9/grammar-fundamentals',
    },
    {
      title: 'Reading Comprehension',
      description: 'Understanding and analyzing texts.',
      path: '/student/dynamic-learning/english/grade-9/reading-comprehension',
    },
    {
      title: 'Creative Writing',
      description: 'Introduction to narrative and descriptive writing.',
      path: '/student/dynamic-learning/english/grade-9/creative-writing',
    },
  ],
  10: [
    {
      title: 'Poetry Analysis',
      description: 'Understanding poetic devices and themes.',
      path: '/student/dynamic-learning/english/grade-10/poetry-analysis',
    },
    {
      title: 'Essay Writing',
      description: 'Persuasive and argumentative essays.',
      path: '/student/dynamic-learning/english/grade-10/essay-writing',
    },
    {
      title: 'Literature Study',
      description: 'Analyzing novels and short stories.',
      path: '/student/dynamic-learning/english/grade-10/literature-study',
    },
  ],
  11: [
    {
      title: 'Advanced Grammar',
      description: 'Complex sentence structures and advanced punctuation.',
      path: '/student/dynamic-learning/english/grade-11/advanced-grammar',
    },
    {
      title: 'Research Skills',
      description: 'Finding and citing reliable sources.',
      path: '/student/dynamic-learning/english/grade-11/research-skills',
    },
    {
      title: 'Shakespeare Studies',
      description: 'Understanding Shakespearean language and themes.',
      path: '/student/dynamic-learning/english/grade-11/shakespeare-studies',
    },
  ],
  12: [
    {
      title: 'Literary Analysis',
      description: 'Advanced techniques for analyzing literature.',
      path: '/student/dynamic-learning/english/grade-12/literary-analysis',
    },
    {
      title: 'Academic Writing',
      description: 'Research papers and formal writing styles.',
      path: '/student/dynamic-learning/english/grade-12/academic-writing',
    },
    {
      title: 'Public Speaking',
      description: 'Presentation skills and oral communication.',
      path: '/student/dynamic-learning/english/grade-12/public-speaking',
    },
  ],
};

function EnglishPage() {
  const navigate = useNavigate();
  const { gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  const topics = englishTopicsByGrade[gradeNumber] || [];

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} English content coming soon!</h1>
      </div>
    );
  }

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: '#f3e5f5', color: '#673ab7' }}>
          <TbBook />
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: '#673ab7' }}>English - Grade {grade}</h1>
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

export default EnglishPage; 