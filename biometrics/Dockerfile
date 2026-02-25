FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for HCNetSDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create SDK directory (mount or COPY the SDK files here)
RUN mkdir -p /app/sdk

# Expose ports
# 9500 = Bridge REST API
# 7660 = ISUP listener (device connections)
EXPOSE 9500 7660

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9500"]
