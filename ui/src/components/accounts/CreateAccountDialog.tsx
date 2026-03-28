/**
 * CreateAccountDialog — modal form for opening a new bank account.
 */

import React, { useState } from 'react';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { useAppDispatch } from '../../hooks/reduxHooks';
import { createAccount } from '../../store/accountsSlice';
import type { AccountType } from '../../types/api';

interface CreateAccountDialogProps {
  open: boolean;
  onClose: () => void;
}

const CreateAccountDialog: React.FC<CreateAccountDialogProps> = ({ open, onClose }) => {
  const dispatch = useAppDispatch();
  const [accountType, setAccountType] = useState<AccountType>('SAVINGS');
  const [currency, setCurrency] = useState('USD');
  const [initialDeposit, setInitialDeposit] = useState('0');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    const deposit = parseFloat(initialDeposit);
    if (isNaN(deposit) || deposit < 0) {
      setError('Initial deposit must be a non-negative number.');
      return;
    }
    setError(null);
    setLoading(true);
    const result = await dispatch(
      createAccount({ account_type: accountType, currency, initial_deposit: deposit })
    );
    setLoading(false);
    if (createAccount.rejected.match(result)) {
      setError(result.error.message ?? 'Failed to create account.');
    } else {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Open a New Account</DialogTitle>
      <DialogContent sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}

        <FormControl fullWidth size="small">
          <InputLabel>Account Type</InputLabel>
          <Select
            value={accountType}
            label="Account Type"
            onChange={(e) => setAccountType(e.target.value as AccountType)}
          >
            <MenuItem value="SAVINGS">Savings</MenuItem>
            <MenuItem value="CURRENT">Current</MenuItem>
            <MenuItem value="FIXED_DEPOSIT">Fixed Deposit</MenuItem>
          </Select>
        </FormControl>

        <TextField
          label="Currency"
          value={currency}
          onChange={(e) => setCurrency(e.target.value.toUpperCase().slice(0, 3))}
          inputProps={{ maxLength: 3 }}
          helperText="3-letter ISO 4217 code (e.g. USD, EUR)"
        />

        <TextField
          label="Initial Deposit"
          type="number"
          value={initialDeposit}
          onChange={(e) => setInitialDeposit(e.target.value)}
          inputProps={{ min: 0, step: '0.01' }}
        />

        <Typography variant="caption" color="text.secondary">
          A unique 10-digit account number will be assigned automatically.
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Opening…' : 'Open Account'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateAccountDialog;
