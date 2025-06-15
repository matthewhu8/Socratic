//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/pages/HomePage.jsx
import React from 'react';
import { PiStudentFill } from "react-icons/pi";
import { LiaChalkboardTeacherSolid } from "react-icons/lia";
import { FaBook, FaChartLine, FaBrain, FaUsers, FaGraduationCap, FaLightbulb } from "react-icons/fa";
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';

function HomePage() {
  return (
    <div className="home-container">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1>Welcome to Socratic</h1>
          <p className="hero-subtitle">Empowering CBSE & IB Students Through Interactive Learning</p>
          <p className="hero-description">
            Master complex concepts with our AI-powered learning platform designed and trained specifically 
            for CBSE and IB student success.
          </p>
          <div className="cta-buttons">
            <Link to="/student/auth" className="cta-primary">
              Start Learning Today
            </Link>
          </div>
        </div>
      </div>

      {/* About Section */}
      <div className="about-section">
        <div className="section-header">
          <p>
            Socratic is an innovative educational platform that transforms traditional learning 
            through interactive problem-solving and personalized guidance. Built specifically 
            for students following challenging curricula like CBSE and IB programs. Whether you wanna learn alongside your traditional YouTube mentors, or you're looking for a more dynamic learning experience,
            Socratic is here to help.
          </p>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section">
        <h2>Why Choose Socratic?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><FaBrain /></div>
            <h3>AI-Powered Learning</h3>
            <p>Adaptive learning paths that adjust to your pace and understanding level</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><FaBook /></div>
            <h3>Curriculum Aligned</h3>
            <p>Content specifically designed for CBSE and IB syllabi with comprehensive coverage</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><FaChartLine /></div>
            <h3>Progress Tracking</h3>
            <p>Detailed analytics to monitor your learning journey and identify areas for improvement</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><FaLightbulb /></div>
            <h3>Interactive Problem Solving</h3>
            <p>Step-by-step guidance through complex problems with instant feedback</p>
          </div>
        </div>
      </div>

      {/* Curriculum Support Section */}
      <div className="curriculum-section">
        <h2>Perfect for CBSE & IB Students</h2>
        <div className="curriculum-content">
          <div className="curriculum-card">
            <h3>CBSE Excellence</h3>
            <ul>
              <li>Aligned with NCERT curriculum standards</li>
              <li>Board exam preparation with previous year questions</li>
              <li>State board compatibility across all subjects</li>
              <li>Comprehensive practice for competitive exams</li>
            </ul>
          </div>
          <div className="curriculum-card">
            <h3>IB Success</h3>
            <ul>
              <li>HL and SL level content for all subjects</li>
              <li>Internal Assessment (IA) guidance</li>
              <li>Extended Essay support and resources</li>
              <li>CAS activity tracking and reflection tools</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Access Section */}
      <div className="access-section">
        <h2>Get Started</h2>
        <div className="dashboard-options">
          <Link to="/student/auth" className="dashboard-card">
            <div className="card-icon"><PiStudentFill /></div>
            <h3>Student Access</h3>
            <p>Join thousands of students already excelling with personalized learning paths, practice tests, and comprehensive study materials</p>
            <div className="card-cta">Access Student Portal →</div>
          </Link>
        </div>
      </div>
      {/* Footer */}
      <div className="home-footer">
        <div className="footer-content">
          <p>Enhancing education through guided learning and exploration</p>
          <div className="footer-stats">
            <div className="stat">
              <span className="stat-number">100+</span>
              <span className="stat-label">Active Students</span>
            </div>
            <div className="stat">
              <span className="stat-number">95%</span>
              <span className="stat-label">Success Rate</span>
            </div>
            <div className="stat">
              <span className="stat-number">50+</span>
              <span className="stat-label">Subjects Covered</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;