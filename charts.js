/**
 * Beagle - Chart Utilities Module
 * Handles chart creation, configuration, and rendering
 */

const BeagleCharts = {
    chart: null,
    canvas: null,

    // Premium color palette
    colors: {
        primary: ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'],
        extended: [
            '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
            '#f43f5e', '#f97316', '#eab308', '#84cc16', '#22c55e',
            '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1'
        ],
        gradient: (ctx, color1 = '#6366f1', color2 = '#8b5cf6') => {
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(1, color2);
            return gradient;
        }
    },

    // Default chart options for dark theme
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    color: '#94a3b8',
                    font: {
                        family: "'Inter', sans-serif",
                        size: 12
                    },
                    padding: 20,
                    usePointStyle: true
                }
            },
            tooltip: {
                backgroundColor: 'rgba(26, 26, 37, 0.95)',
                titleColor: '#f8fafc',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                titleFont: {
                    family: "'Inter', sans-serif",
                    size: 14,
                    weight: 600
                },
                bodyFont: {
                    family: "'Inter', sans-serif",
                    size: 13
                },
                displayColors: true,
                boxPadding: 4
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    color: '#64748b',
                    font: {
                        family: "'Inter', sans-serif",
                        size: 11
                    }
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    color: '#64748b',
                    font: {
                        family: "'Inter', sans-serif",
                        size: 11
                    }
                }
            }
        }
    },

    /**
     * Initialize chart canvas
     */
    init(canvasId = 'chartCanvas') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Chart canvas not found');
            return false;
        }
        return true;
    },

    /**
     * Destroy existing chart
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    },

    /**
     * Create a bar chart
     */
    createBarChart(data, options = {}) {
        this.destroy();
        const ctx = this.canvas.getContext('2d');

        const config = {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((ds, i) => ({
                    label: ds.label || `Series ${i + 1}`,
                    data: ds.data,
                    backgroundColor: ds.color || this.colors.primary[i % 5],
                    borderColor: ds.color || this.colors.primary[i % 5],
                    borderWidth: 0,
                    borderRadius: 6,
                    borderSkipped: false
                }))
            },
            options: {
                ...this.defaultOptions,
                ...options,
                plugins: {
                    ...this.defaultOptions.plugins,
                    title: options.title ? {
                        display: true,
                        text: options.title,
                        color: '#f8fafc',
                        font: { size: 16, weight: 600, family: "'Inter', sans-serif" },
                        padding: { bottom: 20 }
                    } : { display: false }
                }
            }
        };

        this.chart = new Chart(ctx, config);
        return this.chart;
    },

    /**
     * Create a line chart
     */
    createLineChart(data, options = {}) {
        this.destroy();
        const ctx = this.canvas.getContext('2d');

        const config = {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((ds, i) => ({
                    label: ds.label || `Series ${i + 1}`,
                    data: ds.data,
                    borderColor: ds.color || this.colors.primary[i % 5],
                    backgroundColor: `${ds.color || this.colors.primary[i % 5]}20`,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: ds.color || this.colors.primary[i % 5],
                    pointBorderColor: '#0a0a0f',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                }))
            },
            options: {
                ...this.defaultOptions,
                ...options,
                plugins: {
                    ...this.defaultOptions.plugins,
                    title: options.title ? {
                        display: true,
                        text: options.title,
                        color: '#f8fafc',
                        font: { size: 16, weight: 600, family: "'Inter', sans-serif" },
                        padding: { bottom: 20 }
                    } : { display: false }
                }
            }
        };

        this.chart = new Chart(ctx, config);
        return this.chart;
    },

    /**
     * Create a pie chart
     */
    createPieChart(data, options = {}) {
        this.destroy();
        const ctx = this.canvas.getContext('2d');

        const config = {
            type: 'pie',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: this.colors.extended.slice(0, data.labels.length),
                    borderColor: '#0a0a0f',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'right'
                    },
                    tooltip: this.defaultOptions.plugins.tooltip,
                    title: options.title ? {
                        display: true,
                        text: options.title,
                        color: '#f8fafc',
                        font: { size: 16, weight: 600, family: "'Inter', sans-serif" },
                        padding: { bottom: 20 }
                    } : { display: false }
                }
            }
        };

        this.chart = new Chart(ctx, config);
        return this.chart;
    },

    /**
     * Create a doughnut chart
     */
    createDoughnutChart(data, options = {}) {
        this.destroy();
        const ctx = this.canvas.getContext('2d');

        const config = {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: this.colors.extended.slice(0, data.labels.length),
                    borderColor: '#0a0a0f',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '60%',
                plugins: {
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'right'
                    },
                    tooltip: this.defaultOptions.plugins.tooltip,
                    title: options.title ? {
                        display: true,
                        text: options.title,
                        color: '#f8fafc',
                        font: { size: 16, weight: 600, family: "'Inter', sans-serif" },
                        padding: { bottom: 20 }
                    } : { display: false }
                }
            }
        };

        this.chart = new Chart(ctx, config);
        return this.chart;
    },

    /**
     * Create a scatter plot
     */
    createScatterChart(data, options = {}) {
        this.destroy();
        const ctx = this.canvas.getContext('2d');

        const config = {
            type: 'scatter',
            data: {
                datasets: data.datasets.map((ds, i) => ({
                    label: ds.label || `Series ${i + 1}`,
                    data: ds.data,
                    backgroundColor: `${ds.color || this.colors.primary[i % 5]}80`,
                    borderColor: ds.color || this.colors.primary[i % 5],
                    borderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }))
            },
            options: {
                ...this.defaultOptions,
                ...options,
                plugins: {
                    ...this.defaultOptions.plugins,
                    title: options.title ? {
                        display: true,
                        text: options.title,
                        color: '#f8fafc',
                        font: { size: 16, weight: 600, family: "'Inter', sans-serif" },
                        padding: { bottom: 20 }
                    } : { display: false }
                }
            }
        };

        this.chart = new Chart(ctx, config);
        return this.chart;
    },

    /**
     * Create chart from specification object
     */
    createFromSpec(spec) {
        const { type, data, options } = spec;

        switch (type) {
            case 'bar':
                return this.createBarChart(data, options);
            case 'line':
                return this.createLineChart(data, options);
            case 'pie':
                return this.createPieChart(data, options);
            case 'doughnut':
                return this.createDoughnutChart(data, options);
            case 'scatter':
                return this.createScatterChart(data, options);
            default:
                return this.createBarChart(data, options);
        }
    },

    /**
     * Update chart type dynamically
     */
    changeType(newType) {
        if (!this.chart) return;

        const currentData = this.chart.data;
        const currentOptions = this.chart.options;

        this.destroy();
        const ctx = this.canvas.getContext('2d');

        // Handle type-specific data transformations
        let transformedData = currentData;
        if ((newType === 'pie' || newType === 'doughnut') && currentData.datasets) {
            transformedData = {
                labels: currentData.labels,
                datasets: [{
                    data: currentData.datasets[0].data,
                    backgroundColor: this.colors.extended.slice(0, currentData.labels.length),
                    borderColor: '#0a0a0f',
                    borderWidth: 2
                }]
            };
        }

        this.chart = new Chart(ctx, {
            type: newType,
            data: transformedData,
            options: currentOptions
        });

        return this.chart;
    },

    /**
     * Download chart as image
     */
    downloadChart(filename = 'beagle-chart.png') {
        if (!this.chart) return;

        const link = document.createElement('a');
        link.download = filename;
        link.href = this.canvas.toDataURL('image/png', 1.0);
        link.click();
    },

    /**
     * Generate chart from data analysis
     */
    autoGenerateChart(data, columns, query = '') {
        // Find numeric and categorical columns
        const numericCols = columns.filter(col => {
            const type = BeagleAnalysis.detectColumnType(data.map(r => r[col]));
            return type === 'integer' || type === 'float';
        });

        const categoricalCols = columns.filter(col => {
            const type = BeagleAnalysis.detectColumnType(data.map(r => r[col]));
            return type === 'categorical' || type === 'text';
        });

        // Default: bar chart of first categorical vs first numeric
        if (categoricalCols.length > 0 && numericCols.length > 0) {
            const aggregated = BeagleAnalysis.aggregate(
                data,
                categoricalCols[0],
                numericCols[0],
                'sum'
            ).slice(0, 10);

            return {
                type: 'bar',
                data: {
                    labels: aggregated.map(r => r[categoricalCols[0]]),
                    datasets: [{
                        label: numericCols[0],
                        data: aggregated.map(r => r[numericCols[0]])
                    }]
                },
                options: {
                    title: `${numericCols[0]} by ${categoricalCols[0]}`
                }
            };
        }

        // Fallback: value counts of first column
        if (columns.length > 0) {
            const counts = BeagleAnalysis.getValueCounts(data.map(r => r[columns[0]])).slice(0, 10);
            return {
                type: 'bar',
                data: {
                    labels: counts.map(c => c.value),
                    datasets: [{
                        label: 'Count',
                        data: counts.map(c => c.count)
                    }]
                },
                options: {
                    title: `Distribution of ${columns[0]}`
                }
            };
        }

        return null;
    }
};

// Export for use
window.BeagleCharts = BeagleCharts;
