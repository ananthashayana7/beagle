/**
 * Auth Store
 * Zustand store for authentication state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
    persist(
        (set, get) => ({
            // State
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            // Actions
            setUser: (user) => set({ user, isAuthenticated: !!user }),

            setTokens: (accessToken, refreshToken) => set({
                accessToken,
                refreshToken,
                isAuthenticated: !!accessToken
            }),

            login: (user, accessToken, refreshToken) => set({
                user,
                accessToken,
                refreshToken,
                isAuthenticated: true
            }),

            logout: () => set({
                user: null,
                accessToken: null,
                refreshToken: null,
                isAuthenticated: false
            }),

            updateUser: (updates) => set((state) => ({
                user: state.user ? { ...state.user, ...updates } : null
            })),
        }),
        {
            name: 'beagle-auth',
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                isAuthenticated: state.isAuthenticated
            })
        }
    )
)
