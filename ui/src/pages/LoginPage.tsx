/**
 * Login page — handles both MSAL (Azure AD B2C) and dev-mode login flows.
 */

import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Divider,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import MicrosoftIcon from '@mui/icons-material/Window';
import { useMsal } from '@azure/msal-react';
import { useNavigate } from 'react-router-dom';
import { isMsalConfigured, loginRequest } from '../auth/authConfig';
import { apiClient } from '../services/api';

const LoginPage: React.FC = () => {
  const { instance } = useMsal();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleMsalLogin = () => {
    instance.loginRedirect(loginRequest).catch(console.error);
  };

  const handleDevLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('username', username);
      params.set('password', password);
      const { data } = await apiClient.post<{ access_token: string }>('/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      sessionStorage.setItem('dev_token', data.access_token);
      navigate('/', { replace: true });
    } catch {
      setError('Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      minHeight="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      sx={{ background: 'linear-gradient(135deg, #0D2B55 0%, #1A4B8C 100%)' }}
    >
      <Paper elevation={8} sx={{ p: 5, maxWidth: 400, width: '100%', borderRadius: 3 }}>
        {/* Brand */}
        <Box display="flex" alignItems="center" gap={1.5} mb={3}>
          <AccountBalanceIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h5" fontWeight={700} color="primary.main">
              SecureBank
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Online Banking Portal
            </Typography>
          </Box>
        </Box>

        <Typography variant="h6" fontWeight={600} mb={3}>
          Sign in to your account
        </Typography>

        {isMsalConfigured ? (
          <>
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={<MicrosoftIcon />}
              onClick={handleMsalLogin}
              sx={{ mb: 2 }}
            >
              Sign in with Microsoft
            </Button>
            <Typography variant="caption" color="text.secondary" textAlign="center" display="block">
              You will be redirected to your organisation&apos;s Azure AD B2C login page.
            </Typography>
          </>
        ) : (
          <>
            {/* Dev-mode username / password form */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>Dev mode</strong> — MSAL not configured. Use the form below.
              <br />
              Default: <code>johndoe / secret</code>
            </Alert>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <Box display="flex" flexDirection="column" gap={2}>
              <TextField
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                onKeyDown={(e) => e.key === 'Enter' && handleDevLogin()}
              />
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleDevLogin}
                disabled={loading}
              >
                {loading ? 'Signing in…' : 'Sign In'}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />
            <Typography variant="caption" color="text.secondary">
              Configure <code>VITE_B2C_*</code> environment variables to enable Azure AD B2C
              authentication.
            </Typography>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default LoginPage;
