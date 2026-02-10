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
    yfinance \
    flask \
    dill

# Copy execution server
COPY execution_server.py /app/execution_server.py

# Create a non-root user for security
RUN useradd -m -u 1000 sandbox
USER sandbox

# Expose port for the execution server
EXPOSE 5000

# Default command runs the execution server
CMD ["python3", "execution_server.py"]
