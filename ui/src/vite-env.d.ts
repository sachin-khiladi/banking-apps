/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_B2C_TENANT_NAME: string;
  readonly VITE_B2C_CLIENT_ID: string;
  readonly VITE_B2C_SUSI_FLOW: string;
  readonly VITE_REDIRECT_URI: string;
  readonly VITE_API_SCOPE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
