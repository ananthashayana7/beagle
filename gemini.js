/**
 * Beagle - Gemini AI Integration Module
 * Handles communication with Google Gemini API for data analysis
 */

const BeagleAI = {
    apiKey: null,
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
    demoMode: false,

    /**
     * Initialize with API key
     */
    init(apiKey) {
        if (apiKey && apiKey.startsWith('AIza')) {
            this.apiKey = apiKey;
            this.demoMode = false;
            localStorage.setItem('beagle_api_key', apiKey);
            return true;
        }
        return false;
    },

    /**
     * Load saved API key
     */
    loadSavedKey() {
        const savedKey = localStorage.getItem('beagle_api_key');
        if (savedKey) {
            this.apiKey = savedKey;
            this.demoMode = false;
            return true;
        }
        return false;
    },

    /**
     * Enable demo mode (no API key)
     */
    enableDemoMode() {
        this.demoMode = true;
        this.apiKey = null;
    },

    /**
     * Build context from data for the AI
     */
    buildDataContext(data, columns, summary) {
        let context = `You are Beagle, an intelligent data analysis assistant. You help users understand their data through natural conversation.

CURRENT DATASET:
- Total Rows: ${data.length}
- Columns: ${columns.join(', ')}

COLUMN DETAILS:
`;
        summary.columns.forEach(col => {
            context += `\n${col.name} (${col.type}):`;
            if (col.stats) {
                context += ` min=${col.stats.min?.toFixed(2)}, max=${col.stats.max?.toFixed(2)}, mean=${col.stats.mean?.toFixed(2)}, median=${col.stats.median?.toFixed(2)}`;
            } else if (col.topValues) {
                const top3 = col.topValues.slice(0, 3).map(v => v.value).join(', ');
                context += ` top values: ${top3}`;
            }
            context += ` (${col.missing} missing, ${col.unique} unique)`;
        });

        if (summary.correlations.length > 0) {
            context += '\n\nNOTABLE CORRELATIONS:';
            summary.correlations.forEach(c => {
                context += `\n- ${c.col1} ↔ ${c.col2}: ${c.correlation.toFixed(2)}`;
            });
        }

        context += `

SAMPLE DATA (first 5 rows):
${JSON.stringify(data.slice(0, 5), null, 2)}

INSTRUCTIONS:
1. Answer the user's question about this data clearly and concisely.
2. When appropriate, include relevant statistics.
3. If the user asks for a visualization, include a JSON specification in a code block with language "chart" that follows this format:
\`\`\`chart
{
  "type": "bar|line|pie|doughnut|scatter",
  "data": {
    "labels": ["label1", "label2"],
    "datasets": [{"label": "Series", "data": [10, 20]}]
  },
  "options": {"title": "Chart Title"}
}
\`\`\`
4. If the user asks for code, provide Python code in a code block.
5. Be conversational but professional.
6. Format responses with markdown for better readability.`;

        return context;
    },

    /**
     * Send query to Gemini API
     */
    async query(userMessage, dataContext) {
        if (this.demoMode) {
            return this.generateDemoResponse(userMessage, dataContext);
        }

        if (!this.apiKey) {
            throw new Error('No API key configured. Please add your Gemini API key.');
        }

        const url = `${this.baseUrl}?key=${this.apiKey}`;

        const requestBody = {
            contents: [{
                parts: [{
                    text: `${dataContext}\n\nUSER QUESTION: ${userMessage}`
                }]
            }],
            generationConfig: {
                temperature: 0.7,
                topK: 40,
                topP: 0.95,
                maxOutputTokens: 2048
            },
            safetySettings: [
                { category: "HARM_CATEGORY_HARASSMENT", threshold: "BLOCK_NONE" },
                { category: "HARM_CATEGORY_HATE_SPEECH", threshold: "BLOCK_NONE" },
                { category: "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold: "BLOCK_NONE" },
                { category: "HARM_CATEGORY_DANGEROUS_CONTENT", threshold: "BLOCK_NONE" }
            ]
        };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'API request failed');
            }

            const data = await response.json();

            if (data.candidates && data.candidates[0]?.content?.parts?.[0]?.text) {
                return data.candidates[0].content.parts[0].text;
            }

            throw new Error('Unexpected API response format');
        } catch (error) {
            console.error('Gemini API Error:', error);
            throw error;
        }
    },

    /**
     * Generate demo response when no API key
     */
    generateDemoResponse(userMessage, dataContext) {
        const query = userMessage.toLowerCase();

        // Parse data context to extract info
        const rowMatch = dataContext.match(/Total Rows: (\d+)/);
        const rows = rowMatch ? parseInt(rowMatch[1]) : 0;

        const colMatch = dataContext.match(/Columns: (.+?)\n/);
        const columns = colMatch ? colMatch[1].split(', ') : [];

        // Generate contextual demo responses
        if (query.includes('summary') || query.includes('overview')) {
            return this.generateSummaryResponse(rows, columns, dataContext);
        }

        if (query.includes('insight') || query.includes('interesting')) {
            return this.generateInsightsResponse(dataContext);
        }

        if (query.includes('chart') || query.includes('visual') || query.includes('graph') || query.includes('plot')) {
            return this.generateChartResponse(columns, dataContext);
        }

        if (query.includes('python') || query.includes('code')) {
            return this.generateCodeResponse(columns);
        }

        if (query.includes('top') || query.includes('highest') || query.includes('best')) {
            return this.generateTopNResponse(columns, dataContext);
        }

        // Default response
        return this.generateDefaultResponse(rows, columns);
    },

    generateSummaryResponse(rows, columns, context) {
        return `## 📊 Data Summary

Your dataset contains **${rows.toLocaleString()} records** across **${columns.length} columns**.

### Column Overview
${columns.map((c, i) => `${i + 1}. **${c}**`).join('\n')}

### Key Statistics
Based on my analysis, here are some highlights:

- The dataset appears to be well-structured with various data types
- I can see both numerical and categorical columns that could be useful for analysis
- Missing values appear minimal based on the sample

### Suggested Next Steps
1. 📈 Ask me to "visualize the main trends"
2. 💡 Request "key insights from the data"
3. 🐍 Generate "Python code to analyze this data"

What would you like to explore?`;
    },

    generateInsightsResponse(context) {
        const correlationMatch = context.match(/Notable Correlations:([\s\S]*?)(?=\n\nSAMPLE|$)/i);
        let correlationInsight = '';
        if (correlationMatch) {
            correlationInsight = '\n- **Correlation detected**: Some variables show strong relationships that could be predictive';
        }

        return `## 💡 Key Insights

Based on my analysis of your data, here are the notable findings:

### Data Quality
- ✅ Dataset loaded successfully with consistent structure
- ✅ Column types detected and validated

### Statistical Insights
- The numeric columns show varying distributions
- Some categories appear more frequently than others${correlationInsight}

### Recommendations
1. **Outlier Review**: Consider examining extreme values in numeric columns
2. **Missing Data**: Check columns with missing values for patterns
3. **Segmentation**: The categorical variables suggest natural groupings

Would you like me to dive deeper into any specific insight?`;
    },

    generateChartResponse(columns, context) {
        const numCol = columns.find(c => {
            const regex = new RegExp(`${c}\\s*\\((?:integer|float)\\)`);
            return regex.test(context);
        }) || columns[0];

        const catCol = columns.find(c => {
            const regex = new RegExp(`${c}\\s*\\((?:categorical|text)\\)`);
            return regex.test(context);
        }) || columns[0];

        return `## 📈 Visualization

Here's a chart based on your data:

\`\`\`chart
{
  "type": "bar",
  "data": {
    "labels": ["Category A", "Category B", "Category C", "Category D", "Category E"],
    "datasets": [{
      "label": "${numCol}",
      "data": [45, 32, 67, 28, 55]
    }]
  },
  "options": {
    "title": "${numCol} Distribution"
  }
}
\`\`\`

This bar chart shows the distribution across categories. Would you like me to:
- 📊 Try a different chart type (line, pie, scatter)?
- 🔄 Change the grouping or aggregation?
- ➕ Add more data series for comparison?`;
    },

    generateCodeResponse(columns) {
        const colList = columns.slice(0, 5).join("', '");
        return `## 🐍 Python Analysis Code

Here's Python code to analyze your data:

\`\`\`python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load your data
df = pd.read_csv('your_data.csv')

# Basic exploration
print(f"Dataset shape: {df.shape}")
print(f"\\nColumn types:\\n{df.dtypes}")
print(f"\\nMissing values:\\n{df.isnull().sum()}")

# Descriptive statistics
print(f"\\nDescriptive Statistics:\\n{df.describe()}")

# Correlation matrix for numeric columns
numeric_cols = df.select_dtypes(include=['number']).columns
if len(numeric_cols) > 1:
    plt.figure(figsize=(10, 8))
    sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm')
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.savefig('correlation_matrix.png', dpi=150)
    plt.show()

# Distribution plots
for col in numeric_cols[:3]:
    plt.figure(figsize=(8, 4))
    sns.histplot(df[col], kde=True)
    plt.title(f'Distribution of {col}')
    plt.tight_layout()
    plt.show()
\`\`\`

This code provides:
- Basic data exploration
- Summary statistics
- Correlation analysis
- Distribution visualizations

Need code for something more specific?`;
    },

    generateTopNResponse(columns, context) {
        return `## 🏆 Top Performers

Based on your data analysis:

| Rank | Category | Value |
|------|----------|-------|
| 1 | Item A | 1,234 |
| 2 | Item B | 1,089 |
| 3 | Item C | 987 |
| 4 | Item D | 876 |
| 5 | Item E | 765 |

### Key Observations
- **Top performer** stands out with significantly higher values
- The **top 5** account for approximately 60% of the total
- There's a gradual decline suggesting a natural distribution

Would you like me to:
- 📊 Visualize this ranking?
- 🔍 Analyze what makes the top performers different?
- 📉 Show the bottom performers for comparison?`;
    },

    generateDefaultResponse(rows, columns) {
        return `## Analysis Result

I've analyzed your dataset with **${rows.toLocaleString()} rows** and **${columns.length} columns**.

Here's what I can help you with:

1. **📊 Data Summary** - "Give me a summary of this data"
2. **💡 Insights** - "What are the key insights?"
3. **📈 Visualizations** - "Create a chart of [column]"
4. **🐍 Code Generation** - "Generate Python code for analysis"
5. **🔍 Specific Questions** - Ask about particular columns or relationships

What would you like to explore?`;
    },

    /**
     * Parse chart specification from AI response
     */
    parseChartSpec(response) {
        const chartMatch = response.match(/```chart\n([\s\S]*?)\n```/);
        if (chartMatch) {
            try {
                return JSON.parse(chartMatch[1]);
            } catch (e) {
                console.error('Failed to parse chart spec:', e);
            }
        }
        return null;
    },

    /**
     * Extract code blocks from response
     */
    parseCodeBlocks(response) {
        const codeBlocks = [];
        const regex = /```(\w+)?\n([\s\S]*?)\n```/g;
        let match;

        while ((match = regex.exec(response)) !== null) {
            if (match[1] !== 'chart') {
                codeBlocks.push({
                    language: match[1] || 'text',
                    code: match[2]
                });
            }
        }

        return codeBlocks;
    }
};

// Export for use
window.BeagleAI = BeagleAI;
