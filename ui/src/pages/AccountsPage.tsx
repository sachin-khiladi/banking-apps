/**
 * AccountsPage — full list of accounts with create / close actions.
 */

import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { fetchAccounts } from '../store/accountsSlice';
import CreateAccountDialog from '../components/accounts/CreateAccountDialog';
import CloseAccountDialog from '../components/accounts/CloseAccountDialog';
import type { Account } from '../types/api';

const AccountsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: accounts, loading, error } = useAppSelector((s) => s.accounts);
  const [createOpen, setCreateOpen] = useState(false);
  const [closeTarget, setCloseTarget] = useState<Account | null>(null);

  useEffect(() => {
    dispatch(fetchAccounts());
  }, [dispatch]);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={700} color="primary.main">
          My Accounts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          Open Account
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : accounts.length === 0 ? (
        <Paper elevation={0} sx={{ p: 5, textAlign: 'center' }}>
          <Typography color="text.secondary" mb={2}>
            No active accounts found.
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            Open Your First Account
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper} elevation={0}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main' }}>
                {['Account Number', 'Type', 'Balance', 'Currency', 'Status', 'Opened', 'Actions'].map(
                  (h) => (
                    <TableCell key={h} sx={{ color: 'white', fontWeight: 600 }}>
                      {h}
                    </TableCell>
                  )
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {accounts.map((account) => (
                <TableRow
                  key={account.account_number}
                  hover
                  sx={{ '&:last-child td': { border: 0 } }}
                >
                  <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                    {account.account_number}
                  </TableCell>
                  <TableCell>{account.account_type.replace('_', ' ')}</TableCell>
                  <TableCell>
                    {Number(account.balance).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell>{account.currency}</TableCell>
                  <TableCell>
                    <Typography
                      variant="caption"
                      fontWeight={700}
                      color={account.status === 'ACTIVE' ? 'success.main' : 'error.main'}
                    >
                      {account.status}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {new Date(account.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<CloseIcon />}
                      onClick={() => setCloseTarget(account)}
                    >
                      Close
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <CreateAccountDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      {closeTarget && (
        <CloseAccountDialog
          open={true}
          accountNumber={closeTarget.account_number}
          onClose={() => setCloseTarget(null)}
        />
      )}
    </Box>
  );
};

export default AccountsPage;
