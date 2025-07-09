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
import MathProgressPage from './pages/MathProgressPage';
import AssessmentPage from './pages/AssessmentPage';
import TestPage from './pages/TestPage';
import TopicProgressPage from './pages/TopicProgressPage';
import StudentAuthPage from './pages/StudentAuthPage';
import TeacherAuthPage from './pages/TeacherAuthPage';
import LearningModulesPage from './pages/LearningModulesPage';
import DynamicLearningPage from './pages/DynamicLearningPage';
import GradeSelectionPage from './pages/GradeSelectionPage';
import PracticeModePage from './pages/PracticeModePage';
import PreviousYearQuestionsPage from './pages/PreviousYearQuestionsPage';
import TopicSelectionPage from './pages/TopicSelectionPage';
import SubtopicSelectionPage from './pages/SubtopicSelectionPage';
import MobileGradingPage from './pages/MobileGradingPage';
import AITutorPage from './pages/AITutorPage';
import ProtectedRoute from './components/ProtectedRoute';
import SubjectPageRouter from './components/SubjectPageRouter';
import { AuthProvider } from './contexts/AuthContext';

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
            <Route path="/mobile-grade/:sessionId" element={<MobileGradingPage />} />
            
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
            <Route path="/student/math-progress" element={
              <ProtectedRoute userType="student">
                <MathProgressPage />
              </ProtectedRoute>
            } />
            <Route path="/student/learning-modules" element={
              <ProtectedRoute userType="student">
                <LearningModulesPage />
              </ProtectedRoute>
            } />
            <Route path="/student/dynamic-learning" element={
              <ProtectedRoute userType="student">
                <DynamicLearningPage />
              </ProtectedRoute>
            } />
            <Route path="/student/ai-tutor" element={
              <ProtectedRoute userType="student">
                <AITutorPage />
              </ProtectedRoute>
            } />
            
            {/* New CBSE Dynamic Learning Routes */}
            <Route path="/student/dynamic-learning/:subject/:optionType/topics" element={
              <ProtectedRoute userType="student">
                <TopicSelectionPage />
              </ProtectedRoute>
            } />
            <Route path="/student/dynamic-learning/:subject/:subSubject/:optionType/topics" element={
              <ProtectedRoute userType="student">
                <TopicSelectionPage />
              </ProtectedRoute>
            } />
            
            {/* New Practice Routes with Practice Mode and Topic */}
            <Route path="/student/practice/:subject/:practiceMode/:topic" element={
              <ProtectedRoute userType="student">
                <PreviousYearQuestionsPage />
              </ProtectedRoute>
            } />
            <Route path="/student/practice/:subject/:subSubject/:practiceMode/:topic" element={
              <ProtectedRoute userType="student">
                <PreviousYearQuestionsPage />
              </ProtectedRoute>
            } />
            
            {/* Existing Routes */}
            <Route path="/student/dynamic-learning/:subject/select-grade" element={<ProtectedRoute userType="student"><GradeSelectionPage /></ProtectedRoute>} />
            <Route path="/student/practice/:subject/:gradeParam" element={<ProtectedRoute userType="student"><PracticeModePage /></ProtectedRoute>} />
            <Route path="/student/practice/:subject/:gradeParam/previous-year-questions" element={<ProtectedRoute userType="student"><PreviousYearQuestionsPage /></ProtectedRoute>} />
            <Route path="/student/practice/:subject/:subSubject/:gradeParam/previous-year-questions" element={<ProtectedRoute userType="student"><PreviousYearQuestionsPage /></ProtectedRoute>} />
            <Route path="/student/dynamic-learning/:subject/:gradeParam/ncert-topics" element={<ProtectedRoute userType="student"><SubjectPageRouter /></ProtectedRoute>} />
            <Route path="/student/dynamic-learning/:subject/:gradeParam" element={<ProtectedRoute userType="student"><SubjectPageRouter /></ProtectedRoute>} />
            <Route path="/student/dynamic-learning/:subject/:gradeParam/:subtopic" element={<ProtectedRoute userType="student"><PracticeModePage /></ProtectedRoute>} />
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