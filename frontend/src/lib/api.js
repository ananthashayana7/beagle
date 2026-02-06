/**
 * API Client
 * Axios instance with auth interceptors
 */

import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const { accessToken } = useAuthStore.getState()

        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`
        }

        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor - handle errors & token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // Handle 401 - try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            const { refreshToken, setTokens, logout } = useAuthStore.getState()

            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken
                    })

                    const { access_token, refresh_token } = response.data
                    setTokens(access_token, refresh_token)

                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshError) {
                    logout()
                    window.location.href = '/login'
                }
            } else {
                logout()
                window.location.href = '/login'
            }
        }

        return Promise.reject(error)
    }
)

// API methods
export const authApi = {
    login: (data) => api.post('/auth/login', data),
    register: (data) => api.post('/auth/register', data),
    refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
    me: () => api.get('/auth/me'),
    updateProfile: (data) => api.put('/auth/me', data),
    changePassword: (data) => api.post('/auth/change-password', data),
    logout: () => api.post('/auth/logout'),
}

export const filesApi = {
    upload: (file, onProgress) => {
        const formData = new FormData()
        formData.append('file', file)

        return api.post('/files/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
                const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                onProgress?.(percent)
            }
        })
    },
    list: (page = 1, pageSize = 20) => api.get('/files', { params: { page, page_size: pageSize } }),
    get: (fileId) => api.get(`/files/${fileId}`),
    preview: (fileId) => api.get(`/files/${fileId}/preview`),
    statistics: (fileId) => api.get(`/files/${fileId}/statistics`),
    delete: (fileId) => api.delete(`/files/${fileId}`),
}

export const conversationsApi = {
    list: (page = 1, pageSize = 50) => api.get('/conversations', { params: { page, page_size: pageSize } }),
    create: (data) => api.post('/conversations', data),
    get: (id) => api.get(`/conversations/${id}`),
    update: (id, data) => api.put(`/conversations/${id}`, data),
    delete: (id) => api.delete(`/conversations/${id}`),
    sendMessage: (id, content, metadata = null) =>
        api.post(`/conversations/${id}/messages`, { content, metadata }),
    getMessages: (id, limit = 50, offset = 0) =>
        api.get(`/conversations/${id}/messages`, { params: { limit, offset } }),
}

export const executeApi = {
    run: (code, fileId = null, conversationId = null) =>
        api.post('/execute', { code, file_id: fileId, conversation_id: conversationId }),
    get: (executionId) => api.get(`/execute/${executionId}`),
    validate: (code) => api.post('/execute/validate', { code }),
}

export const visualizeApi = {
    generate: (config) => api.post('/visualizations/generate', config),
    suggest: (fileId) => api.get(`/visualizations/suggest/${fileId}`),
    types: () => api.get('/visualizations/types'),
}

export default api
