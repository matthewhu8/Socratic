import React from 'react';
import Box from '@mui/material/Box';
import Avatar from '@mui/material/Avatar';
import Paper from '@mui/material/Paper';
import MathText from '../MathText';

// A single chat message. Assistant messages get an avatar and a surface bubble;
// user messages are right-aligned in the accent color.
function MessageBubble({ role, content }) {
  const isAssistant = role === 'assistant';

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 1,
        alignItems: 'flex-start',
        flexDirection: isAssistant ? 'row' : 'row-reverse',
      }}
    >
      {isAssistant && (
        <Avatar
          sx={{ width: 30, height: 30, fontSize: 13, bgcolor: 'primary.main', mt: 0.25 }}
        >
          AI
        </Avatar>
      )}
      <Paper
        elevation={0}
        sx={{
          px: 1.5,
          py: 1,
          maxWidth: '85%',
          borderRadius: 2,
          bgcolor: isAssistant ? 'background.paper' : 'primary.main',
          color: isAssistant ? 'text.primary' : 'primary.contrastText',
          border: isAssistant ? '1px solid' : 'none',
          borderColor: 'divider',
          fontSize: 14,
          lineHeight: 1.55,
          wordBreak: 'break-word',
          '& .katex': { fontSize: '1em' },
        }}
      >
        <MathText text={content} />
      </Paper>
    </Box>
  );
}

export default MessageBubble;
