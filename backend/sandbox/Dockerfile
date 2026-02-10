# Beagle Sandbox Environment
FROM python:3.11

# Set working directory
WORKDIR /app

# Install data analysis libraries
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    statsmodels \
    matplotlib \
    seaborn \
    plotly \
    openpyxl \
    pyarrow \
    fastparquet \
    yfinance
    # prophet - commented out

# Create a non-root user for security
RUN useradd -m -u 1000 sandbox
USER sandbox

# Default command
CMD ["python3"]
