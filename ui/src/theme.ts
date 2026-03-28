/**
 * Material UI v6 custom theme for SecureBank.
 *
 * Palette: Deep navy primary, vibrant green accent — professional banking look.
 */

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0D2B55',       // Deep navy
      light: '#1A4B8C',
      dark: '#071728',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#00A86B',       // Emerald green
      light: '#2DC78A',
      dark: '#007A4D',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F4F6F9',
      paper: '#FFFFFF',
    },
    success: { main: '#2DC78A' },
    warning: { main: '#F5A623' },
    error:   { main: '#E53935' },
    text: {
      primary: '#12263A',
      secondary: '#5A7184',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8, paddingLeft: 20, paddingRight: 20 },
        containedPrimary: {
          background: 'linear-gradient(135deg, #1A4B8C 0%, #0D2B55 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #0D2B55 0%, #071728 100%)',
          },
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #2DC78A 0%, #00A86B 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #00A86B 0%, #007A4D 100%)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 12px rgba(13,43,85,0.08)',
          borderRadius: 16,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, borderRadius: 6 },
      },
    },
    MuiTextField: {
      defaultProps: { size: 'small' },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(90deg, #0D2B55 0%, #1A4B8C 100%)',
          boxShadow: '0 2px 8px rgba(13,43,85,0.18)',
        },
      },
    },
  },
});

export default theme;
