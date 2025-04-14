# Base image
FROM python:3.10-slim

# Install OS packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip zip procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy script
COPY script.py .

# Install Python dependencies
RUN pip install psutil

# Default command
ENTRYPOINT ["python", "script.py"]
CMD []
