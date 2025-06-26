import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/TopicSelectionPage.css';

function TopicSelectionPage() {
  const { subject, subSubject, optionType } = useParams();
  const navigate = useNavigate();

  // Topic data for different subjects
  const topicsData = {
    mathematics: {
      'ncert-exercises': [
        { id: 'ch1', name: 'Chapter 1: Real Numbers', questionCount: 45 },
        { id: 'ch2', name: 'Chapter 2: Polynomials', questionCount: 38 },
        { id: 'ch3', name: 'Chapter 3: Pair of Linear Equations in Two Variables', questionCount: 52 },
        { id: 'ch4', name: 'Chapter 4: Quadratic Equations', questionCount: 41 },
        { id: 'ch5', name: 'Chapter 5: Arithmetic Progressions', questionCount: 36 },
        { id: 'ch6', name: 'Chapter 6: Triangles', questionCount: 48 },
        { id: 'ch7', name: 'Chapter 7: Coordinate Geometry', questionCount: 33 },
        { id: 'ch8', name: 'Chapter 8: Introduction to Trigonometry', questionCount: 40 },
        { id: 'ch9', name: 'Chapter 9: Some Applications of Trigonometry', questionCount: 28 },
        { id: 'ch10', name: 'Chapter 10: Circles', questionCount: 35 },
        { id: 'ch11', name: 'Chapter 11: Areas Related to Circles', questionCount: 30 },
        { id: 'ch12', name: 'Chapter 12: Surface Areas and Volumes', questionCount: 42 },
        { id: 'ch13', name: 'Chapter 13: Statistics', questionCount: 37 },
        { id: 'ch14', name: 'Chapter 14: Probability', questionCount: 25 }
      ],
      'ncert-examples': [
        { id: 'ch1', name: 'Chapter 1: Real Numbers', questionCount: 18 },
        { id: 'ch2', name: 'Chapter 2: Polynomials', questionCount: 15 },
        { id: 'ch3', name: 'Chapter 3: Pair of Linear Equations', questionCount: 22 },
        { id: 'ch4', name: 'Chapter 4: Quadratic Equations', questionCount: 16 },
        { id: 'ch5', name: 'Chapter 5: Arithmetic Progressions', questionCount: 14 },
        { id: 'ch6', name: 'Chapter 6: Triangles', questionCount: 20 },
        { id: 'ch7', name: 'Chapter 7: Coordinate Geometry', questionCount: 12 },
        { id: 'ch8', name: 'Chapter 8: Introduction to Trigonometry', questionCount: 18 },
        { id: 'ch9', name: 'Chapter 9: Applications of Trigonometry', questionCount: 10 },
        { id: 'ch10', name: 'Chapter 10: Circles', questionCount: 14 },
        { id: 'ch11', name: 'Chapter 11: Areas Related to Circles', questionCount: 12 },
        { id: 'ch12', name: 'Chapter 12: Surface Areas and Volumes', questionCount: 16 },
        { id: 'ch13', name: 'Chapter 13: Statistics', questionCount: 15 },
        { id: 'ch14', name: 'Chapter 14: Probability', questionCount: 10 }
      ],
      'pyqs': [
        { id: '2023', name: '2023 Board Exam Questions', questionCount: 35 },
        { id: '2022', name: '2022 Board Exam Questions', questionCount: 35 },
        { id: '2021', name: '2021 Board Exam Questions', questionCount: 30 },
        { id: '2020', name: '2020 Board Exam Questions', questionCount: 35 },
        { id: '2019', name: '2019 Board Exam Questions', questionCount: 35 }
      ],
      'smart-learning': [
        { id: 'diagnostic', name: 'Diagnostic Test', questionCount: 20 },
        { id: 'weak-areas', name: 'Weak Areas Practice', questionCount: 'Adaptive' },
        { id: 'mixed-practice', name: 'Mixed Topic Practice', questionCount: 'Unlimited' },
        { id: 'exam-simulation', name: 'Board Exam Simulation', questionCount: 35 }
      ]
    },
    science: {
      physics: {
        'ncert-exercises': [
          { id: 'ch10', name: 'Chapter 10: Light - Reflection and Refraction', questionCount: 42 },
          { id: 'ch11', name: 'Chapter 11: Human Eye and Colourful World', questionCount: 35 },
          { id: 'ch12', name: 'Chapter 12: Electricity', questionCount: 48 },
          { id: 'ch13', name: 'Chapter 13: Magnetic Effects of Electric Current', questionCount: 38 },
          { id: 'ch14', name: 'Chapter 14: Sources of Energy', questionCount: 25 }
        ],
        'ncert-examples': [
          { id: 'ch10', name: 'Chapter 10: Light - Reflection and Refraction', questionCount: 15 },
          { id: 'ch11', name: 'Chapter 11: Human Eye and Colourful World', questionCount: 12 },
          { id: 'ch12', name: 'Chapter 12: Electricity', questionCount: 18 },
          { id: 'ch13', name: 'Chapter 13: Magnetic Effects', questionCount: 14 },
          { id: 'ch14', name: 'Chapter 14: Sources of Energy', questionCount: 10 }
        ]
      },
      chemistry: {
        'ncert-exercises': [
          { id: 'ch1', name: 'Chapter 1: Chemical Reactions and Equations', questionCount: 38 },
          { id: 'ch2', name: 'Chapter 2: Acids, Bases and Salts', questionCount: 42 },
          { id: 'ch3', name: 'Chapter 3: Metals and Non-metals', questionCount: 45 },
          { id: 'ch4', name: 'Chapter 4: Carbon and its Compounds', questionCount: 40 },
          { id: 'ch5', name: 'Chapter 5: Periodic Classification of Elements', questionCount: 28 }
        ]
      },
      biology: {
        'ncert-exercises': [
          { id: 'ch6', name: 'Chapter 6: Life Processes', questionCount: 48 },
          { id: 'ch7', name: 'Chapter 7: Control and Coordination', questionCount: 35 },
          { id: 'ch8', name: 'Chapter 8: How do Organisms Reproduce?', questionCount: 38 },
          { id: 'ch9', name: 'Chapter 9: Heredity and Evolution', questionCount: 32 },
          { id: 'ch15', name: 'Chapter 15: Our Environment', questionCount: 25 },
          { id: 'ch16', name: 'Chapter 16: Natural Resources', questionCount: 22 }
        ]
      }
    }
  };

  // Get topics based on current route
  const getTopics = () => {
    if (subSubject) {
      // For science subjects
      return topicsData.science[subSubject]?.[optionType] || [];
    } else {
      // For other subjects
      return topicsData[subject]?.[optionType] || [];
    }
  };

  const topics = getTopics();

  const handleTopicClick = (topicId) => {
    const basePath = subSubject ? `${subject}/${subSubject}` : subject;
    navigate(`/student/practice/${basePath}/grade-10/previous-year-questions`);
  };

  const formatSubjectName = (name) => {
    return name.split('-').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getOptionTypeTitle = () => {
    const titles = {
      'ncert-exercises': 'NCERT Exercises',
      'ncert-examples': 'NCERT Examples',
      'pyqs': 'Previous Year Questions',
      'smart-learning': 'Smart Learning'
    };
    return titles[optionType] || formatSubjectName(optionType);
  };

  return (
    <div className="topic-selection-container">
      <header className="topic-header">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <div className="breadcrumb">
          <span>{formatSubjectName(subject)}</span>
          {subSubject && (
            <>
              <span className="separator">›</span>
              <span>{formatSubjectName(subSubject)}</span>
            </>
          )}
          <span className="separator">›</span>
          <span>{getOptionTypeTitle()}</span>
        </div>
      </header>

      <main className="topic-main">
        <h1>Select a Topic</h1>
        <p className="topic-subtitle">Choose a chapter or topic to start practicing</p>

        <div className="topics-grid">
          {topics.map((topic) => (
            <div 
              key={topic.id} 
              className="topic-card"
              onClick={() => handleTopicClick(topic.id)}
            >
              <div className="topic-info">
                <h3>{topic.name}</h3>
                <p className="question-count">
                  {typeof topic.questionCount === 'number' 
                    ? `${topic.questionCount} questions` 
                    : topic.questionCount
                  }
                </p>
              </div>
              <div className="topic-arrow">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default TopicSelectionPage; 