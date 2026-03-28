/**
 * Account service — wraps all /accounts and /admin/accounts API endpoints.
 */

import { apiClient } from './api';
import type {
  Account,
  AccountAdminResponse,
  AccountBalanceResponse,
  AccountCloseRequest,
  AccountCreateRequest,
  AccountType,
  AccountUpdateRequest,
} from '../types/api';

export const accountService = {
  /** List all active accounts for the authenticated user. */
  listAccounts: () => apiClient.get<Account[]>('/accounts').then((r) => r.data),

  /** Get a single account by number. */
  getAccount: (accountNumber: string) =>
    apiClient.get<Account>(`/accounts/${accountNumber}`).then((r) => r.data),

  /** Create a new bank account. */
  createAccount: (payload: AccountCreateRequest) =>
    apiClient.post<Account>('/accounts', payload).then((r) => r.data),

  /** Update mutable fields of an account. */
  updateAccount: (accountNumber: string, payload: AccountUpdateRequest) =>
    apiClient.put<Account>(`/accounts/${accountNumber}`, payload).then((r) => r.data),

  /** Soft-close an account. */
  closeAccount: (accountNumber: string, payload: AccountCloseRequest) =>
    apiClient
      .post<Account>(`/accounts/${accountNumber}/close`, payload)
      .then((r) => r.data),

  /** Get balance for a specific account type. */
  getBalance: (accountType: AccountType) =>
    apiClient
      .get<AccountBalanceResponse>(`/accounts/balance/${accountType}`)
      .then((r) => r.data),

  // ── Admin ──────────────────────────────────────────────────────────────────

  /** [Admin] List all accounts. */
  adminListAccounts: (includeClosed = true) =>
    apiClient
      .get<AccountAdminResponse[]>('/admin/accounts', { params: { include_closed: includeClosed } })
      .then((r) => r.data),

  /** [Admin] Get any account. */
  adminGetAccount: (accountNumber: string) =>
    apiClient
      .get<AccountAdminResponse>(`/admin/accounts/${accountNumber}`)
      .then((r) => r.data),
};
