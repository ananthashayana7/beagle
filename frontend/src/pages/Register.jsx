/**
 * Register Page
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2, Dog, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../stores/authStore'
import { authApi } from '../lib/api'
import clsx from 'clsx'

export default function Register() {
    const navigate = useNavigate()
    const { login } = useAuthStore()

    const [formData, setFormData] = useState({
        email: '',
        full_name: '',
        department: '',
        password: '',
        confirmPassword: ''
    })
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [errors, setErrors] = useState({})

    // Password requirements
    const passwordRequirements = [
        { label: 'At least 8 characters', test: (p) => p.length >= 8 },
        { label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
        { label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
        { label: 'One number', test: (p) => /\d/.test(p) },
    ]

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: null }))
        }
    }

    const validate = () => {
        const newErrors = {}

        if (!formData.email) newErrors.email = 'Email is required'
        else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Invalid email format'

        if (!formData.full_name) newErrors.full_name = 'Full name is required'

        if (!formData.password) newErrors.password = 'Password is required'
        else {
            const failed = passwordRequirements.filter(req => !req.test(formData.password))
            if (failed.length > 0) newErrors.password = 'Password does not meet requirements'
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!validate()) return

        setLoading(true)
        try {
            // Register
            await authApi.register({
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                department: formData.department || null
            })

            // Auto-login
            const loginResponse = await authApi.login({
                email: formData.email,
                password: formData.password
            })
            const { access_token, refresh_token } = loginResponse.data

            const userResponse = await authApi.me()
            login(userResponse.data, access_token, refresh_token)

            toast.success('Account created successfully!')
            navigate('/dashboard')
        } catch (error) {
            const message = error.response?.data?.detail || 'Registration failed'
            toast.error(message)
            if (error.response?.status === 409) {
                setErrors({ email: 'Email already registered' })
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="animate-in">
            {/* Mobile logo */}
            <div className="flex items-center gap-3 mb-8 lg:hidden">
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 shadow-glow">
                    <Dog className="w-7 h-7 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold gradient-text">Beagle</h1>
                    <p className="text-sm text-dark-400">Data Intelligence</p>
                </div>
            </div>

            {/* Header */}
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-white">Create an account</h2>
                <p className="text-dark-400 mt-1">Get started with Beagle today</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-dark-200 mb-2">
                        Full name
                    </label>
                    <input
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleChange}
                        className={errors.full_name ? 'input-error' : 'input'}
                        placeholder="Enter your full name"
                    />
                    {errors.full_name && (
                        <p className="text-red-400 text-sm mt-1">{errors.full_name}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-dark-200 mb-2">
                        Email address
                    </label>
                    <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className={errors.email ? 'input-error' : 'input'}
                        placeholder="Enter your email"
                    />
                    {errors.email && (
                        <p className="text-red-400 text-sm mt-1">{errors.email}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-dark-200 mb-2">
                        Department <span className="text-dark-500">(optional)</span>
                    </label>
                    <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={handleChange}
                        className="input"
                        placeholder="e.g., Finance, Marketing"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-dark-200 mb-2">
                        Password
                    </label>
                    <div className="relative">
                        <input
                            type={showPassword ? 'text' : 'password'}
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className={errors.password ? 'input-error pr-12' : 'input pr-12'}
                            placeholder="Create a password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                        >
                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                    </div>

                    {/* Password requirements */}
                    {formData.password && (
                        <div className="mt-3 space-y-2">
                            {passwordRequirements.map((req, i) => {
                                const passed = req.test(formData.password)
                                return (
                                    <div key={i} className="flex items-center gap-2 text-sm">
                                        {passed ? (
                                            <Check className="w-4 h-4 text-emerald-400" />
                                        ) : (
                                            <X className="w-4 h-4 text-dark-500" />
                                        )}
                                        <span className={passed ? 'text-emerald-400' : 'text-dark-400'}>
                                            {req.label}
                                        </span>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-dark-200 mb-2">
                        Confirm password
                    </label>
                    <input
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        className={errors.confirmPassword ? 'input-error' : 'input'}
                        placeholder="Confirm your password"
                    />
                    {errors.confirmPassword && (
                        <p className="text-red-400 text-sm mt-1">{errors.confirmPassword}</p>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full h-12 mt-6"
                >
                    {loading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        'Create account'
                    )}
                </button>
            </form>

            {/* Terms */}
            <p className="text-center text-dark-500 text-sm mt-6">
                By signing up, you agree to our{' '}
                <a href="#" className="text-primary-400 hover:underline">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-primary-400 hover:underline">Privacy Policy</a>
            </p>

            {/* Login link */}
            <p className="text-center text-dark-400 mt-6">
                Already have an account?{' '}
                <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">
                    Sign in
                </Link>
            </p>
        </div>
    )
}
