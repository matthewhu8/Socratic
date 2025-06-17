import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/AuthPage.css';
import { AuthContext } from '../contexts/AuthContext';
import API_URL from '../config/api';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

function StudentAuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    grade: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { setCurrentUser } = useContext(AuthContext);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/auth/google/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Google Sign-In failed');
      }

      const loginData = await res.json();
      await finalizeLogin(loginData, 'student');
      
    } catch (error) {
      console.error("Google login error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    console.error("Google login failed");
    setError("Google Sign-In failed. Please try again.");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      if (isSignUp) {
        // Registration process
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          setIsLoading(false);
          return;
        }
        
        console.log("Attempting to register with:", formData.email);
        const registerResponse = await fetch(`${API_URL}/api/auth/student/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: formData.name,
            email: formData.email,
            password: formData.password,
            grade: formData.grade
          }),
        });
        
        console.log("Registration response status:", registerResponse.status);
        if (!registerResponse.ok) {
          const errorData = await registerResponse.json();
          console.error("Registration error:", errorData);
          throw new Error(errorData.detail || 'Registration failed');
        }
        
        // After successful registration, automatically log in
        await loginUser(formData.email, formData.password);
      } else {
        // Login process
        await loginUser(formData.email, formData.password);
      }
    } catch (error) {
      console.error("Authentication error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const loginUser = async (email, password) => {
    try {
      const loginResponse = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!loginResponse.ok) {
        const errorData = await loginResponse.json();
        throw new Error(errorData.detail || 'Login failed');
      }
      
      const loginData = await loginResponse.json();
      await finalizeLogin(loginData, 'student');
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  };

  const finalizeLogin = async (loginData, userType) => {
    // Store tokens
    localStorage.setItem('accessToken', loginData.access_token);
    localStorage.setItem('refreshToken', loginData.refresh_token);
    localStorage.setItem('userType', userType);

    // Fetch user profile to get real database ID
    const profileResponse = await fetch(`${API_URL}/api/auth/${userType}/me`, {
      headers: {
        'Authorization': `Bearer ${loginData.access_token}`
      }
    });

    if (profileResponse.ok) {
      const userData = await profileResponse.json();
      setCurrentUser({
        id: userData.id,              // Real database ID
        name: userData.name,
        email: userData.email,
        grade: userData.grade,
        userType: userType,
        isAuthenticated: true
      });

      navigate('/student/home');
    } else {
      throw new Error('Failed to fetch user profile');
    }
  };

  const toggleForm = () => {
    setIsSignUp(!isSignUp);
    setError('');
  };

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <Link to="/" className="back-link">← Back to Home</Link>
            <h1>{isSignUp ? 'Student Sign Up' : 'Student Sign In'}</h1>
            <p>{isSignUp ? 'Create your student account' : 'Access your student dashboard'}</p>
          </div>

          {error && <div className="error-message">{error}</div>}
          
          <div className="social-login-container">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              text="signin_with"
              shape="rectangular"
              width="100%"
            />
          </div>

          <div className="divider">
            <span>OR</span>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isSignUp && (
              <>
                <div className="form-group">
                  <label htmlFor="name">Full Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter your full name"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="grade">Grade Level</label>
                  <select
                    id="grade"
                    name="grade"
                    value={formData.grade}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select your grade</option>
                    <option value="9">Grade 9</option>
                    <option value="10">Grade 10</option>
                    <option value="11">Grade 11</option>
                    <option value="12">Grade 12</option>
                  </select>
                </div>
              </>
            )}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                required
              />
            </div>

            {isSignUp && (
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="Confirm your password"
                  required
                />
              </div>
            )}

            <button 
              type="submit" 
              className="auth-button"
              disabled={isLoading}
            >
              {isLoading ? 'Processing...' : (isSignUp ? 'Create Account' : 'Sign In')}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              {isSignUp
                ? 'Already have an account?'
                : "Don't have an account yet?"}
              <button className="toggle-form-btn" onClick={toggleForm}>
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}

export default StudentAuthPage; 