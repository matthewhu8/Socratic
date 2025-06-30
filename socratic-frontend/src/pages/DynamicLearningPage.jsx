import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { 
  TbMathFunction, 
  TbFlask, 
  TbBook, 
  TbLanguage,
  TbMicroscope,
  TbAtom,
  TbHeart,
  TbBuildingBank,
  TbMap,
  TbScale,
  TbCoin
} from 'react-icons/tb';
import '../styles/DynamicLearningPage.css';

function DynamicLearningPage() {
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  const [expandedSubject, setExpandedSubject] = useState('mathematics'); // Mathematics open by default
  const [showPremiumMessage, setShowPremiumMessage] = useState(false);

  // Get dynamic class title based on user's grade
  const getClassTitle = () => {
    const userGrade = currentUser?.grade;
    if (userGrade) {
      return `CBSE Class ${userGrade} Learning Platform`;
    }
    return 'CBSE Learning Platform'; // Fallback if no grade is set
  };

  const subjects = [
    {
      id: 'mathematics',
      name: 'Mathematics',
      icon: <TbMathFunction />,
      color: '#4285f4',
      bgColor: '#e8f0fe',
      options: [
        { 
          id: 'ncert-exercises', 
          name: 'NCERT Exercises',
          description: 'Practice problems from NCERT textbook chapters'
        },
        { 
          id: 'ncert-examples', 
          name: 'NCERT Examples',
          description: 'Step-by-step solved examples from NCERT'
        },
        { 
          id: 'pyqs', 
          name: 'Previous Year Questions',
          description: 'Past CBSE board exam questions with solutions'
        },
        { 
          id: 'smart-learning', 
          name: 'Smart Learning',
          description: 'AI-powered adaptive practice tailored to your level'
        }
      ]
    },
    {
      id: 'science',
      name: 'Science',
      icon: <TbFlask />,
      color: '#00897b',
      bgColor: '#e0f2f1',
      subSubjects: [
        { 
          id: 'physics', 
          name: 'Physics', 
          icon: <TbAtom />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Physics problems from NCERT chapters'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Solved physics examples with detailed explanations'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Past physics questions from board exams'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive physics simulations and problems'
            }
          ]
        },
        { 
          id: 'chemistry', 
          name: 'Chemistry', 
          icon: <TbFlask />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Chemistry problems covering all reactions and concepts'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Chemical equations and solved problems'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Previous chemistry board exam questions'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive periodic table and reaction practice'
            }
          ]
        },
        { 
          id: 'biology', 
          name: 'Biology', 
          icon: <TbMicroscope />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Biology questions from life processes to heredity'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Detailed biological diagrams and explanations'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Past biology questions with diagram-based answers'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive 3D models and biology animations'
            }
          ]
        }
      ]
    },
    {
      id: 'social-science',
      name: 'Social Science',
      icon: <TbBuildingBank />,
      color: '#ff6b6b',
      bgColor: '#ffe0e0',
      subSubjects: [
        { 
          id: 'history', 
          name: 'History', 
          icon: <TbBuildingBank />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Questions on Indian and world history'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Historical events with timeline analysis'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Previous history board exam questions'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive timelines and historical maps'
            }
          ]
        },
        { 
          id: 'geography', 
          name: 'Geography', 
          icon: <TbMap />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Map-based and conceptual geography questions'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Geographical phenomena with visual aids'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Past geography questions with map work'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive maps and geographical simulations'
            }
          ]
        },
        { 
          id: 'political-science', 
          name: 'Political Science', 
          icon: <TbScale />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Questions on democracy and political systems'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Case studies of political concepts'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Previous political science exam questions'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive constitution and governance modules'
            }
          ]
        },
        { 
          id: 'economics', 
          name: 'Economics', 
          icon: <TbCoin />,
          options: [
            { 
              id: 'ncert-exercises', 
              name: 'NCERT Exercises',
              description: 'Economic problems and data interpretation'
            },
            { 
              id: 'ncert-examples', 
              name: 'NCERT Examples',
              description: 'Economic concepts with real-world examples'
            },
            { 
              id: 'pyqs', 
              name: 'Previous Year Questions',
              description: 'Past economics board exam questions'
            },
            { 
              id: 'smart-learning', 
              name: 'Smart Learning',
              description: 'Interactive graphs and economic simulations'
            }
          ]
        }
      ]
    },
    {
      id: 'english',
      name: 'English',
      icon: <TbBook />,
      color: '#7c4dff',
      bgColor: '#f3e5ff',
      options: [
        { 
          id: 'ncert-exercises', 
          name: 'NCERT Exercises',
          description: 'Grammar, comprehension and writing exercises'
        },
        { 
          id: 'ncert-examples', 
          name: 'NCERT Examples',
          description: 'Sample essays, letters and literary analysis'
        },
        { 
          id: 'pyqs', 
          name: 'Previous Year Questions',
          description: 'Past English board exam papers with answers'
        },
        { 
          id: 'smart-learning', 
          name: 'Smart Learning',
          description: 'Adaptive grammar and vocabulary building'
        }
      ]
    },
    {
      id: 'hindi',
      name: 'Hindi',
      icon: <TbLanguage />,
      color: '#ffa726',
      bgColor: '#fff3e0',
      options: [
        { 
          id: 'ncert-exercises', 
          name: 'NCERT Exercises',
          description: 'व्याकरण और साहित्य अभ्यास प्रश्न'
        },
        { 
          id: 'ncert-examples', 
          name: 'NCERT Examples',
          description: 'पत्र, निबंध और काव्य विश्लेषण के उदाहरण'
        },
        { 
          id: 'pyqs', 
          name: 'Previous Year Questions',
          description: 'पिछले वर्षों के बोर्ड परीक्षा प्रश्न'
        },
        { 
          id: 'smart-learning', 
          name: 'Smart Learning',
          description: 'इंटरैक्टिव हिंदी व्याकरण और शब्दावली'
        }
      ]
    }
  ];

  const toggleSubject = (subjectId) => {
    setExpandedSubject(expandedSubject === subjectId ? null : subjectId);
  };

  const handleOptionClick = (subject, subSubject, option) => {
    // Check if this is a premium subject or Smart Learning
    if (subject.id !== 'mathematics' || option.id === 'smart-learning') {
      setShowPremiumMessage(true);
      return;
    }
    
    const subjectPath = subSubject ? `${subject.id}/${subSubject.id}` : subject.id;
    navigate(`/student/dynamic-learning/${subjectPath}/${option.id}/topics`);
  };

  const renderSubjectCard = (subject) => {
    const isExpanded = expandedSubject === subject.id;
    const isPremium = subject.id !== 'mathematics';

    return (
      <div key={subject.id} className={`subject-section ${isExpanded ? 'expanded' : ''} ${isPremium ? 'premium' : ''}`}>
        <div 
          className="subject-header"
          style={{ backgroundColor: isPremium ? '#f3f4f6' : subject.bgColor }}
          onClick={() => toggleSubject(subject.id)}
        >
          <div className="subject-icon" style={{ color: isPremium ? '#9ca3af' : subject.color }}>
            {subject.icon}
          </div>
          <h2 style={{ color: isPremium ? '#9ca3af' : subject.color }}>{subject.name}</h2>
          {isPremium && <span className="premium-badge">Beta</span>}
          <div className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M6 9L12 15L18 9" stroke={isPremium ? '#9ca3af' : subject.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>

        {isExpanded && (
          <div className="subject-content">
            {/* For subjects without sub-subjects (Mathematics, English, Hindi) */}
            {!subject.subSubjects && (
              <div className="subject-card">
                <div className="card-header">
                  <div className="card-icon" style={{ backgroundColor: isPremium ? '#9ca3af' : subject.color }}>
                    {subject.icon}
                  </div>
                  <h3>{subject.name}</h3>
                </div>
                <div className="options-list">
                  {subject.options.map(option => {
                    const isOptionBeta = option.id === 'smart-learning' || isPremium;
                    return (
                      <div 
                        key={option.id} 
                        className={`option-item ${isOptionBeta ? 'premium-option' : ''}`}
                        onClick={() => handleOptionClick(subject, null, option)}
                      >
                        <div className="option-content">
                          <h4>{option.name}</h4>
                          <p>{option.description}</p>
                          {option.id === 'smart-learning' && subject.id === 'mathematics' && (
                            <span className="beta-tag">🔒 Beta Access</span>
                          )}
                        </div>
                        <svg className="arrow-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* For subjects with sub-subjects (Science, Social Science) */}
            {subject.subSubjects && subject.subSubjects.map(subSubject => (
              <div key={subSubject.id} className="subject-card">
                <div className="card-header">
                  <div className="card-icon" style={{ backgroundColor: isPremium ? '#9ca3af' : subject.color }}>
                    {subSubject.icon}
                  </div>
                  <h3>{subSubject.name}</h3>
                </div>
                <div className="options-list">
                  {subSubject.options.map(option => {
                    const isOptionBeta = option.id === 'smart-learning' || isPremium;
                    return (
                      <div 
                        key={option.id} 
                        className={`option-item ${isOptionBeta ? 'premium-option' : ''}`}
                        onClick={() => handleOptionClick(subject, subSubject, option)}
                      >
                        <div className="option-content">
                          <h4>{option.name}</h4>
                          <p>{option.description}</p>
                          {option.id === 'smart-learning' && !isPremium && (
                            <span className="beta-tag">🔒 Beta Access</span>
                          )}
                        </div>
                        <svg className="arrow-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="dynamic-learning-container">
      <div className="back-button-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back
        </button>
      </div>
      <div className="hero-section">
        <h1>{getClassTitle()}</h1>
        <p>The comprehensive platform designed to excel in your CBSE board exams</p>
        <div className="stats-container">
          <div className="stat-item">
            <h2>95%</h2>
            <p>Students improved their scores</p>
          </div>
          <div className="stat-item">
            <h2>10,000+</h2>
            <p>Practice questions available</p>
          </div>
        </div>
      </div>

      <div className="subjects-container">
        <div className="subjects-header">
          <h2>Select Your Subject</h2>
          <p>Choose a subject to begin your learning journey</p>
        </div>

        <div className="subjects-list">
          {subjects.map(subject => renderSubjectCard(subject))}
        </div>
      </div>

      {/* Premium Message Modal */}
      {showPremiumMessage && (
        <div className="premium-modal-overlay" onClick={() => setShowPremiumMessage(false)}>
          <div className="premium-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Beta Testing Feature</h3>
            <p>This feature is currently in beta testing.</p>
            <p>Email <a href="mailto:learnsocratic@gmail.com">learnsocratic@gmail.com</a> to gain beta access.</p>
            <button className="premium-modal-close" onClick={() => setShowPremiumMessage(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DynamicLearningPage; 