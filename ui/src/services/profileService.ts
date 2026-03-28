/**
 * Profile service — wraps all /profile API endpoints.
 */

import { apiClient } from './api';
import type { UserProfile, UserProfileUpdateRequest } from '../types/api';

export const profileService = {
  /** Fetch the authenticated user's profile. */
  getProfile: () => apiClient.get<UserProfile>('/profile').then((r) => r.data),

  /** Partially update the authenticated user's profile. */
  updateProfile: (payload: UserProfileUpdateRequest) =>
    apiClient.patch<UserProfile>('/profile', payload).then((r) => r.data),
};
