/**
 * Beagle - Statistical Analysis Module
 * Provides data analysis, statistics, and insights generation
 */

const BeagleAnalysis = {
    /**
     * Calculate descriptive statistics for a numeric column
     */
    getDescriptiveStats(values) {
        const nums = values.filter(v => v !== null && v !== undefined && !isNaN(v)).map(Number);
        if (nums.length === 0) return null;

        const sorted = [...nums].sort((a, b) => a - b);
        const n = nums.length;
        const sum = nums.reduce((a, b) => a + b, 0);
        const mean = sum / n;

        // Variance and Standard Deviation
        const squaredDiffs = nums.map(x => Math.pow(x - mean, 2));
        const variance = squaredDiffs.reduce((a, b) => a + b, 0) / n;
        const stdDev = Math.sqrt(variance);

        // Quartiles
        const q1Index = Math.floor(n * 0.25);
        const q2Index = Math.floor(n * 0.5);
        const q3Index = Math.floor(n * 0.75);

        return {
            count: n,
            sum: sum,
            mean: mean,
            median: sorted[q2Index],
            mode: this.getMode(nums),
            min: sorted[0],
            max: sorted[n - 1],
            range: sorted[n - 1] - sorted[0],
            variance: variance,
            stdDev: stdDev,
            q1: sorted[q1Index],
            q3: sorted[q3Index],
            iqr: sorted[q3Index] - sorted[q1Index]
        };
    },

    /**
     * Calculate mode (most frequent value)
     */
    getMode(values) {
        const frequency = {};
        let maxFreq = 0;
        let mode = null;

        values.forEach(val => {
            frequency[val] = (frequency[val] || 0) + 1;
            if (frequency[val] > maxFreq) {
                maxFreq = frequency[val];
                mode = val;
            }
        });

        return mode;
    },

    /**
     * Detect outliers using IQR method
     */
    detectOutliers(values) {
        const stats = this.getDescriptiveStats(values);
        if (!stats) return [];

        const lowerBound = stats.q1 - 1.5 * stats.iqr;
        const upperBound = stats.q3 + 1.5 * stats.iqr;

        return values
            .map((v, i) => ({ value: v, index: i }))
            .filter(item => item.value < lowerBound || item.value > upperBound);
    },

    /**
     * Calculate correlation between two numeric columns
     */
    calculateCorrelation(x, y) {
        const n = Math.min(x.length, y.length);
        if (n < 2) return null;

        const xNums = x.slice(0, n).map(Number);
        const yNums = y.slice(0, n).map(Number);

        const xMean = xNums.reduce((a, b) => a + b, 0) / n;
        const yMean = yNums.reduce((a, b) => a + b, 0) / n;

        let numerator = 0;
        let xDenom = 0;
        let yDenom = 0;

        for (let i = 0; i < n; i++) {
            const xDiff = xNums[i] - xMean;
            const yDiff = yNums[i] - yMean;
            numerator += xDiff * yDiff;
            xDenom += xDiff * xDiff;
            yDenom += yDiff * yDiff;
        }

        const denominator = Math.sqrt(xDenom * yDenom);
        return denominator === 0 ? 0 : numerator / denominator;
    },

    /**
     * Get value counts for categorical data
     */
    getValueCounts(values) {
        const counts = {};
        values.forEach(val => {
            const key = val === null || val === undefined ? '(empty)' : String(val);
            counts[key] = (counts[key] || 0) + 1;
        });

        return Object.entries(counts)
            .map(([value, count]) => ({ value, count }))
            .sort((a, b) => b.count - a.count);
    },

    /**
     * Detect column data type
     */
    detectColumnType(values) {
        const sample = values.filter(v => v !== null && v !== undefined && v !== '').slice(0, 100);
        if (sample.length === 0) return 'empty';

        // Check if numeric
        const numericCount = sample.filter(v => !isNaN(Number(v))).length;
        if (numericCount / sample.length > 0.8) {
            // Check if integer or float
            const hasDecimals = sample.some(v => String(v).includes('.'));
            return hasDecimals ? 'float' : 'integer';
        }

        // Check if date
        const dateCount = sample.filter(v => !isNaN(Date.parse(v))).length;
        if (dateCount / sample.length > 0.8) return 'date';

        // Check if boolean
        const boolValues = ['true', 'false', 'yes', 'no', '1', '0'];
        const boolCount = sample.filter(v => boolValues.includes(String(v).toLowerCase())).length;
        if (boolCount / sample.length > 0.9) return 'boolean';

        // Check cardinality for categorical vs text
        const uniqueRatio = new Set(sample).size / sample.length;
        return uniqueRatio < 0.5 ? 'categorical' : 'text';
    },

    /**
     * Generate comprehensive data summary
     */
    generateDataSummary(data, columns) {
        const summary = {
            totalRows: data.length,
            totalColumns: columns.length,
            columns: [],
            correlations: [],
            topInsights: []
        };

        // Analyze each column
        columns.forEach(col => {
            const values = data.map(row => row[col]);
            const type = this.detectColumnType(values);
            const colSummary = {
                name: col,
                type: type,
                missing: values.filter(v => v === null || v === undefined || v === '').length,
                unique: new Set(values.filter(v => v !== null && v !== undefined)).size
            };

            if (type === 'integer' || type === 'float') {
                colSummary.stats = this.getDescriptiveStats(values);
                const outliers = this.detectOutliers(values);
                colSummary.outlierCount = outliers.length;
            } else {
                colSummary.topValues = this.getValueCounts(values).slice(0, 5);
            }

            summary.columns.push(colSummary);
        });

        // Find numeric columns for correlation
        const numericCols = summary.columns.filter(c => c.type === 'integer' || c.type === 'float');

        if (numericCols.length >= 2) {
            for (let i = 0; i < Math.min(numericCols.length, 5); i++) {
                for (let j = i + 1; j < Math.min(numericCols.length, 5); j++) {
                    const col1 = numericCols[i].name;
                    const col2 = numericCols[j].name;
                    const corr = this.calculateCorrelation(
                        data.map(r => r[col1]),
                        data.map(r => r[col2])
                    );
                    if (corr !== null && Math.abs(corr) > 0.3) {
                        summary.correlations.push({ col1, col2, correlation: corr });
                    }
                }
            }
        }

        // Generate insights
        summary.topInsights = this.generateInsights(summary);

        return summary;
    },

    /**
     * Generate automatic insights from data
     */
    generateInsights(summary) {
        const insights = [];

        // Dataset size insight
        insights.push({
            type: 'info',
            message: `Dataset contains ${summary.totalRows.toLocaleString()} rows and ${summary.totalColumns} columns.`
        });

        // Missing data insight
        const colsWithMissing = summary.columns.filter(c => c.missing > 0);
        if (colsWithMissing.length > 0) {
            const worstCol = colsWithMissing.sort((a, b) => b.missing - a.missing)[0];
            const pct = ((worstCol.missing / summary.totalRows) * 100).toFixed(1);
            insights.push({
                type: 'warning',
                message: `Column "${worstCol.name}" has ${pct}% missing values.`
            });
        }

        // Outliers insight
        const colsWithOutliers = summary.columns.filter(c => c.outlierCount > 0);
        if (colsWithOutliers.length > 0) {
            const total = colsWithOutliers.reduce((sum, c) => sum + c.outlierCount, 0);
            insights.push({
                type: 'insight',
                message: `Detected ${total} potential outliers across ${colsWithOutliers.length} numeric columns.`
            });
        }

        // Strong correlations
        const strongCorrs = summary.correlations.filter(c => Math.abs(c.correlation) > 0.7);
        strongCorrs.forEach(corr => {
            const strength = corr.correlation > 0 ? 'positive' : 'negative';
            insights.push({
                type: 'insight',
                message: `Strong ${strength} correlation (${corr.correlation.toFixed(2)}) between "${corr.col1}" and "${corr.col2}".`
            });
        });

        // High cardinality categorical
        const highCardCats = summary.columns.filter(c => c.type === 'categorical' && c.unique > 50);
        highCardCats.forEach(col => {
            insights.push({
                type: 'info',
                message: `Column "${col.name}" has high cardinality (${col.unique} unique values).`
            });
        });

        return insights;
    },

    /**
     * Aggregate data by a column
     */
    aggregate(data, groupBy, aggColumn, aggFunc = 'sum') {
        const groups = {};

        data.forEach(row => {
            const key = row[groupBy];
            if (!groups[key]) {
                groups[key] = [];
            }
            const val = Number(row[aggColumn]);
            if (!isNaN(val)) {
                groups[key].push(val);
            }
        });

        return Object.entries(groups).map(([key, values]) => {
            let result;
            switch (aggFunc) {
                case 'sum':
                    result = values.reduce((a, b) => a + b, 0);
                    break;
                case 'avg':
                case 'mean':
                    result = values.reduce((a, b) => a + b, 0) / values.length;
                    break;
                case 'count':
                    result = values.length;
                    break;
                case 'min':
                    result = Math.min(...values);
                    break;
                case 'max':
                    result = Math.max(...values);
                    break;
                default:
                    result = values.reduce((a, b) => a + b, 0);
            }
            return { [groupBy]: key, [aggColumn]: result };
        }).sort((a, b) => b[aggColumn] - a[aggColumn]);
    },

    /**
     * Get top N records by a column
     */
    getTopN(data, column, n = 10, ascending = false) {
        return [...data]
            .sort((a, b) => {
                const aVal = Number(a[column]) || 0;
                const bVal = Number(b[column]) || 0;
                return ascending ? aVal - bVal : bVal - aVal;
            })
            .slice(0, n);
    },

    /**
     * Filter data based on conditions
     */
    filterData(data, conditions) {
        return data.filter(row => {
            return conditions.every(cond => {
                const value = row[cond.column];
                switch (cond.operator) {
                    case 'eq': return value == cond.value;
                    case 'neq': return value != cond.value;
                    case 'gt': return Number(value) > Number(cond.value);
                    case 'gte': return Number(value) >= Number(cond.value);
                    case 'lt': return Number(value) < Number(cond.value);
                    case 'lte': return Number(value) <= Number(cond.value);
                    case 'contains': return String(value).toLowerCase().includes(String(cond.value).toLowerCase());
                    default: return true;
                }
            });
        });
    }
};

// Export for use
window.BeagleAnalysis = BeagleAnalysis;
