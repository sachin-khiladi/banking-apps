/**
 * CloseAccountDialog — confirmation modal for soft-closing an account.
 */

import React, { useState } from 'react';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
} from '@mui/material';
import { useAppDispatch } from '../../hooks/reduxHooks';
import { closeAccount } from '../../store/accountsSlice';

interface CloseAccountDialogProps {
  open: boolean;
  accountNumber: string;
  onClose: () => void;
}

const CloseAccountDialog: React.FC<CloseAccountDialogProps> = ({
  open,
  accountNumber,
  onClose,
}) => {
  const dispatch = useAppDispatch();
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleClose = async () => {
    if (reason.trim().length < 5) {
      setError('Please provide a reason of at least 5 characters.');
      return;
    }
    setError(null);
    setLoading(true);
    const result = await dispatch(
      closeAccount({ accountNumber, payload: { closure_reason: reason } })
    );
    setLoading(false);
    if (closeAccount.rejected.match(result)) {
      setError(result.error.message ?? 'Failed to close account.');
    } else {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle color="error">Close Account</DialogTitle>
      <DialogContent sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          The account will be soft-closed and marked as CLOSED. Account data is retained
          and visible to authorised bank employees. This action cannot be reversed via this
          portal.
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <TextField
          label="Reason for closure"
          multiline
          minRows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          inputProps={{ maxLength: 500 }}
          helperText={`${reason.length}/500`}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="contained" color="error" onClick={handleClose} disabled={loading}>
          {loading ? 'Closing…' : 'Close Account'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CloseAccountDialog;
