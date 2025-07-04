import React, { useState, useEffect, useRef, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/AITutorPage.css';
import API_URL, { fetchWithAuth } from '../config/api';

function AITutorPage() {
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [userInput, setUserInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const canvasRef = useRef(null);
  const recognition = useRef(null);
  const [isListening, setIsListening] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [context, setContext] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentDrawingY, setCurrentDrawingY] = useState(50); // Track Y position for AI drawings

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      recognition.current.lang = 'en-US';

      recognition.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setUserInput(transcript);
        handleSubmit(transcript);
      };

      recognition.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Initialize canvas
  useEffect(() => {
    const initCanvas = (preserveContent = false) => {
      if (canvasRef.current && canvasRef.current.parentElement) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        // Get the container width
        const container = canvasRef.current.parentElement;
        const containerWidth = container.clientWidth;
        
        // Set canvas size based on container width
        const canvasWidth = containerWidth - 20; // Subtract padding
        const canvasHeight = 2000; // Large height for scrolling
        
        // Save current canvas content if needed
        let imageData = null;
        if (preserveContent && canvas.width > 0 && canvas.height > 0) {
          try {
            imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          } catch (e) {
            console.log('Could not preserve canvas content:', e);
          }
        }
        
        // Only resize if dimensions actually changed
        if (canvas.width !== canvasWidth || canvas.height !== canvasHeight) {
          // Set canvas size
          canvas.width = canvasWidth;
          canvas.height = canvasHeight;
          
          // Set canvas CSS size
          canvas.style.width = canvasWidth + 'px';
          canvas.style.height = canvasHeight + 'px';
          
          // Set white background
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvasWidth, canvasHeight);
          
          // Restore content if we have it
          if (imageData) {
            try {
              ctx.putImageData(imageData, 0, 0);
            } catch (e) {
              console.log('Could not restore canvas content:', e);
            }
          }
          
          console.log('Canvas resized:', canvasWidth, 'x', canvasHeight);
        }
        
        // Set default styles
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        
        setContext(ctx);
      }
    };
    
    // Initialize canvas after a short delay to ensure proper sizing
    setTimeout(() => initCanvas(false), 100);
    
    // Reinitialize on window resize
    const handleResize = () => {
      setTimeout(() => initCanvas(true), 100);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Initialize session
  useEffect(() => {
    initializeSession();
    
    // Stop any ongoing speech on page load
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    
    // Cleanup function to stop speech when component unmounts
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);
  
  // Add event listener for page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const initializeSession = async () => {
    try {
      setIsConnecting(true);
      
      // Create a new session
      const response = await fetchWithAuth(`${API_URL}/api/ai-tutor/create-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: currentUser.id,
          userName: currentUser.name,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const data = await response.json();
      setSessionId(data.sessionId);
      setIsConnecting(false);
    } catch (err) {
      console.error('Failed to initialize session:', err);
      setError('Failed to connect. Please try again.');
      setIsConnecting(false);
    }
  };

  // Canvas drawing functions
  const startDrawing = (e) => {
    if (!context) return;
    setIsDrawing(true);
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    context.beginPath();
    context.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing || !context) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    context.lineTo(x, y);
    context.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    if (!context || !canvasRef.current) return;
    const canvas = canvasRef.current;
    context.clearRect(0, 0, canvas.width, canvas.height);
    // Restore white background
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    // Reset stroke style
    context.strokeStyle = '#000000';
    // Reset drawing position
    setCurrentDrawingY(50);
  };

  const captureCanvas = () => {
    if (canvasRef.current) {
      const dataURL = canvasRef.current.toDataURL('image/png');
      console.log('Canvas captured, size:', dataURL.length);
      console.log('Canvas dimensions:', canvasRef.current.width, 'x', canvasRef.current.height);
      return dataURL;
    }
    console.log('Canvas ref not available');
    return null;
  };

  const handleSubmit = async (text = userInput, includeCanvas = false) => {
    if (!text.trim() || isProcessing) return;

    // Auto-include canvas if student asks about their work
    const shouldIncludeCanvas = includeCanvas || 
      text.toLowerCase().includes('my work') ||
      text.toLowerCase().includes('what i drew') ||
      text.toLowerCase().includes('what i wrote') ||
      text.toLowerCase().includes('whiteboard') ||
      text.toLowerCase().includes('drawing') ||
      text.toLowerCase().includes('solution') ||
      text.toLowerCase().includes('check my') ||
      text.toLowerCase().includes('analyze') ||
      text.toLowerCase().includes('correct') ||
      text.toLowerCase().includes('wrong') ||
      text.toLowerCase().includes('this right') ||
      text.toLowerCase().includes('help me') ||
      text.toLowerCase().includes('stuck') ||
      text.toLowerCase().includes('how do i');

    const canvasData = shouldIncludeCanvas ? captureCanvas() : null;
    
    if (shouldIncludeCanvas) {
      console.log('Including canvas in request');
      console.log('Canvas data exists:', canvasData !== null);
      console.log('Canvas data length:', canvasData ? canvasData.length : 0);
    }

    setIsProcessing(true);
    const newMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, newMessage]);
    setUserInput('');

    try {
      const response = await fetchWithAuth(`${API_URL}/api/ai-tutor/process-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId,
          query: text,
          messages: messages.slice(-10), // Send last 10 messages for context
          canvasImage: canvasData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process query');
      }

      const data = await response.json();
      console.log('Full response from backend:', JSON.stringify(data, null, 2));
      
      // Check if the response contains the expected structure
      let aiResponse = data.response;
      let drawingCommands = data.drawingCommands || data.drawing_commands;
      
      // If the response is a string that looks like JSON, try to parse it
      if (typeof data.response === 'string' && data.response.includes('"response"')) {
        try {
          const parsedResponse = JSON.parse(data.response);
          aiResponse = parsedResponse.response;
          drawingCommands = parsedResponse.drawing_commands || parsedResponse.drawingCommands;
          console.log('Parsed nested JSON response:', parsedResponse);
        } catch (e) {
          console.error('Failed to parse nested JSON:', e);
        }
      }
      
      console.log('Final aiResponse:', aiResponse);
      console.log('Final drawingCommands:', drawingCommands);
      
      // Add AI response to messages
      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);

      // Execute drawing commands if any
      console.log('Context available:', !!context, 'Canvas ref:', !!canvasRef.current);
      if (drawingCommands && drawingCommands.length > 0 && context) {
        console.log('Executing drawing commands:', drawingCommands);
        executeDrawingCommands(drawingCommands);
      } else {
        console.log('No drawing commands to execute. drawingCommands:', drawingCommands, 'context:', context);
        if (!context && canvasRef.current) {
          console.log('Context missing, trying to get it from canvas');
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            setContext(ctx);
            console.log('Context set, retrying drawing commands');
            if (drawingCommands && drawingCommands.length > 0) {
              executeDrawingCommands(drawingCommands);
            }
          }
        }
      }

      // Speak the response
      if (aiResponse) {
        speakText(aiResponse);
      }

    } catch (err) {
      console.error('Failed to process query:', err);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const executeDrawingCommands = async (commands) => {
    if (!context || !commands || commands.length === 0) {
      console.log('Cannot execute drawing commands:', { hasContext: !!context, commands });
      return;
    }

    console.log('Starting to execute drawing commands. Current Y position:', currentDrawingY);

    // Test drawing to ensure canvas works
    context.save();
    context.fillStyle = '#ff0000';
    context.fillRect(10, 10, 50, 50); // Red square at top left
    context.restore();
    console.log('Test drawing complete - you should see a red square');

    // Clear a specific area for the new drawing instead of the whole canvas
    const drawingAreaHeight = 400; // Height for each AI drawing
    
    // Create a white rectangle for the new drawing area
    context.save();
    context.fillStyle = '#ffffff';
    context.fillRect(0, currentDrawingY, canvasRef.current.width, drawingAreaHeight);
    context.restore();
    
    // Find the bounding box of the drawing commands to offset if needed
    let maxY = currentDrawingY;
    
    for (const command of commands) {
      try {
        console.log('Executing command:', command);
        
        // Apply Y offset to avoid overlapping
        const yOffset = currentDrawingY;
        
        switch (command.type) {
          case 'text':
            context.save();
            // Handle font size from options
            const fontSize = command.options?.fontSize || 20;
            context.font = command.font || `${fontSize}px Arial`;
            context.fillStyle = command.options?.color || command.color || '#000000';
            const adjustedY = command.position.y + yOffset;
            context.fillText(command.text, command.position.x, adjustedY);
            maxY = Math.max(maxY, adjustedY + 30); // Add some padding
            context.restore();
            break;
            
          case 'shape':
            context.save();
            // Handle both 'color' and 'stroke' property names
            context.strokeStyle = command.options?.color || command.options?.stroke || '#000000';
            // Handle both 'width' and 'strokeWidth' property names
            context.lineWidth = command.options?.width || command.options?.strokeWidth || 2;
            
            if (command.shape === 'rectangle') {
              const rectY = command.options.y + yOffset;
              context.strokeRect(
                command.options.x, 
                rectY, 
                command.options.width, 
                command.options.height
              );
              maxY = Math.max(maxY, rectY + command.options.height + 20);
            } else if (command.shape === 'circle') {
              context.beginPath();
              const circleY = command.options.y + yOffset;
              context.arc(
                command.options.x, 
                circleY, 
                command.options.radius || 50, 
                0, 
                2 * Math.PI
              );
              
              // Handle fill option for circles
              if (command.options.fill) {
                context.fillStyle = command.options.color || '#000000';
                context.fill();
              }
              context.stroke();
              maxY = Math.max(maxY, circleY + (command.options.radius || 50) + 20);
            } else if (command.shape === 'line') {
              context.beginPath();
              
              // Handle dashed lines
              if (command.options.strokeDasharray) {
                const dashArray = command.options.strokeDasharray.split(',').map(num => parseInt(num));
                context.setLineDash(dashArray);
              }
              
              context.moveTo(command.options.x1 || command.options.x, (command.options.y1 || command.options.y) + yOffset);
              context.lineTo(command.options.x2, command.options.y2 + yOffset);
              context.stroke();
              
              // Reset line dash
              context.setLineDash([]);
              
              maxY = Math.max(maxY, Math.max(command.options.y1 || command.options.y, command.options.y2) + yOffset + 20);
            }
            context.restore();
            break;
            
          case 'path':
            if (command.points && command.points.length > 0) {
              context.save();
              // Handle both property name formats
              context.strokeStyle = command.options?.color || command.options?.stroke || '#000000';
              context.lineWidth = command.options?.width || command.options?.strokeWidth || 2;
              if (command.options?.lineCap) {
                context.lineCap = command.options.lineCap;
              }
              
              // Handle dashed lines
              if (command.options?.lineDash) {
                context.setLineDash(command.options.lineDash);
              }
              
              context.beginPath();
              context.moveTo(command.points[0].x, command.points[0].y + yOffset);
              for (let i = 1; i < command.points.length; i++) {
                context.lineTo(command.points[i].x, command.points[i].y + yOffset);
                maxY = Math.max(maxY, command.points[i].y + yOffset + 20);
              }
              context.stroke();
              context.restore();
            }
            break;
            
          case 'clear':
            // Clear the entire canvas and reset the drawing position
            clearCanvas();
            setCurrentDrawingY(50);
            maxY = 50; // Reset maxY as well
            console.log('Canvas cleared and reset');
            break;
            
          default:
            console.warn('Unknown drawing command:', command.type);
        }
      } catch (err) {
        console.error('Failed to execute drawing command:', err, command);
      }
    }
    
    // Update the current Y position for next drawing with more spacing
    setCurrentDrawingY(maxY + 100); // Add more spacing between drawings
    
    // Add a separator line between drawings
    context.save();
    context.strokeStyle = '#e5e7eb';
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(50, maxY + 50);
    context.lineTo(canvasRef.current.width - 50, maxY + 50);
    context.stroke();
    context.restore();
    
    // Scroll to the new content
    const scrollContainer = document.querySelector('.whiteboard-scroll-container');
    if (scrollContainer) {
      scrollContainer.scrollTop = currentDrawingY - 200; // Scroll to show the new content
    }
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      
      utterance.onstart = () => {
        setIsSpeaking(true);
      };
      
      utterance.onend = () => {
        setIsSpeaking(false);
      };
      
      utterance.onerror = () => {
        setIsSpeaking(false);
      };
      
      window.speechSynthesis.speak(utterance);
    }
  };
  
  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleListening = () => {
    if (!recognition.current) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }

    if (isListening) {
      recognition.current.stop();
    } else {
      recognition.current.start();
      setIsListening(true);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="ai-tutor-container">
      <div className="ai-tutor-header">
        <button className="back-button" onClick={() => navigate('/student/home')}>
          ← Back
        </button>
        <h1>AI Tutor</h1>
        <div className="session-info">
          {sessionId && <span>Session: {sessionId.slice(0, 8)}...</span>}
        </div>
      </div>

      <div className="ai-tutor-content">
        <div className="whiteboard-section">
          {isConnecting && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Connecting to whiteboard...</p>
            </div>
          )}
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={initializeSession}>Retry</button>
            </div>
          )}
          <div className="whiteboard-controls">
            <button onClick={clearCanvas} className="control-button">
              Clear Board
            </button>
            <button 
              onClick={() => handleSubmit("Please analyze my work on the whiteboard and provide feedback", true)}
              className="control-button analyze-button"
              disabled={isProcessing}
            >
              🔍 Analyze My Work
            </button>
          </div>
          <div className="whiteboard-scroll-container">
            <canvas
              ref={canvasRef}
              className="whiteboard-canvas"
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
            />
          </div>
        </div>

        <div className="chat-section">
          <div className="messages-container">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <strong>{msg.role === 'user' ? 'You' : 'AI Tutor'}:</strong>
                <p>{msg.content}</p>
              </div>
            ))}
            {isProcessing && (
              <div className="message assistant processing">
                <strong>AI Tutor:</strong>
                <p>Thinking...</p>
              </div>
            )}
          </div>

          <div className="input-section">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question or describe what you need help with..."
              disabled={isProcessing}
              rows={2}
            />
            <div className="input-actions">
              <button 
                onClick={toggleListening} 
                className={`voice-button ${isListening ? 'listening' : ''}`}
                disabled={isProcessing}
              >
                {isListening ? '🔴 Stop' : '🎤 Speak'}
              </button>
              {isSpeaking && (
                <button 
                  onClick={stopSpeaking}
                  className="stop-speech-button"
                >
                  🔇 Stop AI Voice
                </button>
              )}
              <button 
                onClick={() => handleSubmit()} 
                className="submit-button"
                disabled={!userInput.trim() || isProcessing}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AITutorPage; 