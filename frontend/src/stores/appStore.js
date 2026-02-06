/**
 * App Store
 * Global application state
 */

import { create } from 'zustand'

export const useAppStore = create((set, get) => ({
    // Sidebar state
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    // Current file context
    currentFile: null,
    setCurrentFile: (file) => set({ currentFile: file }),

    // Current conversation
    currentConversation: null,
    setCurrentConversation: (conv) => set({ currentConversation: conv }),

    // Theme
    theme: 'dark',
    toggleTheme: () => set((state) => ({
        theme: state.theme === 'dark' ? 'light' : 'dark'
    })),

    // Loading states
    isUploading: false,
    uploadProgress: 0,
    setUploadState: (isUploading, progress = 0) => set({ isUploading, uploadProgress: progress }),

    // Modal states
    uploadModalOpen: false,
    setUploadModalOpen: (open) => set({ uploadModalOpen: open }),

    // Command palette
    commandPaletteOpen: false,
    toggleCommandPalette: () => set((state) => ({
        commandPaletteOpen: !state.commandPaletteOpen
    })),
}))
