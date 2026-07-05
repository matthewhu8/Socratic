import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import DeleteSweepRoundedIcon from '@mui/icons-material/DeleteSweepRounded';
import StopCircleRoundedIcon from '@mui/icons-material/StopCircleRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import VolumeOffRoundedIcon from '@mui/icons-material/VolumeOffRounded';
import VolumeUpRoundedIcon from '@mui/icons-material/VolumeUpRounded';

function WhiteboardAppBar({
  onClear,
  isSpeaking,
  onStopSpeech,
  onLogout,
  isMuted,
  onToggleMute,
}) {
  return (
    <AppBar position="static" elevation={0}>
      <Toolbar variant="dense" sx={{ gap: 1.5 }}>
        <AutoAwesomeRoundedIcon sx={{ color: 'primary.main' }} />
        <Typography variant="h6" sx={{ mr: 2 }}>
          AI Tutor
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        {isSpeaking && (
          <Button
            color="inherit"
            size="small"
            startIcon={<StopCircleRoundedIcon />}
            onClick={onStopSpeech}
          >
            Stop Speech
          </Button>
        )}
        <Button
          color="inherit"
          size="small"
          startIcon={<DeleteSweepRoundedIcon />}
          onClick={onClear}
        >
          Clear Board
        </Button>
        <Tooltip title={isMuted ? 'Unmute tutor voice' : 'Silent learning: mute tutor voice'}>
          <Button
            color="inherit"
            variant={isMuted ? 'outlined' : 'text'}
            size="small"
            startIcon={isMuted ? <VolumeOffRoundedIcon /> : <VolumeUpRoundedIcon />}
            onClick={onToggleMute}
          >
            Silent Learning
          </Button>
        </Tooltip>
        <Tooltip title="Log out">
          <Button color="inherit" size="small" startIcon={<LogoutRoundedIcon />} onClick={onLogout}>
            Log out
          </Button>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}

export default WhiteboardAppBar;
