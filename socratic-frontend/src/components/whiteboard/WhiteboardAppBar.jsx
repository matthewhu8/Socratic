import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import DeleteSweepRoundedIcon from '@mui/icons-material/DeleteSweepRounded';
import StopCircleRoundedIcon from '@mui/icons-material/StopCircleRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';

function WhiteboardAppBar({ aiMode, onAiModeChange, onClear, isSpeaking, onStopSpeech, onLogout }) {
  return (
    <AppBar position="static" elevation={0}>
      <Toolbar variant="dense" sx={{ gap: 1.5 }}>
        <AutoAwesomeRoundedIcon sx={{ color: 'primary.main' }} />
        <Typography variant="h6" sx={{ mr: 2 }}>
          AI Tutor
        </Typography>

        <ToggleButtonGroup
          value={aiMode}
          exclusive
          size="small"
          onChange={(_e, val) => val && onAiModeChange(val)}
          aria-label="AI provider"
        >
          <ToggleButton value="gemini">Gemini</ToggleButton>
          <ToggleButton value="claude">Claude</ToggleButton>
        </ToggleButtonGroup>

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
