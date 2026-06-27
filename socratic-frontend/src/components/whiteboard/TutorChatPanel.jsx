import React, { useEffect, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import CircularProgress from '@mui/material/CircularProgress';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import MicRoundedIcon from '@mui/icons-material/MicRounded';
import MessageBubble from './MessageBubble';

const WELCOME =
  "Hello! I'm your AI tutor. Ask me anything or describe what you'd like to learn. " +
  'I can explain concepts, work through problems, and sketch them out on the board.';

function TutorChatPanel({ messages, isProcessing, isListening, onSend, onMic }) {
  const [input, setInput] = useState('');
  const listEndRef = useRef(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const submit = () => {
    const text = input.trim();
    if (!text || isProcessing) return;
    onSend(text);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <Paper
      square
      elevation={0}
      sx={{
        width: { xs: '100%', md: 400 },
        flexShrink: 0,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderLeft: { md: '1px solid' },
        borderTop: { xs: '1px solid', md: 'none' },
        borderColor: { xs: 'divider', md: 'divider' },
      }}
    >
      <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="subtitle1" fontWeight={700}>
          Chat &amp; Questions
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Ask anything or request explanations
        </Typography>
      </Box>

      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          px: 2,
          py: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 1.5,
        }}
      >
        {messages.length === 0 && <MessageBubble role="assistant" content={WELCOME} />}
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {isProcessing && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary', pl: 5 }}>
            <CircularProgress size={14} thickness={5} />
            <Typography variant="caption">Thinking…</Typography>
          </Box>
        )}
        <div ref={listEndRef} />
      </Box>

      <Box sx={{ p: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
          <IconButton
            onClick={onMic}
            color={isListening ? 'primary' : 'default'}
            title="Voice input"
            size="small"
          >
            <MicRoundedIcon />
          </IconButton>
          <TextField
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or describe what you need help with…"
            multiline
            maxRows={5}
            fullWidth
            size="small"
          />
          <IconButton
            onClick={submit}
            color="primary"
            disabled={isProcessing || !input.trim()}
            title="Send"
          >
            <SendRoundedIcon />
          </IconButton>
        </Box>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 0.5, pl: 5.5 }}
        >
          Press Enter to send, Shift+Enter for a new line
        </Typography>
      </Box>
    </Paper>
  );
}

export default TutorChatPanel;
