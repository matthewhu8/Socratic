//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/components/Header.jsx
import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header
      style={{
        backgroundColor: '#1976d2',
        padding: '1rem',
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}
    >
      <h1>Socratic: Practice Exam</h1>
      <nav>
        <Link to="/" style={{ color: '#fff', marginRight: '1rem' }}>Home</Link>
        <Link to="/teachers" style={{ color: '#fff', marginRight: '1rem' }}>Teacher</Link>
        <Link to="/profile" style={{ color: '#fff' }}>Profile</Link>
      </nav>
    </header>
  );
}

export default Header;