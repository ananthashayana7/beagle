/**
 * Files Page - File management and upload
 */
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, Trash2, Eye, BarChart3, Search, Grid3X3, List, FileSpreadsheet, File, Loader2, Check } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function Files() {
    const navigate = useNavigate()
    const [viewMode, setViewMode] = useState('grid')
    const [searchQuery, setSearchQuery] = useState('')
    const [uploadProgress, setUploadProgress] = useState(0)
    const [isUploading, setIsUploading] = useState(false)

    const [demoFiles] = useState([
        { file_id: '1', original_filename: 'Q4_Sales_Report.xlsx', file_type: 'xlsx', file_size: 2500000, row_count: 15420, processing_status: 'completed' },
        { file_id: '2', original_filename: 'Customer_Feedback_2024.csv', file_type: 'csv', file_size: 1200000, row_count: 8750, processing_status: 'completed' },
        { file_id: '3', original_filename: 'Inventory_Master.json', file_type: 'json', file_size: 850000, row_count: 3200, processing_status: 'completed' },
        { file_id: '4', original_filename: 'Marketing_Campaign.xlsx', file_type: 'xlsx', file_size: 3100000, row_count: 22000, processing_status: 'completed' },
        { file_id: '5', original_filename: 'Employee_Data.csv', file_type: 'csv', file_size: 450000, row_count: 1250, processing_status: 'completed' },
        { file_id: '6', original_filename: 'Transaction_Log.csv', file_type: 'csv', file_size: 8900000, row_count: 125000, processing_status: 'completed' },
    ])

    const onDrop = useCallback(async (files) => {
        if (files.length === 0) return
        setIsUploading(true)
        setUploadProgress(0)
        const interval = setInterval(() => setUploadProgress(p => p >= 100 ? (clearInterval(interval), 100) : p + 10), 200)
        setTimeout(() => { setIsUploading(false); toast.success('File uploaded!') }, 2200)
    }, [])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'text/csv': ['.csv'], 'application/json': ['.json'] }, maxSize: 500 * 1024 * 1024 })

    const getIcon = (t) => t === 'xlsx' ? <FileSpreadsheet className="w-6 h-6 text-emerald-400" /> : t === 'csv' ? <FileText className="w-6 h-6 text-blue-400" /> : <File className="w-6 h-6 text-amber-400" />
    const formatSize = (b) => b < 1024 * 1024 ? (b / 1024).toFixed(1) + ' KB' : (b / 1024 / 1024).toFixed(1) + ' MB'
    const filtered = demoFiles.filter(f => f.original_filename.toLowerCase().includes(searchQuery.toLowerCase()))

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                <h1 className="text-2xl font-bold text-white">Files</h1>

                <div {...getRootProps()} className={clsx('border-2 border-dashed rounded-xl p-8 text-center cursor-pointer', isDragActive ? 'border-primary-500 bg-primary-500/10' : 'border-dark-600 hover:border-primary-500/50')}>
                    <input {...getInputProps()} />
                    {isUploading ? (
                        <div className="space-y-4"><Loader2 className="w-12 h-12 text-primary-500 mx-auto animate-spin" /><div className="w-48 mx-auto h-2 bg-dark-700 rounded-full"><div className="h-full bg-primary-500" style={{ width: `${uploadProgress}%` }} /></div></div>
                    ) : (
                        <><div className="w-16 h-16 rounded-2xl bg-primary-500/20 flex items-center justify-center mx-auto mb-4"><Upload className="w-8 h-8 text-primary-400" /></div><p className="text-white font-medium">Drag & drop files here</p><p className="text-dark-400 text-sm">CSV, Excel, JSON up to 500MB</p></>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-md"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" /><input type="text" placeholder="Search..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white" /></div>
                    <div className="flex bg-dark-800 rounded-lg p-1 border border-dark-600">
                        <button onClick={() => setViewMode('grid')} className={clsx('p-2 rounded', viewMode === 'grid' ? 'bg-dark-700 text-white' : 'text-dark-400')}><Grid3X3 className="w-4 h-4" /></button>
                        <button onClick={() => setViewMode('list')} className={clsx('p-2 rounded', viewMode === 'list' ? 'bg-dark-700 text-white' : 'text-dark-400')}><List className="w-4 h-4" /></button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filtered.map(file => (
                        <div key={file.file_id} className="card-hover p-5 cursor-pointer" onClick={() => navigate('/workspace')}>
                            <div className="w-12 h-12 rounded-xl bg-dark-700 flex items-center justify-center mb-4">{getIcon(file.file_type)}</div>
                            <h3 className="text-white font-medium truncate mb-1">{file.original_filename}</h3>
                            <p className="text-dark-400 text-sm mb-4">{formatSize(file.file_size)} • {file.file_type.toUpperCase()}</p>
                            <div className="flex items-center justify-between text-sm"><span className="text-dark-400">{file.row_count?.toLocaleString()} rows</span><span className="badge-success"><Check className="w-3 h-3 mr-1" />Ready</span></div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
