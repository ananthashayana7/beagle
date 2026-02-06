import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'

// Layouts
import MainLayout from './layouts/MainLayout'
import AuthLayout from './layouts/AuthLayout'

// Pages
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Workspace from './pages/Workspace'
import Files from './pages/Files'
import Settings from './pages/Settings'

// Protected route wrapper
function ProtectedRoute({ children }) {
    const { isAuthenticated } = useAuthStore()

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return children
}

// Public route wrapper (redirect if authenticated)
function PublicRoute({ children }) {
    const { isAuthenticated } = useAuthStore()

    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />
    }

    return children
}

export default function App() {
    return (
        <Routes>
            {/* Auth routes */}
            <Route element={<AuthLayout />}>
                <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
                <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
            </Route>

            {/* Protected routes */}
            <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/workspace" element={<Workspace />} />
                <Route path="/workspace/:conversationId" element={<Workspace />} />
                <Route path="/files" element={<Files />} />
                <Route path="/settings" element={<Settings />} />
            </Route>

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    )
}
