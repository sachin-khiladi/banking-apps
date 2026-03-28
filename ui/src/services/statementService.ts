/**
 * Statement service — wraps all /statements API endpoints.
 */

import { apiClient } from './api';
import type { StatementEmailRequest, StatementEmailResponse } from '../types/api';

export const statementService = {
  /** Send monthly statement e-mail. */
  emailStatement: (payload: StatementEmailRequest) =>
    apiClient
      .post<StatementEmailResponse>('/statements/email', payload)
      .then((r) => r.data),
};
