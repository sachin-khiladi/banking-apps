/**
 * Redux slice for bank account state.
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { accountService } from '../services/accountService';
import type {
  Account,
  AccountCloseRequest,
  AccountCreateRequest,
  AccountType,
  AccountUpdateRequest,
} from '../types/api';

// ── Async thunks ──────────────────────────────────────────────────────────────

export const fetchAccounts = createAsyncThunk('accounts/fetchAll', () =>
  accountService.listAccounts()
);

export const createAccount = createAsyncThunk(
  'accounts/create',
  (payload: AccountCreateRequest) => accountService.createAccount(payload)
);

export const updateAccount = createAsyncThunk(
  'accounts/update',
  ({ accountNumber, payload }: { accountNumber: string; payload: AccountUpdateRequest }) =>
    accountService.updateAccount(accountNumber, payload)
);

export const closeAccount = createAsyncThunk(
  'accounts/close',
  ({ accountNumber, payload }: { accountNumber: string; payload: AccountCloseRequest }) =>
    accountService.closeAccount(accountNumber, payload)
);

export const fetchBalance = createAsyncThunk(
  'accounts/fetchBalance',
  (accountType: AccountType) => accountService.getBalance(accountType)
);

// ── Slice ─────────────────────────────────────────────────────────────────────

interface AccountsState {
  items: Account[];
  loading: boolean;
  error: string | null;
  balanceLoading: boolean;
}

const initialState: AccountsState = {
  items: [],
  loading: false,
  error: null,
  balanceLoading: false,
};

const accountsSlice = createSlice({
  name: 'accounts',
  initialState,
  reducers: {
    clearAccountsError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // fetchAccounts
    builder.addCase(fetchAccounts.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchAccounts.fulfilled, (state, action: PayloadAction<Account[]>) => {
      state.loading = false;
      state.items = action.payload;
    });
    builder.addCase(fetchAccounts.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message ?? 'Failed to load accounts.';
    });

    // createAccount
    builder.addCase(createAccount.fulfilled, (state, action: PayloadAction<Account>) => {
      state.items.push(action.payload);
    });
    builder.addCase(createAccount.rejected, (state, action) => {
      state.error = action.error.message ?? 'Failed to create account.';
    });

    // updateAccount
    builder.addCase(updateAccount.fulfilled, (state, action: PayloadAction<Account>) => {
      const idx = state.items.findIndex(
        (a) => a.account_number === action.payload.account_number
      );
      if (idx !== -1) state.items[idx] = action.payload;
    });
    builder.addCase(updateAccount.rejected, (state, action) => {
      state.error = action.error.message ?? 'Failed to update account.';
    });

    // closeAccount — mark the account as CLOSED in the local cache rather than removing it
    builder.addCase(closeAccount.fulfilled, (state, action: PayloadAction<Account>) => {
      const idx = state.items.findIndex(
        (a) => a.account_number === action.payload.account_number
      );
      if (idx !== -1) state.items[idx] = action.payload;
    });
    builder.addCase(closeAccount.rejected, (state, action) => {
      state.error = action.error.message ?? 'Failed to close account.';
    });
  },
});

export const { clearAccountsError } = accountsSlice.actions;
export default accountsSlice.reducer;
