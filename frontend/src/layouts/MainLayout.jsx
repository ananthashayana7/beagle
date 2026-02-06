/**
 * Main Layout - Netflix-style dark theme
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, FolderOpen, Settings, LogOut, Menu, X, Search, Bell, Plus } from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '../stores/authStore'

const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/workspace', icon: MessageSquare, label: 'Workspace' },
    { path: '/files', icon: FolderOpen, label: 'Files' },
    { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function MainLayout() {
    const navigate = useNavigate()
    const { user, logout } = useAuthStore()
    const [sidebarOpen, setSidebarOpen] = useState(true)

    const handleLogout = () => { logout(); navigate('/login') }

    return (
        <div className="flex h-screen bg-neutral-900">
            {/* Sidebar - Netflix dark */}
            <aside className={`flex flex-col bg-black transition-all duration-200 ${sidebarOpen ? 'w-60' : 'w-16'}`}>
                {/* Logo */}
                <div className="flex items-center gap-3 px-4 py-4 border-b border-neutral-800">
                    <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center">
                        <span className="text-white font-bold">B</span>
                    </div>
                    {sidebarOpen && <span className="font-semibold text-white">Beagle</span>}
                </div>

                {/* New Analysis */}
                <div className="p-3">
                    <button onClick={() => navigate('/workspace')}
                        className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded font-medium text-sm transition-colors ${sidebarOpen ? '' : 'px-0'}`}>
                        <Plus className="w-4 h-4" />
                        {sidebarOpen && <span>New Analysis</span>}
                    </button>
                </div>

                {/* Nav */}
                <nav className="flex-1 px-2 py-2 space-y-1">
                    {navItems.map((item) => (
                        <NavLink key={item.path} to={item.path}
                            className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded transition-colors
                ${sidebarOpen ? '' : 'justify-center'}
                ${isActive ? 'bg-neutral-800 text-white font-medium' : 'text-neutral-400 hover:bg-neutral-800/50 hover:text-white'}`}>
                            <item.icon className="w-5 h-5" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* User */}
                <div className="border-t border-neutral-800 p-3">
                    <div className={`flex items-center gap-3 p-2 ${sidebarOpen ? '' : 'justify-center'}`}>
                        <div className="w-8 h-8 rounded bg-red-600 flex items-center justify-center text-white text-sm font-medium">
                            {user?.full_name?.[0] || 'U'}
                        </div>
                        {sidebarOpen && (
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">{user?.full_name || 'User'}</p>
                                <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
                            </div>
                        )}
                    </div>
                    <button onClick={handleLogout}
                        className={`flex items-center gap-3 w-full mt-2 px-3 py-2 text-neutral-500 hover:text-red-500 hover:bg-neutral-800/50 rounded transition-colors ${sidebarOpen ? '' : 'justify-center'}`}>
                        <LogOut className="w-5 h-5" />
                        {sidebarOpen && <span>Logout</span>}
                    </button>
                </div>

                {/* Toggle */}
                <button onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="absolute left-full top-4 ml-2 p-1.5 bg-neutral-800 border border-neutral-700 rounded text-neutral-400 hover:text-white">
                    {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                </button>
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <header className="flex items-center justify-between px-6 py-3 bg-neutral-900 border-b border-neutral-800">
                    <div className="relative w-80">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                        <input type="text" placeholder="Search..."
                            className="w-full pl-9 pr-4 py-2 bg-neutral-800 border border-neutral-700 rounded text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-red-500" />
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="relative p-2 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded">
                            <Bell className="w-5 h-5" />
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-hidden">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
