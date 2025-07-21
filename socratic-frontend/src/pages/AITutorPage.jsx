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
  const currentAudioRef = useRef(null);
  const [isListening, setIsListening] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [context, setContext] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentDrawingY, setCurrentDrawingY] = useState(50); // Track Y position for AI drawings
  const [nextDrawingY, setNextDrawingY] = useState(50); // Track next available Y position
  const [previousCanvasImage, setPreviousCanvasImage] = useState(null); // Store previous canvas state
  const [hasNewDrawing, setHasNewDrawing] = useState(false); // Track if user drew since last query
  const [showAnnotationToggle, setShowAnnotationToggle] = useState(false); // Show manual annotation toggle

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
        const canvasHeight = 800; // Initial height, will expand as needed
        
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
    setHasNewDrawing(true); // Mark that user has drawn something
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
    // Show annotation toggle if user has drawn and we have a previous image
    if (hasNewDrawing && previousCanvasImage) {
      setShowAnnotationToggle(true);
    }
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
    setNextDrawingY(50);
    // Clear drawing states
    setHasNewDrawing(false);
    setPreviousCanvasImage(null);
    setShowAnnotationToggle(false);
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

  const compressCanvas = (dataURL, maxWidth = 800, quality = 0.8) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Calculate new dimensions while maintaining aspect ratio
        const ratio = Math.min(maxWidth / img.width, maxWidth / img.height);
        canvas.width = img.width * ratio;
        canvas.height = img.height * ratio;
        
        // Draw compressed image
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Convert to compressed data URL
        const compressedDataURL = canvas.toDataURL('image/jpeg', quality);
        resolve(compressedDataURL);
      };
      img.src = dataURL;
    });
  };

  const captureAndStorePreviousCanvas = () => {
    const currentImage = captureCanvas();
    if (currentImage) {
      compressCanvas(currentImage).then(compressed => {
        setPreviousCanvasImage(compressed);
        console.log('Previous canvas image captured and compressed');
      });
    }
  };

  const isCanvasEmpty = () => {
    if (!canvasRef.current || !context) return true;
    
    const canvas = canvasRef.current;
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const pixels = imageData.data;
    
    // Check if all pixels are white (255, 255, 255)
    for (let i = 0; i < pixels.length; i += 4) {
      const r = pixels[i];
      const g = pixels[i + 1];
      const b = pixels[i + 2];
      const a = pixels[i + 3];
      
      // If we find any non-white pixel (considering alpha), canvas has content
      if (a > 0 && (r !== 255 || g !== 255 || b !== 255)) {
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async (text = userInput, includeCanvas = false, forceAnnotationMode = false) => {
    if (!text.trim() || isProcessing) return;

    // Always include canvas if there's any content on it OR if explicitly requested
    const hasCanvasContent = !isCanvasEmpty();
    const shouldIncludeCanvas = includeCanvas || hasCanvasContent;

    // Determine if this is an annotation-based query
    const isAnnotationQuery = Boolean(forceAnnotationMode || (hasNewDrawing && previousCanvasImage));
    
    const canvasData = shouldIncludeCanvas ? captureCanvas() : null;
    let compressedCanvasData = null;
    let compressedPreviousData = null;
    
    // Compress current canvas if we have data
    if (canvasData) {
      compressedCanvasData = await compressCanvas(canvasData);
    }
    
    // Compress previous canvas if this is an annotation query
    if (isAnnotationQuery && previousCanvasImage) {
      compressedPreviousData = previousCanvasImage; // Already compressed when stored
    }
    
    if (shouldIncludeCanvas) {
      console.log('Including canvas in request');
      console.log('Canvas has content:', hasCanvasContent);
      console.log('Canvas data exists:', compressedCanvasData !== null);
      console.log('Canvas data length:', compressedCanvasData ? compressedCanvasData.length : 0);
      console.log('Is annotation query:', isAnnotationQuery);
      console.log('Previous canvas exists:', compressedPreviousData !== null);
    }
    
    const requestPayload = {
      sessionId,
      query: text,
      messages: messages,
      canvasImage: compressedCanvasData,
      previousCanvasImage: compressedPreviousData,
      hasAnnotation: isAnnotationQuery,
    };
    console.log('Request payload:', JSON.stringify(requestPayload, null, 2));

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
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        throw new Error('Failed to process query');
      }

      const data = await response.json();
      console.log('Full response from backend:', JSON.stringify(data, null, 2));
      
      // Extract response and SVG content from backend
      const aiResponse = data.response;
      const svgContent = data.svgContent;
      
      console.log('AI Response:', aiResponse);
      console.log('SVG Content:', svgContent);
      
      // Add AI response to messages
      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);

      // Render SVG content if any
      if (svgContent) {
        console.log('Rendering SVG content');
        if (context) {
          renderSvgToCanvas(svgContent);
        } else if (canvasRef.current) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            setContext(ctx);
            renderSvgToCanvasWithContext(svgContent, ctx);
          }
        }
      } else {
        console.log('No SVG content received');
      }

      // Speak the response
      if (aiResponse) {
        speakText(aiResponse);
      }
      
      // Reset drawing state and capture new previous state after AI responds
      setHasNewDrawing(false);
      setShowAnnotationToggle(false);
      
      // Capture the current state as the new "previous" state after AI drawing completes
      setTimeout(() => {
        captureAndStorePreviousCanvas();
      }, 1000); // Give time for SVG rendering to complete

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

  const renderSvgToCanvasWithContext = async (svgContent, ctx) => {
    if (!ctx || !svgContent) {
      console.log('Cannot render SVG:', { hasContext: !!ctx, hasSvg: !!svgContent });
      return;
    }

    console.log('Starting to render SVG with provided context. Current Y position:', currentDrawingY);
    renderSvgInternal(svgContent, ctx);
  };

  const renderSvgToCanvas = async (svgContent) => {
    if (!context || !svgContent) {
      console.log('Cannot render SVG:', { hasContext: !!context, hasSvg: !!svgContent });
      return;
    }

    console.log('Starting to render SVG. Current Y position:', currentDrawingY);
    renderSvgInternal(svgContent, context);
  };

  const renderSvgInternal = async (svgContent, ctx) => {
    try {
      console.log('Starting SVG rendering process');
      
      // Use the next available Y position
      const drawingY = nextDrawingY;
      console.log('Drawing at Y position:', drawingY);
      
      // Clear a specific area for the new SVG content
      const drawingAreaHeight = 500; // Height for each AI drawing
      const requiredHeight = drawingY + drawingAreaHeight + 200; // Extra buffer
      
      // Immediately reserve space for this drawing
      setNextDrawingY(drawingY + drawingAreaHeight + 100);
      
      // Check if canvas needs to be expanded
      if (canvasRef.current && canvasRef.current.height < requiredHeight) {
        console.log(`Expanding canvas from ${canvasRef.current.height}px to ${requiredHeight + 500}px`);
        
        // Create temporary canvas to preserve content
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = canvasRef.current.width;
        tempCanvas.height = canvasRef.current.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Copy current canvas content
        tempCtx.drawImage(canvasRef.current, 0, 0);
        
        // Expand the main canvas
        canvasRef.current.height = requiredHeight + 500; // Add extra space
        canvasRef.current.style.height = (requiredHeight + 500) + 'px';
        
        // Restore the content
        ctx.drawImage(tempCanvas, 0, 0);
        
        // Restore context settings
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
      }
      
      // Create a white rectangle for the new drawing area
      ctx.save();
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, drawingY, canvasRef.current.width, drawingAreaHeight);
      ctx.restore();
      
      // Create SVG blob and convert to image
      const svgBlob = new Blob([svgContent], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(svgBlob);
      const img = new Image();
      
      img.onload = () => {
        try {
          // Draw the SVG image onto the canvas at the reserved Y position
          ctx.drawImage(img, 0, drawingY);
          console.log('SVG successfully rendered to canvas at Y:', drawingY);
          
          // Update the current Y position for display purposes
          const svgHeight = img.height || 300; // Default height if not available
          const maxY = drawingY + svgHeight;
          setCurrentDrawingY(drawingY); // Update current position
          
          // Update next position if the actual height is different
          const actualNextY = maxY + 100;
          setNextDrawingY(prevNext => Math.max(prevNext, actualNextY))
                    
          
          // Scroll to the new content
          const scrollContainer = document.querySelector('.whiteboard-scroll-container');
          if (scrollContainer) {
            scrollContainer.scrollTop = drawingY - 200;
          }
          
          // Clean up the object URL
          URL.revokeObjectURL(url);
        } catch (error) {
          console.error('Error drawing SVG to canvas:', error);
          URL.revokeObjectURL(url);
        }
      };
      
      img.onerror = (error) => {
        console.error('Error loading SVG image:', error);
        URL.revokeObjectURL(url);
      };
      
      // Start loading the image
      img.src = url;
      
    } catch (error) {
      console.error('Error in SVG rendering process:', error);
    }
  };

  const speakText = async (text) => {
    // Try Google Cloud TTS first
    try {
      setIsSpeaking(true);
      
      const apiKey = process.env.REACT_APP_GOOGLE_TTS_KEY;
      if (!apiKey) {
        console.log('Google TTS API key not configured, falling back to browser TTS');
        fallbackToSpeechSynthesis(text);
        return;
      }
      
      // Google Cloud TTS API request
      const response = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input: { text },
          voice: {
            languageCode: 'en-US',
            name: 'en-US-Journey-F', // Premium Neural voice - young, friendly female
            // Alternative voices to try:
            // 'en-US-Neural2-F' - Standard female neural voice
            // 'en-US-Neural2-H' - Young female neural voice
            // 'en-US-Wavenet-F' - Natural female wavenet voice
            // 'en-US-Journey-D' - Warm male journey voice
          },
          audioConfig: {
            audioEncoding: 'MP3',
            speakingRate: 1.0, // Range: 0.25 to 4.0 (1.0 is normal speed)
            pitch: 0, // Range: -20.0 to 20.0 semitones (0 is normal)
            volumeGainDb: 0, // Range: -96.0 to 16.0 dB (0 is normal)
          }
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Google TTS API error:', errorData);
        throw new Error(errorData.error?.message || 'Google TTS request failed');
      }
      
      const data = await response.json();
      
      // Create audio element from base64 response
      const audio = new Audio(`data:audio/mp3;base64,${data.audioContent}`);
      currentAudioRef.current = audio; // Store reference for stopping
      
      // Set up event handlers
      audio.onloadeddata = () => {
        console.log('Google TTS audio loaded successfully');
      };
      
      audio.onended = () => {
        setIsSpeaking(false);
        currentAudioRef.current = null;
      };
      
      audio.onerror = (error) => {
        console.error('Google TTS audio playback error:', error);
        setIsSpeaking(false);
        currentAudioRef.current = null;
        // Fallback to browser's speech synthesis
        fallbackToSpeechSynthesis(text);
      };
      
      // Play the audio
      await audio.play();
      console.log('Playing Google TTS audio');
      
    } catch (error) {
      console.error('Failed to use Google TTS:', error);
      setIsSpeaking(false);
      currentAudioRef.current = null;
      // Fallback to browser's speech synthesis
      fallbackToSpeechSynthesis(text);
    }
  };
  
  const fallbackToSpeechSynthesis = (text) => {
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
    // Stop VoiceRSS audio if playing
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    
    // Stop speech synthesis if playing
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    
    setIsSpeaking(false);
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
      {/* Header */}
      <div className="ai-tutor-header">
        <button onClick={() => navigate('/student/home')} className="back-button">
          ← Back to Home
        </button>
        <h1>AI Tutor</h1>
        {sessionId && <p className="session-info">Session ID: {sessionId}</p>}
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
            {showAnnotationToggle && (
              <div className="annotation-controls">
                <button 
                  onClick={() => {
                    setShowAnnotationToggle(false);
                    handleSubmit(userInput, false, true); // Force annotation mode
                  }}
                  className="annotation-button"
                  disabled={!userInput.trim() || isProcessing}
                >
                  Send with annotation reference
                </button>
              </div>
            )}
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