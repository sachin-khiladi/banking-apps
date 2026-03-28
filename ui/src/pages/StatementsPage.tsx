/**
 * StatementsPage — request a monthly e-mail statement.
 */

import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import { statementService } from '../services/statementService';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const currentYear = new Date().getFullYear();
const YEARS = Array.from({ length: 5 }, (_, i) => currentYear - i);

const StatementsPage: React.FC = () => {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(currentYear);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    setSuccess(null);
    setError(null);
    setLoading(true);
    try {
      const result = await statementService.emailStatement({
        period_month: month,
        period_year: year,
        recipient_email: email || undefined,
      });
      setSuccess(
        `Statement for ${MONTHS[result.period_month - 1]} ${result.period_year} sent to ${result.recipient_email}.`
      );
    } catch {
      setError('Failed to send statement. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} color="primary.main" mb={1}>
        Statements
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        Request a monthly account statement to be delivered by e-mail.
      </Typography>

      <Paper elevation={0} sx={{ p: 4, maxWidth: 540 }}>
        {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Month</InputLabel>
              <Select
                value={month}
                label="Month"
                onChange={(e) => setMonth(Number(e.target.value))}
              >
                {MONTHS.map((m, i) => (
                  <MenuItem key={m} value={i + 1}>{m}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Year</InputLabel>
              <Select
                value={year}
                label="Year"
                onChange={(e) => setYear(Number(e.target.value))}
              >
                {YEARS.map((y) => (
                  <MenuItem key={y} value={y}>{y}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Recipient e-mail (optional)"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Defaults to your profile e-mail"
              type="email"
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={<EmailIcon />}
              onClick={handleSend}
              disabled={loading}
            >
              {loading ? 'Sending…' : 'Send Statement'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default StatementsPage;
