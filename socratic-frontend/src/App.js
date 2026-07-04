import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import StudentAuthPage from './pages/StudentAuthPage';
import AITutorPage from './pages/AITutorPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// The frontend has been refocused on the AI whiteboard tutor only. All other
// feature pages still live on disk but are intentionally no longer routed.
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/student/auth" element={<StudentAuthPage />} />
            <Route
              path="/student/ai-tutor"
              element={
                <ProtectedRoute userType="student">
                  <AITutorPage />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/student/ai-tutor" replace />} />
            <Route path="*" element={<Navigate to="/student/ai-tutor" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
