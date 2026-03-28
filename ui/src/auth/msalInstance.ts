/**
 * Singleton MSAL PublicClientApplication instance.
 *
 * Import this wherever an MSAL instance is needed outside of React context.
 */

import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig } from './authConfig';

export const msalInstance = new PublicClientApplication(msalConfig);
