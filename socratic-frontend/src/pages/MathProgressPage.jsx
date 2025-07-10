import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/MathProgressPage.css';
import API_URL from '../config/api';

function MathProgressPage() {
  const navigate = useNavigate();
  const [mathProgress, setMathProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMathProgress();
  }, []);

  const fetchMathProgress = async () => {
    try {
      const response = await fetch(`${API_URL}/api/student/knowledge-profile`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMathProgress(data.profile);
      }
    } catch (err) {
      console.error('Error fetching math progress:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSkillColor = (score) => {
    if (score >= 70) return '#27ae60'; // Green
    if (score >= 40) return '#f39c12'; // Yellow
    return '#e74c3c'; // Red
  };

  // Define the expected topics in order
  const expectedTopics = [
    "Real Numbers",
    "Polynomials", 
    "Pair of Linear Equations in Two Variables"
  ];

  const getTopicData = (topicName) => {
    if (!mathProgress || !mathProgress.subjects || !mathProgress.subjects.mathematics || !mathProgress.subjects.mathematics.topics) {
      return null;
    }
    
    const topic = mathProgress.subjects.mathematics.topics.find(t => 
      t.topic_name === topicName
    );
    
    return topic || null;
  };

  if (loading) {
    return (
      <div className="math-progress-container">
        <div className="math-progress-header">
          <button onClick={() => navigate('/student/dashboard')} className="back-button">
            ← Back
          </button>
          <h1>Mathematics Progress</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="math-progress-container">
      <div className="math-progress-header">
        <button onClick={() => navigate('/student/dashboard')} className="back-button">
          ← Back
        </button>
        <h1>Mathematics Progress</h1>
      </div>

      <div className="math-progress-content">
        <div className="chapters-grid">
          {expectedTopics.map((topicName) => {
            const topicData = getTopicData(topicName);
            
            return (
              <div key={topicName} className="chapter-card">
                <h3>{topicName}</h3>
                
                {topicData ? (
                  <>
                    <div className="overall-proficiency">
                      <div className="proficiency-info">
                        <span className="proficiency-label">Overall Proficiency</span>
                        <span 
                          className="proficiency-score"
                          style={{ color: getSkillColor(topicData.overall_proficiency) }}
                        >
                          {topicData.overall_proficiency}%
                        </span>
                      </div>
                      <div className="proficiency-progress">
                        <div 
                          className="proficiency-progress-bar"
                          style={{ 
                            width: `${topicData.overall_proficiency}%`,
                            backgroundColor: getSkillColor(topicData.overall_proficiency)
                          }}
                        />
                      </div>
                    </div>
                    
                    <div className="skills-section">
                      <h4>Skills Breakdown</h4>
                      <div className="skills-list">
                        {Object.entries(topicData.skills).map(([skillName, skillData]) => (
                          <div key={skillName} className="skill-item">
                            <div className="skill-info">
                              <span className="skill-name">{skillName}</span>
                              <span 
                                className="skill-score"
                                style={{ color: getSkillColor(skillData.score) }}
                              >
                                {skillData.score}%
                              </span>
                            </div>
                            <div className="skill-progress">
                              <div 
                                className="skill-progress-bar"
                                style={{ 
                                  width: `${skillData.score}%`,
                                  backgroundColor: getSkillColor(skillData.score)
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="no-data">No progress data available for this topic</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default MathProgressPage; 