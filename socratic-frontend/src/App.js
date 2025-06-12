//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import PhysicsProblemPage from './pages/PhysicProblemPage';
import TeacherDashboardPage from './pages/TeacherDashboardPage';
import CreateTestPage from './pages/CreateTestPage';
import CreatePracticeExamPage from './pages/CreatePracticeExamPage';
import StudentDashboardPage from './pages/StudentDashboardPage';
import StudentHomePage from './pages/StudentHomePage';
import AssessmentPage from './pages/AssessmentPage';
import TestPage from './pages/TestPage';
import TopicProgressPage from './pages/TopicProgressPage';
import StudentAuthPage from './pages/StudentAuthPage';
import TeacherAuthPage from './pages/TeacherAuthPage';
import LearningModulesPage from './pages/LearningModulesPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// Empty placeholder component for Learning Modules
const LearningModulesPlaceholder = () => (
  <div style={{ 
    padding: '2rem', 
    textAlign: 'center', 
    maxWidth: '800px', 
    margin: '0 auto',
    marginTop: '2rem'
  }}>
    <h1>Learning Modules</h1>
    <p>This feature is coming soon.</p>
    <button 
      onClick={() => window.history.back()} 
      style={{ 
        padding: '0.5rem 1rem', 
        marginTop: '1rem',
        background: '#3498db',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      Back to Dashboard
    </button>
  </div>
);

// Placeholder component for Create Learning Module
const CreateLearningModulePlaceholder = () => (
  <div style={{ 
    padding: '2rem', 
    textAlign: 'center', 
    maxWidth: '800px', 
    margin: '0 auto',
    marginTop: '2rem'
  }}>
    <h1>Create Learning Module</h1>
    <p>This feature is coming soon. We're working on building tools to help you create interactive learning experiences for your students.</p>
    <button 
      onClick={() => window.history.back()} 
      style={{ 
        padding: '0.5rem 1rem', 
        marginTop: '1rem',
        background: '#3498db',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      Back to Dashboard
    </button>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/student/auth" element={<StudentAuthPage />} />
            <Route path="/teachers/auth" element={<TeacherAuthPage />} />
            
            {/* Student Protected Routes */}
            <Route path="/student/home" element={
              <ProtectedRoute userType="student">
                <StudentHomePage />
              </ProtectedRoute>
            } />
            <Route path="/student/dashboard" element={
              <ProtectedRoute userType="student">
                <StudentDashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/student/learning-modules" element={
              <ProtectedRoute userType="student">
                <LearningModulesPage />
              </ProtectedRoute>
            } />
            <Route path="/student/assessment" element={
              <ProtectedRoute userType="student">
                <AssessmentPage />
              </ProtectedRoute>
            } />
            <Route path="/test/:testCode" element={
              <ProtectedRoute userType="student">
                <TestPage />
              </ProtectedRoute>
            } />
            <Route path="/assessment/:testCode" element={
              <ProtectedRoute userType="student">
                <AssessmentPage />
              </ProtectedRoute>
            } />
            
            {/* Teacher Protected Routes */}
            <Route path="/teacher/dashboard" element={
              <ProtectedRoute userType="teacher">
                <TeacherDashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/teacher/create-test" element={
              <ProtectedRoute userType="teacher">
                <CreateTestPage />
              </ProtectedRoute>
            } />
            <Route path="/teacher/create-practice-exam" element={
              <ProtectedRoute userType="teacher">
                <CreatePracticeExamPage />
              </ProtectedRoute>
            } />
            <Route path="/teacher/topic-progress/:topicName" element={
              <ProtectedRoute userType="teacher">
                <TopicProgressPage />
              </ProtectedRoute>
            } />
            
            {/* Legacy/Other Routes */}
            <Route path="/physics-problem" element={<PhysicsProblemPage />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;