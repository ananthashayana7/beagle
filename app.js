/**
 * Beagle - Main Application
 * Core application logic, UI interactions, and data management
 */

(function () {
    'use strict';

    // Application State
    const state = {
        data: [],
        columns: [],
        fileName: '',
        summary: null,
        chatHistory: [],
        currentChartSpec: null
    };

    // DOM Elements
    const elements = {
        // States
        welcomeState: document.getElementById('welcomeState'),
        chatState: document.getElementById('chatState'),

        // Upload
        uploadZone: document.getElementById('uploadZone'),
        fileInput: document.getElementById('fileInput'),
        loadSampleBtn: document.getElementById('loadSampleBtn'),

        // Chat
        chatMessages: document.getElementById('chatMessages'),
        chatForm: document.getElementById('chatForm'),
        chatInput: document.getElementById('chatInput'),
        sendBtn: document.getElementById('sendBtn'),
        suggestions: document.getElementById('suggestions'),

        // Sidebar
        sidebar: document.getElementById('sidebar'),
        closeSidebar: document.getElementById('closeSidebar'),
        toggleDataBtn: document.getElementById('toggleDataBtn'),
        dataFileName: document.getElementById('dataFileName'),
        dataRowCount: document.getElementById('dataRowCount'),
        dataTableHead: document.getElementById('dataTableHead'),
        dataTableBody: document.getElementById('dataTableBody'),
        columnList: document.getElementById('columnList'),

        // Visualization
        vizPanel: document.getElementById('vizPanel'),
        closeVizPanel: document.getElementById('closeVizPanel'),
        chartTypeSelect: document.getElementById('chartTypeSelect'),
        downloadChartBtn: document.getElementById('downloadChartBtn'),

        // Header
        newSessionBtn: document.getElementById('newSessionBtn'),
        exportBtn: document.getElementById('exportBtn'),

        // Modal
        apiKeyModal: document.getElementById('apiKeyModal'),
        apiKeyInput: document.getElementById('apiKeyInput'),
        saveApiKeyBtn: document.getElementById('saveApiKeyBtn'),
        skipApiKeyBtn: document.getElementById('skipApiKeyBtn'),

        // Loading
        loadingOverlay: document.getElementById('loadingOverlay')
    };

    /**
     * Initialize application
     */
    function init() {
        // Initialize chart module
        BeagleCharts.init();

        // Check for saved API key
        const hasKey = BeagleAI.loadSavedKey();
        if (!hasKey) {
            showApiKeyModal();
        }

        // Setup event listeners
        setupEventListeners();

        // Register hljs languages
        if (window.hljs) {
            hljs.registerLanguage('python', window.hljsDefinePython);
            hljs.registerLanguage('r', window.hljsDefineR);
        }
    }

    /**
     * Setup all event listeners
     */
    function setupEventListeners() {
        // File Upload
        elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
        elements.fileInput.addEventListener('change', handleFileSelect);

        // Drag and drop
        elements.uploadZone.addEventListener('dragover', handleDragOver);
        elements.uploadZone.addEventListener('dragleave', handleDragLeave);
        elements.uploadZone.addEventListener('drop', handleDrop);

        // Sample data
        elements.loadSampleBtn.addEventListener('click', loadSampleData);

        // Chat
        elements.chatForm.addEventListener('submit', handleChatSubmit);
        elements.chatInput.addEventListener('input', handleInputChange);

        // Suggestions
        elements.suggestions.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                elements.chatInput.value = chip.dataset.query;
                handleInputChange();
                handleChatSubmit(new Event('submit'));
            });
        });

        // Sidebar
        elements.toggleDataBtn.addEventListener('click', toggleSidebar);
        elements.closeSidebar.addEventListener('click', () => elements.sidebar.classList.add('hidden'));

        // Visualization
        elements.closeVizPanel.addEventListener('click', () => elements.vizPanel.classList.add('hidden'));
        elements.chartTypeSelect.addEventListener('change', handleChartTypeChange);
        elements.downloadChartBtn.addEventListener('click', () => BeagleCharts.downloadChart());

        // Header
        elements.newSessionBtn.addEventListener('click', newSession);
        elements.exportBtn.addEventListener('click', exportReport);

        // API Key Modal
        elements.saveApiKeyBtn.addEventListener('click', saveApiKey);
        elements.skipApiKeyBtn.addEventListener('click', skipApiKey);
        document.querySelector('.modal-backdrop')?.addEventListener('click', skipApiKey);
    }

    /**
     * Handle file selection
     */
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) processFile(file);
    }

    /**
     * Handle drag over
     */
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.uploadZone.classList.add('dragover');
    }

    /**
     * Handle drag leave
     */
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.uploadZone.classList.remove('dragover');
    }

    /**
     * Handle file drop
     */
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.uploadZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file) processFile(file);
    }

    /**
     * Process uploaded file
     */
    async function processFile(file) {
        showLoading();
        state.fileName = file.name;

        const extension = file.name.split('.').pop().toLowerCase();

        try {
            let parsedData;

            switch (extension) {
                case 'csv':
                    parsedData = await parseCSV(file);
                    break;
                case 'xlsx':
                case 'xls':
                    parsedData = await parseExcel(file);
                    break;
                case 'json':
                    parsedData = await parseJSON(file);
                    break;
                default:
                    throw new Error('Unsupported file format');
            }

            state.data = parsedData.data;
            state.columns = parsedData.columns;

            // Generate summary
            state.summary = BeagleAnalysis.generateDataSummary(state.data, state.columns);

            // Update UI
            updateDataPreview();
            switchToChatState();

            // Add welcome message
            addMessage('assistant', generateWelcomeMessage());

        } catch (error) {
            console.error('File processing error:', error);
            addMessage('assistant', `❌ Error processing file: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    /**
     * Parse CSV file
     */
    function parseCSV(file) {
        return new Promise((resolve, reject) => {
            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                complete: (results) => {
                    if (results.errors.length > 0) {
                        console.warn('CSV parse warnings:', results.errors);
                    }
                    resolve({
                        data: results.data,
                        columns: results.meta.fields || []
                    });
                },
                error: reject
            });
        });
    }

    /**
     * Parse Excel file
     */
    function parseExcel(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const jsonData = XLSX.utils.sheet_to_json(firstSheet);
                    const columns = jsonData.length > 0 ? Object.keys(jsonData[0]) : [];
                    resolve({ data: jsonData, columns });
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Parse JSON file
     */
    function parseJSON(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    let jsonData = JSON.parse(e.target.result);

                    // Handle array of objects
                    if (!Array.isArray(jsonData)) {
                        jsonData = [jsonData];
                    }

                    const columns = jsonData.length > 0 ? Object.keys(jsonData[0]) : [];
                    resolve({ data: jsonData, columns });
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    /**
     * Load sample dataset
     */
    function loadSampleData() {
        showLoading();

        // Generate sample sales data
        const categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'];
        const regions = ['North', 'South', 'East', 'West'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        const sampleData = [];
        for (let i = 0; i < 500; i++) {
            sampleData.push({
                'Order ID': `ORD-${String(i + 1).padStart(5, '0')}`,
                'Date': `2024-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`,
                'Category': categories[Math.floor(Math.random() * categories.length)],
                'Region': regions[Math.floor(Math.random() * regions.length)],
                'Revenue': Math.round(Math.random() * 5000 + 100),
                'Quantity': Math.floor(Math.random() * 50) + 1,
                'Profit': Math.round((Math.random() * 1000 - 200) * 100) / 100,
                'Customer Type': Math.random() > 0.3 ? 'Retail' : 'Wholesale'
            });
        }

        state.fileName = 'sample_sales_data.csv';
        state.data = sampleData;
        state.columns = Object.keys(sampleData[0]);
        state.summary = BeagleAnalysis.generateDataSummary(state.data, state.columns);

        updateDataPreview();
        switchToChatState();
        addMessage('assistant', generateWelcomeMessage());

        hideLoading();
    }

    /**
     * Generate welcome message
     */
    function generateWelcomeMessage() {
        const summary = state.summary;
        const numericCols = summary.columns.filter(c => c.type === 'integer' || c.type === 'float');
        const categoricalCols = summary.columns.filter(c => c.type === 'categorical');

        let message = `## 🐕 Data Loaded Successfully!\n\n`;
        message += `I've analyzed **${state.fileName}** and here's what I found:\n\n`;

        // Stats grid
        message += `<div class="stats-grid">`;
        message += `<div class="stat-card"><div class="stat-value">${summary.totalRows.toLocaleString()}</div><div class="stat-label">Rows</div></div>`;
        message += `<div class="stat-card"><div class="stat-value">${summary.totalColumns}</div><div class="stat-label">Columns</div></div>`;
        message += `<div class="stat-card"><div class="stat-value">${numericCols.length}</div><div class="stat-label">Numeric</div></div>`;
        message += `<div class="stat-card"><div class="stat-value">${categoricalCols.length}</div><div class="stat-label">Categorical</div></div>`;
        message += `</div>\n\n`;

        // Quick insights
        if (summary.topInsights.length > 0) {
            message += `### 💡 Quick Insights\n`;
            summary.topInsights.slice(0, 3).forEach(insight => {
                const icon = insight.type === 'warning' ? '⚠️' : insight.type === 'insight' ? '💡' : 'ℹ️';
                message += `- ${icon} ${insight.message}\n`;
            });
        }

        message += `\n**What would you like to explore?** Try asking me to summarize the data, create visualizations, or find specific insights!`;

        return message;
    }

    /**
     * Update data preview in sidebar
     */
    function updateDataPreview() {
        elements.dataFileName.textContent = state.fileName;
        elements.dataRowCount.textContent = `${state.data.length.toLocaleString()} rows × ${state.columns.length} columns`;

        // Build table header
        elements.dataTableHead.innerHTML = `<tr>${state.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;

        // Build table body (first 100 rows)
        const displayRows = state.data.slice(0, 100);
        elements.dataTableBody.innerHTML = displayRows.map(row =>
            `<tr>${state.columns.map(c => `<td title="${escapeHtml(String(row[c] ?? ''))}">${escapeHtml(String(row[c] ?? ''))}</td>`).join('')}</tr>`
        ).join('');

        // Build column list
        elements.columnList.innerHTML = state.summary.columns.map(col =>
            `<li>
                <span>${escapeHtml(col.name)}</span>
                <span class="type-badge">${col.type}</span>
            </li>`
        ).join('');

        // Enable export
        elements.exportBtn.disabled = false;
    }

    /**
     * Switch to chat state
     */
    function switchToChatState() {
        elements.welcomeState.classList.add('hidden');
        elements.chatState.classList.remove('hidden');
    }

    /**
     * Toggle sidebar visibility
     */
    function toggleSidebar() {
        elements.sidebar.classList.toggle('hidden');
    }

    /**
     * Handle chat input change
     */
    function handleInputChange() {
        elements.sendBtn.disabled = elements.chatInput.value.trim() === '';
    }

    /**
     * Handle chat form submit
     */
    async function handleChatSubmit(e) {
        e.preventDefault();

        const query = elements.chatInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage('user', query);
        elements.chatInput.value = '';
        elements.sendBtn.disabled = true;

        // Hide suggestions after first message
        elements.suggestions.style.display = 'none';

        // Show typing indicator
        const typingId = addTypingIndicator();

        try {
            // Build context and query AI
            const context = BeagleAI.buildDataContext(state.data, state.columns, state.summary);
            const response = await BeagleAI.query(query, context);

            // Remove typing indicator
            removeTypingIndicator(typingId);

            // Add AI response
            addMessage('assistant', response);

            // Check for chart specification
            const chartSpec = BeagleAI.parseChartSpec(response);
            if (chartSpec) {
                state.currentChartSpec = chartSpec;
                showVisualization(chartSpec);
            }

        } catch (error) {
            removeTypingIndicator(typingId);
            addMessage('assistant', `❌ Error: ${error.message}\n\nPlease check your API key or try again.`);
        }
    }

    /**
     * Add message to chat
     */
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Parse markdown and render
        if (role === 'assistant') {
            // Remove chart blocks before rendering markdown
            const cleanContent = content.replace(/```chart[\s\S]*?```/g, '');
            contentDiv.innerHTML = renderMarkdown(cleanContent);

            // Highlight code blocks
            contentDiv.querySelectorAll('pre code').forEach(block => {
                if (window.hljs) {
                    hljs.highlightElement(block);
                }
            });

            // Add view chart button if chart exists
            if (content.includes('```chart')) {
                const chartBtn = document.createElement('button');
                chartBtn.className = 'view-chart-btn';
                chartBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18M9 21V9"/>
                    </svg>
                    View Chart
                `;
                chartBtn.addEventListener('click', () => {
                    if (state.currentChartSpec) {
                        showVisualization(state.currentChartSpec);
                    }
                });
                contentDiv.appendChild(chartBtn);
            }
        } else {
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(contentDiv);
        elements.chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

        // Save to history
        state.chatHistory.push({ role, content });

        return messageDiv;
    }

    /**
     * Add typing indicator
     */
    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.id = id;
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        elements.chatMessages.appendChild(messageDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        return id;
    }

    /**
     * Remove typing indicator
     */
    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) indicator.remove();
    }

    /**
     * Show visualization panel
     */
    function showVisualization(chartSpec) {
        elements.vizPanel.classList.remove('hidden');
        elements.chartTypeSelect.value = chartSpec.type || 'bar';
        BeagleCharts.createFromSpec(chartSpec);
    }

    /**
     * Handle chart type change
     */
    function handleChartTypeChange() {
        const newType = elements.chartTypeSelect.value;
        BeagleCharts.changeType(newType);
    }

    /**
     * Render markdown to HTML
     */
    function renderMarkdown(text) {
        if (window.marked) {
            return marked.parse(text);
        }
        // Fallback: basic conversion
        return text
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    /**
     * Escape HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show API key modal
     */
    function showApiKeyModal() {
        elements.apiKeyModal.classList.remove('hidden');
    }

    /**
     * Hide API key modal
     */
    function hideApiKeyModal() {
        elements.apiKeyModal.classList.add('hidden');
    }

    /**
     * Save API key
     */
    function saveApiKey() {
        const key = elements.apiKeyInput.value.trim();
        if (BeagleAI.init(key)) {
            hideApiKeyModal();
        } else {
            alert('Invalid API key format. It should start with "AIza"');
        }
    }

    /**
     * Skip API key (demo mode)
     */
    function skipApiKey() {
        BeagleAI.enableDemoMode();
        hideApiKeyModal();
    }

    /**
     * New session
     */
    function newSession() {
        if (state.data.length > 0) {
            if (!confirm('Start a new session? Current data will be cleared.')) {
                return;
            }
        }

        // Reset state
        state.data = [];
        state.columns = [];
        state.fileName = '';
        state.summary = null;
        state.chatHistory = [];
        state.currentChartSpec = null;

        // Reset UI
        elements.chatMessages.innerHTML = '';
        elements.sidebar.classList.add('hidden');
        elements.vizPanel.classList.add('hidden');
        elements.suggestions.style.display = 'flex';
        elements.exportBtn.disabled = true;
        elements.chatState.classList.add('hidden');
        elements.welcomeState.classList.remove('hidden');
        elements.fileInput.value = '';

        // Destroy chart
        BeagleCharts.destroy();
    }

    /**
     * Export report
     */
    function exportReport() {
        const report = generateReport();
        const blob = new Blob([report], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `beagle-report-${new Date().toISOString().split('T')[0]}.md`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Generate markdown report
     */
    function generateReport() {
        let report = `# Beagle Data Analysis Report\n\n`;
        report += `**Generated:** ${new Date().toLocaleString()}\n`;
        report += `**File:** ${state.fileName}\n\n`;

        report += `## Dataset Overview\n\n`;
        report += `- **Rows:** ${state.data.length.toLocaleString()}\n`;
        report += `- **Columns:** ${state.columns.length}\n\n`;

        report += `## Column Details\n\n`;
        report += `| Column | Type | Missing | Unique |\n`;
        report += `|--------|------|---------|--------|\n`;
        state.summary.columns.forEach(col => {
            report += `| ${col.name} | ${col.type} | ${col.missing} | ${col.unique} |\n`;
        });

        report += `\n## Insights\n\n`;
        state.summary.topInsights.forEach(insight => {
            report += `- ${insight.message}\n`;
        });

        if (state.chatHistory.length > 0) {
            report += `\n## Analysis Conversation\n\n`;
            state.chatHistory.forEach(msg => {
                const role = msg.role === 'user' ? '**You:**' : '**Beagle:**';
                report += `${role}\n\n${msg.content}\n\n---\n\n`;
            });
        }

        return report;
    }

    /**
     * Show loading overlay
     */
    function showLoading() {
        elements.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        elements.loadingOverlay.classList.add('hidden');
    }

    // CSS for typing indicator (inject dynamically)
    const typingStyles = document.createElement('style');
    typingStyles.textContent = `
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 8px 0;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--accent-primary);
            border-radius: 50%;
            animation: typing 1.4s ease-in-out infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 100% { opacity: 0.3; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1); }
        }
    `;
    document.head.appendChild(typingStyles);

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
