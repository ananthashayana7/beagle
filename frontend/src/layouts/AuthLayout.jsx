/**
 * Auth Layout - Netflix-style dark theme
 */
import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
    return (
        <div className="min-h-screen flex bg-neutral-900">
            {/* Left side - Dark branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-black p-12 flex-col justify-between">
                <div>
                    <div className="flex items-center gap-3 mb-16">
                        <div className="w-10 h-10 bg-red-600 rounded flex items-center justify-center">
                            <span className="text-white font-bold text-xl">B</span>
                        </div>
                        <span className="text-2xl font-semibold text-white">Beagle</span>
                    </div>

                    <h1 className="text-4xl font-semibold leading-tight mb-6 text-white">
                        Data Analysis Made Simple
                    </h1>
                    <p className="text-neutral-400 text-lg mb-12">
                        Upload your data, ask questions in plain English, and get insights instantly.
                    </p>

                    <div className="space-y-4">
                        {['Natural language queries', 'Automated visualizations', 'Secure data processing', 'Export reports'].map((item, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-red-600"></div>
                                <span className="text-neutral-300">{item}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <p className="text-neutral-600 text-sm">© 2026 Beagle Analytics</p>
            </div>

            {/* Right side - Form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-neutral-900">
                <div className="w-full max-w-md">
                    <Outlet />
                </div>
            </div>
        </div>
    )
}
