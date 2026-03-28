/**
 * NavBar — top app bar with branding, navigation links, and user menu.
 */

import React, { useState } from 'react';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import MenuIcon from '@mui/icons-material/Menu';
import { Link, useNavigate } from 'react-router-dom';
import { useMsal } from '@azure/msal-react';
import { isMsalConfigured } from '../../auth/authConfig';

interface NavBarProps {
  onDrawerToggle: () => void;
}

const navLinks = [
  { label: 'Dashboard', path: '/' },
  { label: 'Accounts', path: '/accounts' },
  { label: 'Profile', path: '/profile' },
  { label: 'Statements', path: '/statements' },
];

const NavBar: React.FC<NavBarProps> = ({ onDrawerToggle }) => {
  const { instance, accounts } = useMsal();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const username = accounts[0]?.name ?? accounts[0]?.username ?? 'User';
  const initials = username
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const handleLogout = () => {
    setAnchorEl(null);
    if (isMsalConfigured) {
      instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin });
    } else {
      sessionStorage.removeItem('dev_token');
      navigate('/login');
    }
  };

  return (
    <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
      <Toolbar>
        {/* Mobile hamburger */}
        <IconButton
          color="inherit"
          edge="start"
          onClick={onDrawerToggle}
          sx={{ mr: 1, display: { sm: 'none' } }}
          aria-label="open drawer"
        >
          <MenuIcon />
        </IconButton>

        {/* Brand */}
        <AccountBalanceIcon sx={{ mr: 1 }} />
        <Typography
          variant="h6"
          component={Link}
          to="/"
          sx={{ color: 'white', textDecoration: 'none', fontWeight: 700, flexGrow: 0 }}
        >
          SecureBank
        </Typography>

        {/* Desktop nav links */}
        <Box sx={{ flexGrow: 1, display: { xs: 'none', sm: 'flex' }, ml: 4, gap: 0.5 }}>
          {navLinks.map((link) => (
            <Button
              key={link.path}
              component={Link}
              to={link.path}
              color="inherit"
              sx={{ opacity: 0.9, '&:hover': { opacity: 1, bgcolor: 'rgba(255,255,255,0.12)' } }}
            >
              {link.label}
            </Button>
          ))}
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {/* Dev mode badge */}
        {!isMsalConfigured && (
          <Chip label="Dev Mode" size="small" color="warning" sx={{ mr: 2 }} />
        )}

        {/* User avatar & menu */}
        <Tooltip title="Account menu">
          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} sx={{ p: 0.5 }}>
            <Avatar sx={{ width: 36, height: 36, bgcolor: 'secondary.main', fontSize: 14 }}>
              {initials}
            </Avatar>
          </IconButton>
        </Tooltip>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <MenuItem disabled>
            <Typography variant="body2" fontWeight={600}>
              {username}
            </Typography>
          </MenuItem>
          <Divider />
          <MenuItem component={Link} to="/profile" onClick={() => setAnchorEl(null)}>
            My Profile
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;
