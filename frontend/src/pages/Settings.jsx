/**
 * Settings Page
 */
import { useState } from 'react'
import { User, Shield, Bell, Palette, Key, Save, Loader2 } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'api', label: 'API Keys', icon: Key },
]

export default function Settings() {
    const { user, updateUser } = useAuthStore()
    const [activeTab, setActiveTab] = useState('profile')
    const [saving, setSaving] = useState(false)
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        email: user?.email || '',
        department: user?.department || '',
    })

    const handleSave = async () => {
        setSaving(true)
        setTimeout(() => {
            updateUser(formData)
            toast.success('Settings saved!')
            setSaving(false)
        }, 1000)
    }

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
                <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

                <div className="flex gap-8">
                    {/* Sidebar */}
                    <div className="w-48 flex-shrink-0">
                        <nav className="space-y-1">
                            {tabs.map((tab) => (
                                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                                    className={clsx('flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-colors',
                                        activeTab === tab.id ? 'bg-primary-500/20 text-primary-400' : 'text-dark-300 hover:bg-dark-800')}>
                                    <tab.icon className="w-5 h-5" /><span>{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>

                    {/* Content */}
                    <div className="flex-1">
                        {activeTab === 'profile' && (
                            <div className="card p-6 space-y-6">
                                <h2 className="text-lg font-semibold text-white">Profile Information</h2>
                                <div className="space-y-4">
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">Full Name</label>
                                        <input type="text" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} className="input" /></div>
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">Email</label>
                                        <input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} className="input" /></div>
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">Department</label>
                                        <input type="text" value={formData.department} onChange={e => setFormData({ ...formData, department: e.target.value })} className="input" placeholder="e.g., Finance" /></div>
                                </div>
                                <button onClick={handleSave} disabled={saving} className="btn-primary">
                                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4" />Save Changes</>}
                                </button>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <div className="card p-6 space-y-6">
                                <h2 className="text-lg font-semibold text-white">Security Settings</h2>
                                <div className="space-y-4">
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">Current Password</label><input type="password" className="input" /></div>
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">New Password</label><input type="password" className="input" /></div>
                                    <div><label className="block text-sm font-medium text-dark-200 mb-2">Confirm Password</label><input type="password" className="input" /></div>
                                </div>
                                <button className="btn-primary"><Save className="w-4 h-4" />Update Password</button>
                            </div>
                        )}

                        {activeTab === 'notifications' && (
                            <div className="card p-6 space-y-6">
                                <h2 className="text-lg font-semibold text-white">Notification Preferences</h2>
                                {['Email notifications for new insights', 'Weekly summary reports', 'File processing alerts', 'Team activity updates'].map((item, i) => (
                                    <div key={i} className="flex items-center justify-between py-3 border-b border-dark-700 last:border-0">
                                        <span className="text-dark-200">{item}</span>
                                        <button className="w-12 h-6 bg-primary-600 rounded-full relative"><span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" /></button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {activeTab === 'appearance' && (
                            <div className="card p-6 space-y-6">
                                <h2 className="text-lg font-semibold text-white">Appearance</h2>
                                <div><label className="block text-sm font-medium text-dark-200 mb-3">Theme</label>
                                    <div className="flex gap-4">
                                        {['Dark', 'Light', 'System'].map(t => (
                                            <button key={t} className={clsx('px-4 py-2 rounded-lg border', t === 'Dark' ? 'border-primary-500 bg-primary-500/20 text-primary-400' : 'border-dark-600 text-dark-300')}>{t}</button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'api' && (
                            <div className="card p-6 space-y-6">
                                <h2 className="text-lg font-semibold text-white">API Keys</h2>
                                <p className="text-dark-400">Manage API keys for external integrations.</p>
                                <div className="p-4 bg-dark-900 rounded-lg border border-dark-700">
                                    <div className="flex items-center justify-between">
                                        <div><p className="text-white font-medium">Production API Key</p><code className="text-dark-400 text-sm">bgl_prod_••••••••••••••••</code></div>
                                        <button className="btn-secondary">Regenerate</button>
                                    </div>
                                </div>
                                <button className="btn-primary">Generate New Key</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
