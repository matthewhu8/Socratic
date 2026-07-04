import React from 'react';

function ProblemDisplay({ problem }) {
  return (
    <div style={{
      border: '1px solid #ccc',
      padding: '1rem',
      margin: '1rem 0'
    }}>
      <h2>{problem.title}</h2>
      <p>{problem.description}</p>
      <div style={{
        marginTop: '1rem',
        border: '1px dashed #aaa',
        padding: '1rem',
        textAlign: 'center'
      }}>
        {problem.imageUrl 
          ? <img src={problem.imageUrl} alt="Problem Visualization" style={{ maxWidth: '100%' }} />
          : <p>Visualization Area</p>
        }
      </div>
    </div>
  );
}

export default ProblemDisplay;
