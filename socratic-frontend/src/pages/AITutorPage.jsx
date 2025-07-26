import React, { useState, useEffect, useRef, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../styles/AITutorPage.css';
import API_URL, { fetchWithAuth } from '../config/api';
import MathText from '../components/MathText';

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
  const [aiMode, setAiMode] = useState('jess'); // 'sally' or 'jess' mode
  const [toolMode, setToolMode] = useState('draw'); // 'draw' or 'text'
  const [textInputs, setTextInputs] = useState([]); // Text elements on canvas
  const [activeTextInput, setActiveTextInput] = useState(null);

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

  const handleCanvasClick = (e) => {
    if (toolMode !== 'text') return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Add new text input
    const newTextInput = {
      x: x,
      y: y,
      text: ''
    };
    
    setTextInputs([...textInputs, newTextInput]);
    setActiveTextInput(textInputs.length);
  };
  
  const updateTextInput = (index, text) => {
    const newTextInputs = [...textInputs];
    newTextInputs[index].text = text;
    setTextInputs(newTextInputs);
  };
  
  const finalizeTextInput = (index) => {
    const textInput = textInputs[index];
    if (textInput.text.trim() && context) {
      // Draw text on canvas
      context.font = '16px Arial';
      context.fillStyle = '#000000';
      context.fillText(textInput.text, textInput.x, textInput.y);
    }
    
    // Remove the input
    const newTextInputs = textInputs.filter((_, i) => i !== index);
    setTextInputs(newTextInputs);
    setActiveTextInput(null);
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
      mode: aiMode,
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
      
      // Ensure SVG has proper namespace and encoding
      let processedSvg = svgContent;
      if (!svgContent.includes('xmlns=')) {
        // Add namespace if missing
        processedSvg = svgContent.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
      }
      
      // Ensure proper XML declaration
      if (!processedSvg.startsWith('<?xml')) {
        processedSvg = '<?xml version="1.0" encoding="UTF-8"?>' + processedSvg;
      }
      
      // Try direct Canvas rendering first
      try {
        // Parse SVG and extract text elements for direct canvas rendering
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(processedSvg, 'image/svg+xml');
        const svgElement = svgDoc.documentElement;
        
        // Check for parsing errors
        if (svgDoc.querySelector('parsererror')) {
          throw new Error('SVG parsing error');
        }
        
        // Get all text elements
        const textElements = svgElement.querySelectorAll('text');
        
        if (textElements.length > 0) {
          // Direct canvas rendering for text elements
          ctx.save();
          
          textElements.forEach(textEl => {
            const x = parseFloat(textEl.getAttribute('x')) || 0;
            const y = parseFloat(textEl.getAttribute('y')) || 0;
            const fontSize = textEl.getAttribute('font-size') || '16px';
            const fontFamily = textEl.getAttribute('font-family') || 'Arial';
            const fill = textEl.getAttribute('fill') || '#2563eb';
            const text = textEl.textContent;
            
            ctx.font = `${fontSize} ${fontFamily}`;
            ctx.fillStyle = fill;
            ctx.fillText(text, x, drawingY + y);
          });
          
          ctx.restore();
          console.log('SVG rendered directly to canvas using text elements');
          
          // Update positions
          setCurrentDrawingY(drawingY);
          const actualNextY = drawingY + 300 + 100; // Approximate height
          setNextDrawingY(prevNext => Math.max(prevNext, actualNextY));
          
          // Scroll to the new content
          const scrollContainer = document.querySelector('.whiteboard-scroll-container');
          if (scrollContainer) {
            scrollContainer.scrollTop = drawingY - 200;
          }
          
          return; // Success, exit early
        }
      } catch (directRenderError) {
        console.log('Direct canvas rendering failed, falling back to image method:', directRenderError);
      }
      
      // Fallback to Image-based rendering
      const svgBlob = new Blob([processedSvg], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      const img = new Image();
      
      img.onload = () => {
        try {
          // Draw the SVG image onto the canvas at the reserved Y position
          ctx.drawImage(img, 0, drawingY);
          console.log('SVG successfully rendered to canvas at Y:', drawingY);
          console.log('Image dimensions:', img.width, 'x', img.height);
          
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
        console.error('SVG content that failed:', processedSvg);
        console.error('First 200 chars of SVG:', processedSvg.substring(0, 200));
        
        // Try alternative rendering method using foreignObject
        try {
          console.log('Attempting fallback rendering...');
        } catch (fallbackError) {
          console.error('Fallback rendering also failed:', fallbackError);
        }
        
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
      
      const apiKey = 'AIzaSyB_lC4glTCt2tmTWxq5yrO4sSNRWLITggI';
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
      <div className="ai-tutor-header animate-slide-up">
        <div className="header-left">
          <button onClick={() => navigate('/student/home')} className="back-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </button>
          <div className="header-divider"></div>
          <h1>AI Tutor</h1>
        </div>
      </div>

      <div className="ai-tutor-content">
        <div className="whiteboard-section">
          {/* Toolbar */}
          <div className="toolbar-section animate-slide-up" style={{ animationDelay: '300ms' }}>
            <div className="tool-buttons">
              {/* Sally/Jess Toggle */}
              <button
                className="tool-button"
                onClick={() => setAiMode(aiMode === 'sally' ? 'jess' : 'sally')}
                title={`Switch to ${aiMode === 'sally' ? 'Jess' : 'Sally'} mode`}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                {aiMode === 'sally' ? 'Sally' : 'Jess'}
              </button>
              
              {/* Text Tool */}
              <button
                className={`tool-button ${toolMode === 'text' ? 'active' : ''}`}
                onClick={() => setToolMode('text')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 7V4h16v3M9 20h6M12 4v16"/>
                </svg>
                Text
              </button>
              
              {/* Draw Tool */}
              <button
                className={`tool-button ${toolMode === 'draw' ? 'active' : ''}`}
                onClick={() => setToolMode('draw')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 19l7-7 3 3-7 7-3-3z"/>
                  <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
                  <path d="M2 2l7.586 7.586"/>
                  <circle cx="11" cy="11" r="2"/>
                </svg>
                Draw
              </button>
              
              {/* Stop Speech Button - only shows when AI is speaking */}
              {isSpeaking && (
                <button
                  onClick={stopSpeaking}
                  className="stop-speech-button"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="6" y="4" width="4" height="16"/>
                    <rect x="14" y="4" width="4" height="16"/>
                  </svg>
                  Stop Speech
                </button>
              )}
            </div>
            
            <button onClick={clearCanvas} className="control-button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
              </svg>
              Clear Board
            </button>
          </div>
          
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
          <div className="whiteboard-scroll-container animate-scale-in" style={{ animationDelay: '400ms' }}>
            {/* Welcome Message - shows when canvas is empty */}
            {isCanvasEmpty() && (
              <div className="welcome-message animate-fade-in" style={{ animationDelay: '600ms' }}>
                <div className="welcome-content">
                  <div className="welcome-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 7V4h16v3M9 20h6M12 4v16"/>
                    </svg>
                  </div>
                  <h3 className="welcome-title">Interactive Learning Space</h3>
                  <p className="welcome-description">
                    Start a conversation with your AI tutor or use the drawing tools to visualize concepts together
                  </p>
                </div>
              </div>
            )}
            <canvas
              ref={canvasRef}
              className={`whiteboard-canvas ${toolMode === 'text' ? 'text-mode' : ''}`}
              onMouseDown={toolMode === 'draw' ? startDrawing : handleCanvasClick}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
            />
            {/* Render text inputs */}
            {textInputs.map((textInput, index) => (
              <input
                key={index}
                type="text"
                className="canvas-text-input"
                style={{
                  left: textInput.x + 'px',
                  top: textInput.y + 'px',
                  display: activeTextInput === index ? 'block' : 'none'
                }}
                value={textInput.text}
                onChange={(e) => updateTextInput(index, e.target.value)}
                onBlur={() => finalizeTextInput(index)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    finalizeTextInput(index);
                  }
                }}
                autoFocus
              />
            ))}
          </div>
        </div>

        <div className="chat-section animate-slide-up" style={{ animationDelay: '500ms' }}>
          {/* Chat Header */}
          <div className="chat-header">
            <h3>Chat & Questions</h3>
            <p>Ask anything or request explanations</p>
          </div>
          
          <div className="messages-container">
            {/* Welcome message from AI */}
            {messages.length === 0 && (
              <div className="message assistant animate-fade-in" style={{ animationDelay: '700ms' }}>
                <div className="message-avatar">AI</div>
                <div className="message-card">
                  <p>
                    Hello! I'm your AI tutor. Feel free to ask me anything or describe what you'd like to learn today. 
                    I can help explain concepts, solve problems, or guide you through exercises.
                  </p>
                </div>
              </div>
            )}
            
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <>
                    <div className="message-avatar">AI</div>
                    <div className="message-card">
                      <MathText text={msg.content} />
                    </div>
                  </>
                ) : (
                  <>
                    <strong>{msg.role === 'user' ? 'You' : 'AI Tutor'}:</strong>
                    <div className="message-content">
                      <MathText text={msg.content} />
                    </div>
                  </>
                )}
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
            <div className="input-wrapper">
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask a question or describe what you need help with..."
                disabled={isProcessing}
                rows={1}
              />
            </div>
            <div className="input-info">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>{userInput.length}/500</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AITutorPage; 
