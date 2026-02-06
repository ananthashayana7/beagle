"""
AI Service
Integration with Gemini/Claude for natural language data analysis
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.config import settings


class AIService:
    """AI service for data analysis chat"""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.default_ai_model
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response for data analysis.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Data context (columns, dtypes, etc.)
        
        Returns:
            Dictionary with response content and metadata
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Use Gemini API if available
        if self.api_key:
            return await self._generate_with_gemini(system_prompt, messages, context)
        else:
            return await self._generate_demo_response(messages, context)
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the system prompt with data context"""
        prompt = """You are Beagle, an expert data analyst assistant. You help users analyze their data through natural language conversation.

Your capabilities:
1. **Data Analysis**: Statistical analysis, trends, patterns, anomalies
2. **Visualization Suggestions**: Recommend appropriate charts for insights
3. **Code Generation**: Provide Python code using pandas, numpy, scipy, plotly
4. **Insights**: Provide actionable business insights

Guidelines:
- Be concise and professional
- Always explain your analysis in plain language
- When generating code, use clean, well-commented Python
- Suggest visualizations when they would help understand the data
- If unsure, ask clarifying questions

When you want to show a visualization, include a JSON block like this:
```chart
{"type": "bar", "x": "column_name", "y": "value_column", "title": "Chart Title"}
```

When providing Python code, wrap it in ```python blocks."""

        if context:
            prompt += f"""

**Current Dataset Context:**
- Filename: {context.get('filename', 'Unknown')}
- Rows: {context.get('row_count', 'Unknown')}
- Columns: {context.get('column_count', 'Unknown')}
- Column names: {', '.join(context.get('columns', [])[:20])}
- Data types: {json.dumps(context.get('dtypes', {}), indent=2)[:500]}"""

        return prompt
    
    async def _generate_with_gemini(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response using Google Gemini API"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        # Build conversation history
        history = []
        for msg in messages[:-1]:  # All but the last message
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Start chat
        chat = model.start_chat(history=history)
        
        # Get user's latest message
        user_message = messages[-1]["content"]
        
        # Generate response
        response = chat.send_message(
            f"{system_prompt}\n\nUser: {user_message}"
        )
        
        # Extract content
        content = response.text
        
        # Parse for code and charts
        has_code = bool(re.search(r'```python', content))
        has_visualization = bool(re.search(r'```chart', content))
        
        # Extract chart configs
        chart_configs = []
        for match in re.finditer(r'```chart\n(.*?)\n```', content, re.DOTALL):
            try:
                chart_config = json.loads(match.group(1))
                chart_configs.append(chart_config)
            except json.JSONDecodeError:
                pass
        
        return {
            "content": content,
            "has_code": has_code,
            "has_visualization": has_visualization,
            "metadata": {
                "model": self.model,
                "chart_configs": chart_configs if chart_configs else None
            },
            "token_count": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
        }
    
    async def _generate_demo_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate demo response when no API key is available"""
        user_message = messages[-1]["content"].lower()
        
        # Determine response type based on keywords
        if any(word in user_message for word in ["chart", "plot", "graph", "visual"]):
            if context and context.get("columns"):
                cols = context["columns"]
                numeric_cols = [c for c, t in context.get("dtypes", {}).items() 
                              if "int" in t.lower() or "float" in t.lower()]
                
                y_col = numeric_cols[0] if numeric_cols else cols[0]
                x_col = cols[1] if len(cols) > 1 else cols[0]
                
                content = f"""Based on your data, I recommend a bar chart showing **{y_col}** by **{x_col}**.

```chart
{{"type": "bar", "x": "{x_col}", "y": "{y_col}", "title": "{y_col} by {x_col}"}}
```

This visualization will help you see the distribution and comparison of values across categories."""
            else:
                content = "I'd be happy to create a visualization! Please upload a data file first so I can analyze the columns."
        
        elif any(word in user_message for word in ["summary", "describe", "overview"]):
            if context:
                content = f"""## Data Summary

**Dataset:** {context.get('filename', 'Your data')}
- **Rows:** {context.get('row_count', 'N/A'):,}
- **Columns:** {context.get('column_count', 'N/A')}

**Column Types:**
{self._format_dtypes(context.get('dtypes', {}))}

Would you like me to:
1. Generate statistical summary for numeric columns?
2. Show value distributions for categorical columns?
3. Create visualizations to explore the data?"""
            else:
                content = "Please upload a data file first and I'll provide a comprehensive summary."
        
        elif any(word in user_message for word in ["code", "python", "script"]):
            if context:
                content = f"""Here's Python code to analyze your data:

```python
import pandas as pd
import numpy as np

# Load your data
df = pd.read_csv('{context.get('filename', 'your_data.csv')}')

# Basic information
print(f"Shape: {{df.shape}}")
print(f"\\nColumn types:\\n{{df.dtypes}}")

# Statistical summary
print(f"\\nStatistical Summary:\\n{{df.describe()}}")

# Missing values
print(f"\\nMissing values:\\n{{df.isnull().sum()}}")

# Correlation matrix (numeric columns only)
numeric_df = df.select_dtypes(include=[np.number])
if len(numeric_df.columns) > 1:
    print(f"\\nCorrelation Matrix:\\n{{numeric_df.corr()}}")
```

You can run this code in the execution panel or copy it to your local environment."""
            else:
                content = "Upload a data file and I'll generate customized Python code for analysis."
        
        elif any(word in user_message for word in ["statistic", "average", "mean", "median", "correlation"]):
            if context:
                content = f"""## Statistical Analysis

For the dataset **{context.get('filename', 'your data')}**:

**Numeric columns** can be analyzed for:
- Mean, median, standard deviation
- Quartiles (25%, 50%, 75%)
- Min/max values
- Correlation with other numeric variables

**Categorical columns** can be analyzed for:
- Value frequencies
- Mode (most common value)
- Unique value counts

Which specific statistics would you like me to calculate?"""
            else:
                content = "Please upload a data file to perform statistical analysis."
        
        else:
            if context:
                content = f"""I'm ready to help analyze your **{context.get('filename', 'data')}** ({context.get('row_count', 'N/A'):,} rows, {context.get('column_count', 'N/A')} columns).

You can ask me to:
- 📊 **Create visualizations** - "Create a bar chart of sales by region"
- 📈 **Analyze trends** - "What are the key trends in this data?"
- 🔢 **Calculate statistics** - "What's the average value of column X?"
- 🐍 **Generate code** - "Write Python code to clean this data"
- 💡 **Get insights** - "What are the main patterns in this dataset?"

What would you like to explore?"""
            else:
                content = """Welcome to **Beagle** 🐕! I'm your AI data analysis assistant.

To get started:
1. **Upload a file** (CSV, Excel, or JSON)
2. **Ask questions** about your data
3. **Get insights**, visualizations, and Python code

What data would you like to analyze today?"""
        
        has_code = "```python" in content
        has_visualization = "```chart" in content
        
        return {
            "content": content,
            "has_code": has_code,
            "has_visualization": has_visualization,
            "metadata": {
                "model": "demo",
                "chart_configs": None
            },
            "token_count": None
        }
    
    def _format_dtypes(self, dtypes: Dict[str, str]) -> str:
        """Format dtypes dictionary for display"""
        if not dtypes:
            return "No type information available"
        
        lines = []
        for col, dtype in list(dtypes.items())[:10]:
            type_label = "📊 Numeric" if "int" in dtype or "float" in dtype else "📝 Text"
            lines.append(f"  - **{col}**: {type_label}")
        
        if len(dtypes) > 10:
            lines.append(f"  - ... and {len(dtypes) - 10} more columns")
        
        return "\n".join(lines)
