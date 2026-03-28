/**
 * Application entry point.
 *
 * Bootstraps React, MUI theme, Redux store, and MSAL provider.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Provider } from 'react-redux';
import { MsalProvider } from '@azure/msal-react';
import App from './App';
import theme from './theme';
import { store } from './store';
import { msalInstance } from './auth/msalInstance';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MsalProvider instance={msalInstance}>
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </Provider>
    </MsalProvider>
  </React.StrictMode>,
);
