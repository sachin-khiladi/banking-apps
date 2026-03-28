/**
 * ProtectedRoute — redirects unauthenticated users to /login.
 *
 * When MSAL is configured, uses @azure/msal-react AuthenticatedTemplate.
 * In dev mode (MSAL not configured) checks for a dev_token in sessionStorage.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { isMsalConfigured } from '../../auth/authConfig';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  if (isMsalConfigured) {
    return (
      <>
        <AuthenticatedTemplate>{children}</AuthenticatedTemplate>
        <UnauthenticatedTemplate>
          <Navigate to="/login" replace />
        </UnauthenticatedTemplate>
      </>
    );
  }

  // Dev mode — check for a dev token in sessionStorage.
  const devToken = sessionStorage.getItem('dev_token');
  if (!devToken) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
