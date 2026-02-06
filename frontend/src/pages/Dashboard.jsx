/**
 * Dashboard Page
 * Overview with metrics and recent activity
 */

import { useQuery } from '@tanstack/react-query'
import {
    FileText,
    MessageSquare,
    BarChart3,
    TrendingUp,
    Clock,
    ArrowUpRight,
    Plus,
    Upload
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { filesApi, conversationsApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import { useAppStore } from '../stores/appStore'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function Dashboard() {
    const navigate = useNavigate()
    const { user } = useAuthStore()
    const { setUploadModalOpen } = useAppStore()

    // Queries (would connect to real API in production)
    const { data: filesData } = useQuery({
        queryKey: ['files'],
        queryFn: () => filesApi.list(1, 5),
        retry: false,
    })

    const { data: conversationsData } = useQuery({
        queryKey: ['conversations'],
        queryFn: () => conversationsApi.list(1, 5),
        retry: false,
    })

    // Stats (mock data for demo)
    const stats = [
        {
            label: 'Total Files',
            value: filesData?.data?.total ?? 12,
            change: '+3 this week',
            icon: FileText,
            color: 'text-blue-400 bg-blue-500/20'
        },
        {
            label: 'Active Conversations',
            value: conversationsData?.data?.total ?? 8,
            change: '+5 this week',
            icon: MessageSquare,
            color: 'text-purple-400 bg-purple-500/20'
        },
        {
            label: 'Visualizations',
            value: 47,
            change: '+12 this week',
            icon: BarChart3,
            color: 'text-emerald-400 bg-emerald-500/20'
        },
        {
            label: 'Insights Generated',
            value: 156,
            change: '+28 this week',
            icon: TrendingUp,
            color: 'text-amber-400 bg-amber-500/20'
        }
    ]

    // Recent files (mock for demo)
    const recentFiles = filesData?.data?.items ?? [
        { file_id: '1', original_filename: 'Q4_Sales_Report.xlsx', file_type: 'xlsx', row_count: 2500, created_at: new Date().toISOString() },
        { file_id: '2', original_filename: 'Customer_Feedback.csv', file_type: 'csv', row_count: 1200, created_at: new Date().toISOString() },
        { file_id: '3', original_filename: 'Inventory_Data.json', file_type: 'json', row_count: 850, created_at: new Date().toISOString() },
    ]

    const recentConversations = conversationsData?.data?.items ?? [
        { conversation_id: '1', title: 'Sales Analysis Q4', message_count: 12, updated_at: new Date().toISOString() },
        { conversation_id: '2', title: 'Customer Segmentation', message_count: 8, updated_at: new Date().toISOString() },
        { conversation_id: '3', title: 'Revenue Forecast', message_count: 15, updated_at: new Date().toISOString() },
    ]

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Welcome section */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">
                            Welcome back, {user?.full_name?.split(' ')[0] || 'there'}
                        </h1>
                        <p className="text-dark-400 mt-1">
                            Here's what's happening with your data today
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setUploadModalOpen(true)}
                            className="btn-secondary"
                        >
                            <Upload className="w-4 h-4" />
                            Upload File
                        </button>
                        <button
                            onClick={() => navigate('/workspace')}
                            className="btn-primary"
                        >
                            <Plus className="w-4 h-4" />
                            New Analysis
                        </button>
                    </div>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {stats.map((stat, i) => (
                        <div key={i} className="card p-6 hover:border-primary-500/30 transition-colors">
                            <div className="flex items-center justify-between mb-4">
                                <div className={clsx('p-2.5 rounded-xl', stat.color)}>
                                    <stat.icon className="w-5 h-5" />
                                </div>
                                <span className="text-emerald-400 text-sm font-medium flex items-center gap-1">
                                    <ArrowUpRight className="w-3 h-3" />
                                    {stat.change}
                                </span>
                            </div>
                            <h3 className="text-3xl font-bold text-white mb-1">{stat.value}</h3>
                            <p className="text-dark-400">{stat.label}</p>
                        </div>
                    ))}
                </div>

                {/* Two column layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Recent Files */}
                    <div className="card">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-700">
                            <h2 className="text-lg font-semibold text-white">Recent Files</h2>
                            <Link to="/files" className="text-primary-400 hover:text-primary-300 text-sm font-medium">
                                View all →
                            </Link>
                        </div>
                        <div className="divide-y divide-dark-700">
                            {recentFiles.map((file) => (
                                <div
                                    key={file.file_id}
                                    className="flex items-center gap-4 px-6 py-4 hover:bg-dark-700/30 transition-colors cursor-pointer"
                                    onClick={() => navigate('/workspace')}
                                >
                                    <div className="w-10 h-10 rounded-lg bg-dark-700 flex items-center justify-center">
                                        <FileText className="w-5 h-5 text-primary-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-white font-medium truncate">{file.original_filename}</p>
                                        <p className="text-dark-400 text-sm">
                                            {file.row_count?.toLocaleString() || '—'} rows • {file.file_type.toUpperCase()}
                                        </p>
                                    </div>
                                    <div className="text-dark-500 text-sm flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        {file.created_at ? format(new Date(file.created_at), 'MMM d') : 'Recently'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Recent Conversations */}
                    <div className="card">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-700">
                            <h2 className="text-lg font-semibold text-white">Recent Conversations</h2>
                            <Link to="/workspace" className="text-primary-400 hover:text-primary-300 text-sm font-medium">
                                View all →
                            </Link>
                        </div>
                        <div className="divide-y divide-dark-700">
                            {recentConversations.map((conv) => (
                                <div
                                    key={conv.conversation_id}
                                    className="flex items-center gap-4 px-6 py-4 hover:bg-dark-700/30 transition-colors cursor-pointer"
                                    onClick={() => navigate(`/workspace/${conv.conversation_id}`)}
                                >
                                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
                                        <MessageSquare className="w-5 h-5 text-primary-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-white font-medium truncate">{conv.title}</p>
                                        <p className="text-dark-400 text-sm">
                                            {conv.message_count} messages
                                        </p>
                                    </div>
                                    <div className="text-dark-500 text-sm">
                                        {conv.updated_at ? format(new Date(conv.updated_at), 'MMM d') : 'Recently'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Quick actions */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {[
                            {
                                title: 'Analyze Sales Data',
                                description: 'Get insights from your sales performance',
                                action: 'Start Analysis',
                                gradient: 'from-blue-600 to-cyan-600'
                            },
                            {
                                title: 'Generate Report',
                                description: 'Create executive summary from your data',
                                action: 'Create Report',
                                gradient: 'from-purple-600 to-pink-600'
                            },
                            {
                                title: 'Forecast Trends',
                                description: 'Predict future patterns with AI',
                                action: 'Run Forecast',
                                gradient: 'from-emerald-600 to-teal-600'
                            }
                        ].map((item, i) => (
                            <div
                                key={i}
                                className="relative overflow-hidden rounded-xl p-5 cursor-pointer group"
                            >
                                <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-10 group-hover:opacity-20 transition-opacity`} />
                                <div className="relative">
                                    <h3 className="text-white font-semibold mb-1">{item.title}</h3>
                                    <p className="text-dark-400 text-sm mb-3">{item.description}</p>
                                    <button className="text-primary-400 text-sm font-medium hover:text-primary-300">
                                        {item.action} →
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
