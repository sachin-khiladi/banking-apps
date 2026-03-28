/** TypeScript types mirroring the backend Pydantic models. */

// ── Accounts ──────────────────────────────────────────────────────────────────

export type AccountType = 'SAVINGS' | 'CURRENT' | 'FIXED_DEPOSIT';
export type AccountStatus = 'ACTIVE' | 'CLOSED';

export interface Account {
  account_number: string;
  owner_id: string;
  account_type: AccountType;
  status: AccountStatus;
  balance: string;
  currency: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface AccountAdminResponse extends Account {
  is_deleted: boolean;
  closure_reason: string | null;
}

export interface AccountBalanceResponse {
  account_number: string;
  account_type: AccountType;
  available_balance: string;
  currency: string;
  status: AccountStatus;
  as_of: string;
}

export interface AccountCreateRequest {
  account_type: AccountType;
  currency?: string;
  initial_deposit?: number;
}

export interface AccountUpdateRequest {
  currency?: string;
}

export interface AccountCloseRequest {
  closure_reason: string;
}

// ── User profile ──────────────────────────────────────────────────────────────

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface UserProfile {
  owner_id: string;
  email: string;
  mobile_no: string;
  address?: Address;
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdateRequest {
  email?: string;
  mobile_no?: string;
  address?: Address;
}

// ── Statements ────────────────────────────────────────────────────────────────

export interface StatementEmailRequest {
  period_month: number;
  period_year: number;
  recipient_email?: string;
}

export interface StatementEmailResponse {
  recipient_email: string;
  period_month: number;
  period_year: number;
  accounts_included: number;
}
