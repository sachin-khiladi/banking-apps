/**
 * Axios instance pre-configured for the Banking API.
 *
 * An MSAL access token (or JWT dev token) is attached to every request via the
 * request interceptor.  Components should never call axios directly.
 */

import axios from 'axios';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { msalInstance } from '../auth/msalInstance';
import { isMsalConfigured, loginRequest } from '../auth/authConfig';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const apiClient = axios.create({
  baseURL: apiBaseUrl ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
});

/** Acquire a Bearer token and attach it to the request. */
apiClient.interceptors.request.use(async (config) => {
  if (isMsalConfigured) {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      try {
        const { accessToken } = await msalInstance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0],
        });
        config.headers.Authorization = `Bearer ${accessToken}`;
      } catch (err) {
        // Only redirect for interaction-required errors (expired / missing consent).
        // Network or configuration errors should not cause a redirect loop.
        if (err instanceof InteractionRequiredAuthError) {
          await msalInstance.acquireTokenRedirect(loginRequest);
        } else {
          console.error('Token acquisition failed:', err);
        }
      }
    }
  } else {
    // Dev mode: read token from sessionStorage set by the dev login helper.
    const devToken = sessionStorage.getItem('dev_token');
    if (devToken) {
      config.headers.Authorization = `Bearer ${devToken}`;
    }
  }
  return config;
});

/** Normalise error responses into a readable message string. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string } | undefined;
    if (data?.detail) return String(data.detail);
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
