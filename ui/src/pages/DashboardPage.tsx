/**
 * Dashboard — summary cards for account balances and quick actions.
 */

import React, { useEffect } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  Paper,
  Skeleton,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { fetchAccounts } from '../store/accountsSlice';
import { fetchProfile } from '../store/profileSlice';
import AccountCard from '../components/accounts/AccountCard';

const DashboardPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: accounts, loading, error } = useAppSelector((s) => s.accounts);
  const { data: profile } = useAppSelector((s) => s.profile);

  useEffect(() => {
    dispatch(fetchAccounts());
    dispatch(fetchProfile());
  }, [dispatch]);

  const totalBalance = accounts.reduce((sum, a) => sum + parseFloat(a.balance), 0);

  return (
    <Box>
      {/* Greeting */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} color="primary.main">
          {profile ? `Welcome back, ${profile.email.split('@')[0]}` : 'Welcome back'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here&apos;s an overview of your banking activity.
        </Typography>
      </Box>

      {/* Summary tile */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={4}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #0D2B55 0%, #1A4B8C 100%)',
              color: 'white',
              borderRadius: 3,
            }}
          >
            <Typography variant="caption" sx={{ opacity: 0.75 }}>
              Total Balance
            </Typography>
            {loading ? (
              <Skeleton variant="text" width={120} sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
            ) : (
              <Typography variant="h4" fontWeight={700}>
                USD{' '}
                {totalBalance.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Typography>
            )}
            <Typography variant="caption" sx={{ opacity: 0.6 }}>
              Across {accounts.length} active account{accounts.length !== 1 ? 's' : ''}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Accounts section */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6" fontWeight={600}>
          My Accounts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          component={Link}
          to="/accounts"
          size="small"
        >
          Open Account
        </Button>
      </Box>

      {loading && (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!loading && accounts.length === 0 && !error && (
        <Paper elevation={0} sx={{ p: 4, textAlign: 'center', bgcolor: 'background.paper' }}>
          <Typography color="text.secondary" mb={2}>
            You don&apos;t have any accounts yet.
          </Typography>
          <Button variant="contained" component={Link} to="/accounts" startIcon={<AddIcon />}>
            Open Your First Account
          </Button>
        </Paper>
      )}

      <Box display="flex" gap={3} flexWrap="wrap">
        {accounts.map((account) => (
          <AccountCard key={account.account_number} account={account} />
        ))}
      </Box>
    </Box>
  );
};

export default DashboardPage;
