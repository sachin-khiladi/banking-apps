# SecureBank UI

Modern React frontend for the Banking System API built with:

- **React 18** + **TypeScript** (Vite)
- **Material UI v6** — deep-navy / emerald design system
- **Redux Toolkit** — typed account and profile state slices
- **Microsoft MSAL** (`@azure/msal-react`) — Azure AD B2C authentication
- **Axios** — typed API service layer

## Prerequisites

| Tool | Minimum version |
|---|---|
| Node.js | 18 |
| npm | 9 |

## Quick Start (local dev)

```bash
cd ui

# 1. Install dependencies
npm install

# 2. Copy and configure environment variables
cp .env.example .env.local
# Edit .env.local — set VITE_API_BASE_URL to point at the running FastAPI backend

# 3. Start the development server
npm run dev
# → http://localhost:3000
```

### Dev-mode login

When the `VITE_B2C_*` variables are **not** set, the app falls back to a
username/password form that calls the backend `/token` endpoint.  
Default credentials (from the backend's in-memory dev store):

| Username | Password | Role |
|---|---|---|
| `johndoe` | `secret` | customer |
| `bankadmin` | `adminpass` | bank\_employee |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | FastAPI backend base URL (e.g. `http://localhost:8000`) |
| `VITE_B2C_TENANT_NAME` | B2C only | Azure AD B2C tenant name |
| `VITE_B2C_CLIENT_ID` | B2C only | App (client) ID in your B2C tenant |
| `VITE_B2C_SUSI_FLOW` | B2C only | Sign-up / sign-in user flow (default: `B2C_1_signupsignin`) |
| `VITE_REDIRECT_URI` | B2C only | OAuth2 redirect URI (default: `window.location.origin`) |
| `VITE_API_SCOPE` | B2C only | Backend API scope URI |

## Available Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start Vite dev server with HMR on port 3000 |
| `npm run build` | TypeScript check + production bundle → `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | ESLint (TypeScript strict) |

## Project Structure

```
ui/
├── src/
│   ├── auth/              # MSAL config and singleton instance
│   ├── components/
│   │   ├── accounts/      # Account cards, create/close dialogs
│   │   └── common/        # Layout, NavBar, ProtectedRoute
│   ├── hooks/             # Typed Redux hooks
│   ├── pages/             # Dashboard, Accounts, Profile, Statements, Login
│   ├── services/          # Axios API clients (account, profile, statement)
│   ├── store/             # Redux slices (accounts, profile)
│   ├── types/             # TypeScript interfaces mirroring backend models
│   └── theme.ts           # MUI custom theme
└── .env.example           # Environment variable template
```

## Feature Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | MSAL B2C redirect or dev username/password form |
| Dashboard | `/` | Balance summary, account cards overview |
| Accounts | `/accounts` | Full account list with open/close actions |
| Profile | `/profile` | View and edit user profile (PATCH semantics) |
| Statements | `/statements` | Request monthly e-mail statement |
