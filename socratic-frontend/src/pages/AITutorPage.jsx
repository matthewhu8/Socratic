import React, { useCallback, useContext, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import { AuthContext } from '../contexts/AuthContext';
import { useSpeech } from '../hooks/useSpeech';
import { useTutorSession } from '../hooks/useTutorSession';
import WhiteboardAppBar from '../components/whiteboard/WhiteboardAppBar';
import TutorBoard from '../components/whiteboard/TutorBoard';
import TutorChatPanel from '../components/whiteboard/TutorChatPanel';

// Thin orchestrator: wires the board, chat, and app bar to the session and
// speech hooks. All streaming/pedagogical logic lives in those hooks.
function AITutorPage() {
  const navigate = useNavigate();
  const { currentUser, logout } = useContext(AuthContext);

  const boardRef = useRef(null);
  const getBoard = useCallback(() => boardRef.current, []);

  const { isSpeaking, isListening, speakSentence, cancelSpeech, toggleListening } = useSpeech();

  const {
    isConnecting,
    error,
    messages,
    isProcessing,
    sendQuery,
    retry,
  } = useTutorSession({ currentUser, getBoard, speakSentence, cancelSpeech });

  const handleClear = useCallback(() => boardRef.current?.clear(), []);

  const handleStopSpeech = useCallback(() => cancelSpeech(), [cancelSpeech]);

  const handleLogout = useCallback(() => {
    cancelSpeech();
    logout();
    navigate('/student/auth');
  }, [cancelSpeech, logout, navigate]);

  const handleMic = useCallback(() => {
    toggleListening((transcript) => sendQuery(transcript));
  }, [toggleListening, sendQuery]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <WhiteboardAppBar
        onClear={handleClear}
        isSpeaking={isSpeaking}
        onStopSpeech={handleStopSpeech}
        onLogout={handleLogout}
      />

      {error && (
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={retry}>
              Retry
            </Button>
          }
          sx={{ borderRadius: 0 }}
        >
          {error}
        </Alert>
      )}

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
        }}
      >
        <TutorBoard ref={boardRef} />
        <TutorChatPanel
          messages={messages}
          isProcessing={isProcessing}
          isListening={isListening}
          onSend={sendQuery}
          onMic={handleMic}
        />
      </Box>

      <Backdrop open={isConnecting} sx={{ zIndex: (t) => t.zIndex.drawer + 1, color: '#fff' }}>
        <CircularProgress color="inherit" />
      </Backdrop>
    </Box>
  );
}

export default AITutorPage;
