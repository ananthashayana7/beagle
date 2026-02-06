/**
 * Login Page - Netflix-style dark theme
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
    const navigate = useNavigate()
    const { login } = useAuthStore()

    const [formData, setFormData] = useState({ email: '', password: '' })
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [errors, setErrors] = useState({})

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
        if (errors[e.target.name]) setErrors(prev => ({ ...prev, [e.target.name]: null }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.email) return setErrors({ email: 'Email is required' })
        if (!formData.password) return setErrors({ password: 'Password is required' })

        setLoading(true)
        setTimeout(() => {
            login({ user_id: 'demo', email: formData.email, full_name: 'Demo User', role: 'analyst' }, 'demo-token', 'demo-refresh')
            toast.success('Welcome!')
            navigate('/dashboard')
        }, 800)
    }

    const handleDemoLogin = () => {
        setLoading(true)
        setTimeout(() => {
            login({ user_id: 'demo', email: 'demo@beagle.ai', full_name: 'Demo User', role: 'analyst' }, 'demo-token', 'demo-refresh')
            toast.success('Welcome to Beagle!')
            navigate('/dashboard')
        }, 500)
    }

    return (
        <div className="bg-neutral-900 p-8 rounded-lg">
            <div className="lg:hidden flex items-center gap-3 mb-8">
                <div className="w-10 h-10 bg-red-600 rounded flex items-center justify-center">
                    <span className="text-white font-bold text-xl">B</span>
                </div>
                <span className="text-2xl font-semibold text-white">Beagle</span>
            </div>

            <h2 className="text-2xl font-semibold text-white mb-2">Sign in</h2>
            <p className="text-neutral-400 mb-8">Enter your credentials to access your account</p>

            <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Email</label>
                    <input type="email" name="email" value={formData.email} onChange={handleChange}
                        className={errors.email ? 'input-error' : 'input'} placeholder="you@company.com" />
                    {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
                </div>

                <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Password</label>
                    <div className="relative">
                        <input type={showPassword ? 'text' : 'password'} name="password" value={formData.password}
                            onChange={handleChange} className={errors.password ? 'input-error pr-12' : 'input pr-12'} placeholder="••••••••" />
                        <button type="button" onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white">
                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                    </div>
                    {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
                </div>

                <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 rounded border-neutral-600 bg-neutral-800" />
                        <span className="text-sm text-neutral-400">Remember me</span>
                    </label>
                    <a href="#" className="text-sm text-neutral-400 hover:text-white">Forgot password?</a>
                </div>

                <button type="submit" disabled={loading} className="btn-primary w-full h-11">
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Sign in'}
                </button>

                <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-neutral-700" /></div>
                    <div className="relative flex justify-center"><span className="px-4 bg-neutral-900 text-neutral-500 text-sm">or</span></div>
                </div>

                <button type="button" onClick={handleDemoLogin} disabled={loading} className="btn-secondary w-full h-11">
                    Try Demo Mode
                </button>
            </form>

            <p className="text-center text-neutral-500 mt-8">
                Don't have an account? <Link to="/register" className="text-white font-medium hover:text-red-500">Sign up</Link>
            </p>
        </div>
    )
}
