/**
 * Redux slice for user profile state.
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { profileService } from '../services/profileService';
import type { UserProfile, UserProfileUpdateRequest } from '../types/api';

// ── Async thunks ──────────────────────────────────────────────────────────────

export const fetchProfile = createAsyncThunk('profile/fetch', () =>
  profileService.getProfile()
);

export const updateProfile = createAsyncThunk(
  'profile/update',
  (payload: UserProfileUpdateRequest) => profileService.updateProfile(payload)
);

// ── Slice ─────────────────────────────────────────────────────────────────────

interface ProfileState {
  data: UserProfile | null;
  loading: boolean;
  error: string | null;
}

const initialState: ProfileState = {
  data: null,
  loading: false,
  error: null,
};

const profileSlice = createSlice({
  name: 'profile',
  initialState,
  reducers: {
    clearProfileError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchProfile.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchProfile.fulfilled, (state, action: PayloadAction<UserProfile>) => {
      state.loading = false;
      state.data = action.payload;
    });
    builder.addCase(fetchProfile.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message ?? 'Failed to load profile.';
    });

    builder.addCase(updateProfile.fulfilled, (state, action: PayloadAction<UserProfile>) => {
      state.data = action.payload;
    });
    builder.addCase(updateProfile.rejected, (state, action) => {
      state.error = action.error.message ?? 'Failed to update profile.';
    });
  },
});

export const { clearProfileError } = profileSlice.actions;
export default profileSlice.reducer;
