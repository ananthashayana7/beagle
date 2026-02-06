import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import App from './App'
import './index.css'

// Query client configuration
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
})

// Hide preloader
const preloader = document.querySelector('.preloader')
if (preloader) {
    preloader.style.opacity = '0'
    setTimeout(() => preloader.remove(), 300)
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <App />
                <Toaster
                    position="top-right"
                    toastOptions={{
                        className: 'glass',
                        style: {
                            background: '#1e293b',
                            color: '#e2e8f0',
                            border: '1px solid #334155',
                        },
                        success: {
                            iconTheme: {
                                primary: '#10b981',
                                secondary: '#1e293b',
                            },
                        },
                        error: {
                            iconTheme: {
                                primary: '#ef4444',
                                secondary: '#1e293b',
                            },
                        },
                    }}
                />
            </BrowserRouter>
        </QueryClientProvider>
    </React.StrictMode>
)
