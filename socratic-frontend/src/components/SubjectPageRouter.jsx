import React from 'react';
import { useParams } from 'react-router-dom';
import MathematicsPage from '../pages/MathematicsPage';
import PhysicsPage from '../pages/PhysicsPage';
import ChemistryPage from '../pages/ChemistryPage';
import BiologyPage from '../pages/BiologyPage';
import EnglishPage from '../pages/EnglishPage';

function SubjectPageRouter() {
  const { subject, gradeParam } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';

  switch (subject) {
    case 'mathematics':
      return <MathematicsPage />;
    case 'physics':
      return <PhysicsPage />;
    case 'chemistry':
      return <ChemistryPage />;
    case 'biology':
      return <BiologyPage />;
    case 'english':
      return <EnglishPage />;
    default:
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Subject not found</h1>
          <p>The subject "{subject}" is not available.</p>
          <button onClick={() => window.history.back()}>Back</button>
        </div>
      );
  }
}

export default SubjectPageRouter; 