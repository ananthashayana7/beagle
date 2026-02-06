/**
 * Workspace Page
 * Main chat interface for data analysis
 */

import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import {
    Send,
    Plus,
    FileText,
    Loader2,
    Bot,
    User,
    Copy,
    Check,
    Play,
    BarChart3,
    Code2,
    Sparkles
} from 'lucide-react'
import { conversationsApi, filesApi } from '../lib/api'
import { useAppStore } from '../stores/appStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function Workspace() {
    const { conversationId } = useParams()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const { currentFile, setCurrentFile } = useAppStore()

    const [message, setMessage] = useState('')
    const [copiedCode, setCopiedCode] = useState(null)
    const messagesEndRef = useRef(null)

    // Demo conversation state
    const [demoMessages, setDemoMessages] = useState([])
    const [isThinking, setIsThinking] = useState(false)

    // Sample prompts
    const samplePrompts = [
        "Analyze the sales trends and identify top performing products",
        "Create a bar chart comparing revenue by region",
        "What are the key patterns in customer behavior?",
        "Generate a statistical summary of the dataset",
        "Write Python code to clean and process this data"
    ]

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [demoMessages])

    const handleSend = async () => {
        if (!message.trim()) return

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: message
        }

        setDemoMessages(prev => [...prev, userMessage])
        setMessage('')
        setIsThinking(true)

        // Simulate AI response
        setTimeout(() => {
            const aiMessage = generateDemoResponse(userMessage.content)
            setDemoMessages(prev => [...prev, aiMessage])
            setIsThinking(false)
        }, 1500)
    }

    const generateDemoResponse = (query) => {
        const lower = query.toLowerCase()
        let content = ''
        let hasCode = false
        let hasViz = false

        if (lower.includes('chart') || lower.includes('visual')) {
            hasViz = true
            content = `Based on your request, I've prepared a visualization.

## Revenue by Region Analysis

The data shows significant variation across regions:

| Region | Revenue | Growth |
|--------|---------|--------|
| North | $2.4M | +15% |
| South | $1.8M | +8% |
| East | $2.1M | +12% |
| West | $1.5M | +5% |

\`\`\`chart
{"type": "bar", "x": "Region", "y": "Revenue", "title": "Revenue by Region Q4"}
\`\`\`

**Key Insights:**
- North region leads with 28% of total revenue
- All regions showing positive growth
- West region has the highest growth potential`
        } else if (lower.includes('code') || lower.includes('python')) {
            hasCode = true
            content = `Here's Python code to analyze your data:

\`\`\`python
import pandas as pd
import numpy as np

# Load and clean data
df = pd.read_csv('your_data.csv')

# Basic statistics
print("Dataset Shape:", df.shape)
print("\\nColumn Types:")
print(df.dtypes)

# Statistical summary
print("\\nNumerical Summary:")
print(df.describe())

# Check for missing values
missing = df.isnull().sum()
print("\\nMissing Values:")
print(missing[missing > 0])

# Correlation analysis
numeric_cols = df.select_dtypes(include=[np.number])
correlation = numeric_cols.corr()
print("\\nCorrelation Matrix:")
print(correlation)
\`\`\`

This code will:
1. Load your dataset
2. Display basic info and data types
3. Generate statistical summaries
4. Identify missing values
5. Calculate correlations between numeric columns

Click **Run Code** to execute this in the sandbox.`
        } else if (lower.includes('trend') || lower.includes('pattern') || lower.includes('analyze')) {
            content = `## Data Analysis Summary

Based on my analysis of your dataset, here are the key findings:

### 📈 Trends Identified
1. **Revenue Growth**: 12% increase quarter-over-quarter
2. **Seasonal Patterns**: Peak activity in Q4 (holiday season)
3. **Customer Segments**: Enterprise accounts drive 65% of revenue

### 🔍 Key Patterns
- Product Category A shows consistent 15% monthly growth
- Customer acquisition costs have decreased by 8%
- Average order value increased from $125 to $142

### ⚠️ Areas of Concern
- Churn rate increased by 2.3% in the SMB segment
- Inventory turnover slower than industry benchmark

### 💡 Recommendations
1. Focus marketing spend on high-LTV customer segments
2. Investigate SMB churn drivers
3. Optimize inventory for slow-moving SKUs

Would you like me to dive deeper into any of these areas?`
        } else {
            content = `I'm ready to help analyze your data! Here's what I can do:

### 📊 Data Analysis
- Statistical summaries and descriptive analytics
- Trend identification and pattern recognition
- Correlation and regression analysis

### 📈 Visualizations
- Bar charts, line graphs, scatter plots
- Heatmaps and distribution plots
- Custom chart configurations

### 🐍 Python Code
- Data cleaning and transformation
- Advanced statistical analysis
- Machine learning preparation

### 💡 Insights
- Business intelligence recommendations
- Anomaly detection
- Forecasting and predictions

**To get started:**
1. Upload a data file (CSV, Excel, or JSON)
2. Ask specific questions about your data
3. Request visualizations or code

What would you like to explore?`
        }

        return {
            id: Date.now(),
            role: 'assistant',
            content,
            hasCode,
            hasViz
        }
    }

    const handleCopyCode = (code) => {
        navigator.clipboard.writeText(code)
        setCopiedCode(code)
        toast.success('Code copied!')
        setTimeout(() => setCopiedCode(null), 2000)
    }

    return (
        <div className="h-full flex">
            {/* Main chat area */}
            <div className="flex-1 flex flex-col">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto">
                    {demoMessages.length === 0 ? (
                        /* Empty state */
                        <div className="h-full flex flex-col items-center justify-center p-8">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center mb-6 shadow-glow-lg">
                                <Sparkles className="w-8 h-8 text-white" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Start a New Analysis</h2>
                            <p className="text-dark-400 text-center max-w-md mb-8">
                                Ask questions about your data, generate visualizations, or request Python code.
                                I'm here to help you uncover insights.
                            </p>

                            {/* Sample prompts */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                                {samplePrompts.map((prompt, i) => (
                                    <button
                                        key={i}
                                        onClick={() => setMessage(prompt)}
                                        className="text-left p-4 bg-dark-800 hover:bg-dark-700 border border-dark-700 hover:border-primary-500/30 rounded-xl transition-all group"
                                    >
                                        <p className="text-dark-200 group-hover:text-white transition-colors">
                                            {prompt}
                                        </p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        /* Messages list */
                        <div className="max-w-4xl mx-auto p-6 space-y-6">
                            {demoMessages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={clsx(
                                        'flex gap-4',
                                        msg.role === 'user' ? 'justify-end' : ''
                                    )}
                                >
                                    {msg.role === 'assistant' && (
                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                                            <Bot className="w-4 h-4 text-white" />
                                        </div>
                                    )}

                                    <div
                                        className={clsx(
                                            'max-w-[80%] rounded-2xl p-4',
                                            msg.role === 'user'
                                                ? 'bg-primary-600 text-white'
                                                : 'bg-dark-800 border border-dark-700'
                                        )}
                                    >
                                        {msg.role === 'user' ? (
                                            <p>{msg.content}</p>
                                        ) : (
                                            <div className="markdown text-dark-100">
                                                <ReactMarkdown
                                                    components={{
                                                        code({ node, inline, className, children, ...props }) {
                                                            const match = /language-(\w+)/.exec(className || '')
                                                            const code = String(children).replace(/\n$/, '')

                                                            if (!inline && match) {
                                                                return (
                                                                    <div className="relative group">
                                                                        <div className="absolute right-2 top-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                            <button
                                                                                onClick={() => handleCopyCode(code)}
                                                                                className="p-1.5 bg-dark-700 hover:bg-dark-600 rounded text-dark-400 hover:text-white"
                                                                            >
                                                                                {copiedCode === code ? (
                                                                                    <Check className="w-4 h-4" />
                                                                                ) : (
                                                                                    <Copy className="w-4 h-4" />
                                                                                )}
                                                                            </button>
                                                                            {match[1] === 'python' && (
                                                                                <button className="p-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-white">
                                                                                    <Play className="w-4 h-4" />
                                                                                </button>
                                                                            )}
                                                                        </div>
                                                                        <SyntaxHighlighter
                                                                            style={oneDark}
                                                                            language={match[1]}
                                                                            PreTag="div"
                                                                            className="!bg-dark-950 !rounded-lg !my-4"
                                                                            {...props}
                                                                        >
                                                                            {code}
                                                                        </SyntaxHighlighter>
                                                                    </div>
                                                                )
                                                            }
                                                            return (
                                                                <code className={className} {...props}>
                                                                    {children}
                                                                </code>
                                                            )
                                                        }
                                                    }}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>

                                    {msg.role === 'user' && (
                                        <div className="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center flex-shrink-0">
                                            <User className="w-4 h-4 text-dark-300" />
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Thinking indicator */}
                            {isThinking && (
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                                        <Bot className="w-4 h-4 text-white" />
                                    </div>
                                    <div className="bg-dark-800 border border-dark-700 rounded-2xl p-4">
                                        <div className="flex items-center gap-2 text-dark-400">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span>Analyzing...</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input area */}
                <div className="border-t border-dark-700 p-4 bg-dark-800/50 backdrop-blur-xl">
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-end gap-3">
                            <div className="flex-1 relative">
                                <textarea
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault()
                                            handleSend()
                                        }
                                    }}
                                    placeholder="Ask a question about your data..."
                                    rows={1}
                                    className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                                    style={{ minHeight: '48px', maxHeight: '200px' }}
                                />
                            </div>

                            <button
                                onClick={handleSend}
                                disabled={!message.trim() || isThinking}
                                className="btn-primary h-12 w-12 p-0"
                            >
                                {isThinking ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </button>
                        </div>

                        {/* Toolbar */}
                        <div className="flex items-center gap-2 mt-3">
                            <button className="btn-ghost py-1.5 px-3 text-xs">
                                <FileText className="w-3.5 h-3.5" />
                                Attach File
                            </button>
                            <button className="btn-ghost py-1.5 px-3 text-xs">
                                <Code2 className="w-3.5 h-3.5" />
                                Code Mode
                            </button>
                            <button className="btn-ghost py-1.5 px-3 text-xs">
                                <BarChart3 className="w-3.5 h-3.5" />
                                Visualize
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
