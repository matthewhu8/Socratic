import { createTheme } from '@mui/material/styles';

// Modern dark "focus mode" theme. Near-black surfaces keep the whiteboard the
// visual centerpiece; a single violet accent carries interactive emphasis.
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#7c6cff',
      light: '#9d90ff',
      dark: '#5a4bd6',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#4dd6c1',
    },
    background: {
      default: '#0f1115',
      paper: '#1a1d24',
    },
    text: {
      primary: '#e8eaf0',
      secondary: '#9aa0ad',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily:
      '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h6: { fontWeight: 600, letterSpacing: 0.2 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#15171d',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
  },
});

export default theme;
