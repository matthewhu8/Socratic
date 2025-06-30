import React, { useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/TopicSelectionPage.css';

function TopicSelectionPage() {
  const { subject, subSubject, optionType } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  
  // State for beta access popup
  const [showBetaPopup, setShowBetaPopup] = useState(false);

  // Function to check if a chapter is in beta (chapters 4-14 or Smart Learning)
  const isChapterInBeta = (chapterName) => {
    // Check if it's Smart Learning
    if (optionType === 'smart-learning') {
      return true;
    }
    
    // Check if it's chapters 4-14
    const chapterMatch = chapterName.match(/Chapter (\d+):/);
    if (chapterMatch) {
      const chapterNumber = parseInt(chapterMatch[1]);
      return chapterNumber >= 4 && chapterNumber <= 14;
    }
    return false;
  };

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

  const handleTopicClick = (topicId, topicName) => {
    // Check if this chapter is in beta
    if (isChapterInBeta(topicName)) {
      setShowBetaPopup(true);
      return;
    }

    const userGrade = currentUser?.grade || '10'; // Fallback to grade 10 if not set
    const practiceMode = optionType; // Use the actual practice mode selected
    
    // Extract the actual topic name from the chapter title
    // "Chapter 1: Real Numbers" -> "Real Numbers"
    // "Chapter 10: Light - Reflection and Refraction" -> "Light - Reflection and Refraction"
    let actualTopicName = topicName;
    if (topicName.includes(': ')) {
      actualTopicName = topicName.split(': ')[1];
    }
    
    // Convert topic name to URL-friendly format
    // "Real Numbers" -> "real-numbers"
    // "Light - Reflection and Refraction" -> "light-reflection-and-refraction"
    const urlFriendlyTopic = actualTopicName
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^\w-]/g, ''); // Remove special characters except hyphens
    
    if (subSubject) {
      // For science subjects: /student/practice/science/physics/ncert-exercises/real-numbers
      navigate(`/student/practice/${subject}/${subSubject}/${practiceMode}/${urlFriendlyTopic}`);
    } else {
      // For other subjects: /student/practice/mathematics/ncert-exercises/real-numbers
      navigate(`/student/practice/${subject}/${practiceMode}/${urlFriendlyTopic}`);
    }
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
        <div className="breadcrumb">
          <button onClick={() => navigate(-1)} className="back-button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
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
          {topics.map((topic) => {
            const isBeta = isChapterInBeta(topic.name);
            return (
              <div 
                key={topic.id} 
                className={`topic-card ${isBeta ? 'topic-card-beta' : ''}`}
                onClick={() => handleTopicClick(topic.id, topic.name)}
              >
                <div className="topic-info">
                  <h3>{topic.name}</h3>
                  <p className="question-count">
                    {typeof topic.questionCount === 'number' 
                      ? `${topic.questionCount} questions` 
                      : topic.questionCount
                    }
                  </p>
                  {isBeta && (
                    <div className="beta-badge">
                      <span>🔒 Beta Access</span>
                    </div>
                  )}
                </div>
                <div className="topic-arrow">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              </div>
            );
          })}
        </div>

        {/* Beta Access Popup */}
        {showBetaPopup && (
          <div className="beta-popup-overlay" onClick={() => setShowBetaPopup(false)}>
            <div className="beta-popup" onClick={(e) => e.stopPropagation()}>
              <div className="beta-popup-header">
                <h2>Beta Private Access</h2>
                <button 
                  className="beta-popup-close" 
                  onClick={() => setShowBetaPopup(false)}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
              
              <div className="beta-popup-content">
                <div className="beta-popup-icon">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z" fill="#4285f4"/>
                  </svg>
                </div>
                
                <h3>Exclusive Early Access</h3>
                <p>
                  This chapter is currently in private beta testing. We're working hard to bring you 
                  the best learning experience with advanced features and comprehensive content.
                </p>
                
                <p className="beta-access-text">
                  Email <strong>learnsocratic@gmail.com</strong> for exclusive beta access
                </p>
                
                <div className="beta-popup-actions">
                  <a 
                    href="mailto:learnsocratic@gmail.com?subject=Beta Access Request&body=Hi! I would like early access to the beta chapters. My email is: "
                    className="beta-email-btn"
                  >
                    📧 Email for Access
                  </a>
                  <button 
                    className="beta-close-btn" 
                    onClick={() => setShowBetaPopup(false)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default TopicSelectionPage; 