/**
 * Redux store configuration.
 */

import { configureStore } from '@reduxjs/toolkit';
import accountsReducer from './accountsSlice';
import profileReducer from './profileSlice';

export const store = configureStore({
  reducer: {
    accounts: accountsReducer,
    profile: profileReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
