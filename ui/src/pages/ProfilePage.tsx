/**
 * ProfilePage — view and edit the authenticated user's profile.
 */

import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { fetchProfile, updateProfile } from '../store/profileSlice';
import type { Address, UserProfileUpdateRequest } from '../types/api';

const ProfilePage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { data: profile, loading, error } = useAppSelector((s) => s.profile);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<UserProfileUpdateRequest>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    dispatch(fetchProfile());
  }, [dispatch]);

  const startEdit = () => {
    setForm({
      email: profile?.email,
      mobile_no: profile?.mobile_no,
      address: profile?.address ? { ...profile.address } : undefined,
    });
    setSaveError(null);
    setEditing(true);
  };

  /** Merge a single address field into the form state without losing other fields. */
  const setAddressField = (key: keyof Address, value: string) => {
    setForm((prev) => ({
      ...prev,
      address: {
        line1: prev.address?.line1 ?? '',
        city: prev.address?.city ?? '',
        state: prev.address?.state ?? '',
        postal_code: prev.address?.postal_code ?? '',
        country: prev.address?.country ?? '',
        ...prev.address,
        [key]: value,
      },
    }));
  };

  const handleSave = async () => {
    setSaveError(null);
    setSaving(true);
    const result = await dispatch(updateProfile(form));
    setSaving(false);
    if (updateProfile.rejected.match(result)) {
      setSaveError(result.error.message ?? 'Failed to update profile.');
    } else {
      setEditing(false);
    }
  };

  const field = (label: string, value: string | undefined) => (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body1" fontWeight={500}>
        {value ?? '—'}
      </Typography>
    </Box>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={700} color="primary.main">
          My Profile
        </Typography>
        {!editing && profile && (
          <Button variant="outlined" startIcon={<EditIcon />} onClick={startEdit}>
            Edit
          </Button>
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading && !profile && (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      )}

      {profile && !editing && (
        <Paper elevation={0} sx={{ p: 4 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>{field('Owner ID', profile.owner_id)}</Grid>
            <Grid item xs={12} sm={6}>{field('Email', profile.email)}</Grid>
            <Grid item xs={12} sm={6}>{field('Mobile', profile.mobile_no)}</Grid>
            <Grid item xs={12} sm={6}>
              {field('Member Since', new Date(profile.created_at).toLocaleDateString())}
            </Grid>

            {profile.address && (
              <>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight={600} color="primary.main">
                    Address
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>{field('Line 1', profile.address.line1)}</Grid>
                <Grid item xs={12} sm={6}>{field('Line 2', profile.address.line2)}</Grid>
                <Grid item xs={12} sm={4}>{field('City', profile.address.city)}</Grid>
                <Grid item xs={12} sm={4}>{field('State', profile.address.state)}</Grid>
                <Grid item xs={12} sm={4}>{field('Postal Code', profile.address.postal_code)}</Grid>
                <Grid item xs={12} sm={6}>{field('Country', profile.address.country)}</Grid>
              </>
            )}
          </Grid>
        </Paper>
      )}

      {editing && (
        <Paper elevation={0} sx={{ p: 4 }}>
          {saveError && <Alert severity="error" sx={{ mb: 2 }}>{saveError}</Alert>}
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Email"
                fullWidth
                value={form.email ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Mobile (E.164)"
                fullWidth
                value={form.mobile_no ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, mobile_no: e.target.value }))}
                placeholder="+12065550100"
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight={600} color="primary.main">
                Address
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Line 1"
                fullWidth
                value={form.address?.line1 ?? ''}
                onChange={(e) => setAddressField('line1', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Line 2"
                fullWidth
                value={form.address?.line2 ?? ''}
                onChange={(e) => setAddressField('line2', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="City"
                fullWidth
                value={form.address?.city ?? ''}
                onChange={(e) => setAddressField('city', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="State"
                fullWidth
                value={form.address?.state ?? ''}
                onChange={(e) => setAddressField('state', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                label="Postal Code"
                fullWidth
                value={form.address?.postal_code ?? ''}
                onChange={(e) => setAddressField('postal_code', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                label="Country (2-letter)"
                fullWidth
                value={form.address?.country ?? ''}
                inputProps={{ maxLength: 2 }}
                onChange={(e) => setAddressField('country', e.target.value.toUpperCase())}
              />
            </Grid>

            <Grid item xs={12} display="flex" gap={2} justifyContent="flex-end">
              <Button
                startIcon={<CancelIcon />}
                onClick={() => setEditing(false)}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving…' : 'Save Changes'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default ProfilePage;
