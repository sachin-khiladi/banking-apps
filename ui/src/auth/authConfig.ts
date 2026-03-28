/**
 * Azure AD B2C MSAL configuration.
 *
 * Environment variables are injected at build time by Vite (VITE_* prefix).
 * For local dev, copy ui/.env.example to ui/.env.local and fill in the values.
 */

import { Configuration, LogLevel } from '@azure/msal-browser';

const tenantName = import.meta.env.VITE_B2C_TENANT_NAME as string | undefined;
const clientId = import.meta.env.VITE_B2C_CLIENT_ID as string | undefined;
const susiFlow = (import.meta.env.VITE_B2C_SUSI_FLOW as string | undefined) ?? 'B2C_1_signupsignin';
const redirectUri = (import.meta.env.VITE_REDIRECT_URI as string | undefined) ?? window.location.origin;
const apiScope = import.meta.env.VITE_API_SCOPE as string | undefined;

/** Authority URL for the sign-up / sign-in user flow. */
export const b2cPolicies = {
  names: { signUpSignIn: susiFlow },
  authorities: {
    signUpSignIn: {
      authority: `https://${tenantName}.b2clogin.com/${tenantName}.onmicrosoft.com/${susiFlow}`,
    },
  },
  authorityDomain: `${tenantName}.b2clogin.com`,
};

/** MSAL PublicClientApplication config. */
export const msalConfig: Configuration = {
  auth: {
    clientId: clientId ?? '',
    authority: b2cPolicies.authorities.signUpSignIn.authority,
    knownAuthorities: [b2cPolicies.authorityDomain],
    redirectUri,
    postLogoutRedirectUri: redirectUri,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        if (level === LogLevel.Error) console.error(message);
        if (level === LogLevel.Warning) console.warn(message);
      },
      logLevel: LogLevel.Warning,
    },
  },
};

/** Token request scopes — used to acquire API access tokens. */
export const loginRequest = {
  scopes: apiScope ? [apiScope] : ['openid', 'profile'],
};

/** Whether MSAL is fully configured (B2C env vars present). */
export const isMsalConfigured = Boolean(tenantName && clientId);
