import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserInfo } from '../types';

interface AuthState {
  isAuthenticated: boolean;
  isAdmin: boolean;
  token: string | null;
  userInfo: UserInfo | null;
  
  setAuth: (token: string, userInfo?: UserInfo) => void;
  setAdminAuth: (token: string) => void;
  updateUserInfo: (userInfo: UserInfo) => void;
  logout: () => void;
  adminLogout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      isAdmin: false,
      token: null,
      userInfo: null,

      setAuth: (token: string, userInfo?: UserInfo) => {
        localStorage.setItem('auth_token', token);
        set({ 
          isAuthenticated: true, 
          token,
          userInfo: userInfo || null,
        });
      },

      setAdminAuth: (token: string) => {
        localStorage.setItem('admin_token', token);
        set({ isAdmin: true, token });
      },

      updateUserInfo: (userInfo: UserInfo) => {
        set({ userInfo });
      },

      logout: () => {
        localStorage.removeItem('auth_token');
        set({ 
          isAuthenticated: false, 
          token: null,
          userInfo: null,
        });
      },

      adminLogout: () => {
        localStorage.removeItem('admin_token');
        set({ isAdmin: false, token: null });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);