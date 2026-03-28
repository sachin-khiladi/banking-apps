/**
 * AccountCard — displays a single account's key details.
 */

import React from 'react';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Divider,
  Typography,
} from '@mui/material';
import SavingsIcon from '@mui/icons-material/Savings';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import LockIcon from '@mui/icons-material/Lock';
import type { Account } from '../../types/api';

interface AccountCardProps {
  account: Account;
  onClick?: (account: Account) => void;
}

const ACCOUNT_ICONS: Record<string, React.ReactNode> = {
  SAVINGS: <SavingsIcon fontSize="large" />,
  CURRENT: <AccountBalanceWalletIcon fontSize="large" />,
  FIXED_DEPOSIT: <LockIcon fontSize="large" />,
};

const ACCOUNT_COLORS: Record<string, string> = {
  SAVINGS: '#1A4B8C',
  CURRENT: '#00A86B',
  FIXED_DEPOSIT: '#F5A623',
};

const AccountCard: React.FC<AccountCardProps> = ({ account, onClick }) => {
  const color = ACCOUNT_COLORS[account.account_type] ?? '#0D2B55';
  const icon = ACCOUNT_ICONS[account.account_type];

  return (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${color} 0%, ${color}CC 100%)`,
        color: 'white',
        minWidth: 280,
        maxWidth: 340,
      }}
    >
      <CardActionArea onClick={() => onClick?.(account)} disabled={!onClick}>
        <CardContent>
          {/* Header row */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Box sx={{ opacity: 0.8 }}>{icon}</Box>
            <Chip
              label={account.status}
              size="small"
              sx={{
                bgcolor: account.status === 'ACTIVE' ? 'rgba(255,255,255,0.25)' : 'rgba(229,57,53,0.7)',
                color: 'white',
                fontWeight: 700,
              }}
            />
          </Box>

          {/* Account type label */}
          <Typography variant="caption" sx={{ opacity: 0.75, letterSpacing: 1 }}>
            {account.account_type.replace('_', ' ')}
          </Typography>

          {/* Balance */}
          <Typography variant="h5" fontWeight={700} mt={0.5}>
            {account.currency}{' '}
            {Number(account.balance).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Typography>

          <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)', my: 1.5 }} />

          {/* Account number */}
          <Typography variant="caption" sx={{ opacity: 0.75 }}>
            Account No.
          </Typography>
          <Typography variant="body2" fontWeight={600} letterSpacing={2}>
            {account.account_number.replace(/(.{4})/g, '$1 ').trim()}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

export default AccountCard;
