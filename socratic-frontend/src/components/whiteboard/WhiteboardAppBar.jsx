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

function WhiteboardAppBar({ onClear, isSpeaking, onStopSpeech, onLogout }) {
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
