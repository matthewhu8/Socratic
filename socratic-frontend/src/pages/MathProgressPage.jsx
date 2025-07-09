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

  const chapters = [
    { id: 1, name: 'Chapter 1' },
    { id: 2, name: 'Chapter 2' },
    { id: 3, name: 'Chapter 3' }
  ];

  const getChapterData = (chapterNum) => {
    if (!mathProgress || !mathProgress.subjects.mathematics.topics) return null;
    
    const topic = mathProgress.subjects.mathematics.topics.find(t => 
      t.topic_name.toLowerCase().includes(`chapter ${chapterNum}`) || 
      t.topic_name.toLowerCase().includes(`${chapterNum}`)
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
          {chapters.map((chapter) => {
            const chapterData = getChapterData(chapter.id);
            
            return (
              <div key={chapter.id} className="chapter-card">
                <h3>{chapter.name}</h3>
                
                {chapterData ? (
                  <div className="skills-list">
                    {Object.entries(chapterData.skills).map(([skillName, skillData]) => (
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
                ) : (
                  <div className="no-data">No progress data available</div>
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