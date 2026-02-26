FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy SDK libraries
COPY sdk/EN-HCNetSDKV6.1.9.48_build20230410_linux64/lib/*.so* /app/sdk/
COPY sdk/EN-HCNetSDKV6.1.9.48_build20230410_linux64/lib/HCNetSDKCom/ /app/sdk/HCNetSDKCom/

# Add SDK libs to library path
ENV LD_LIBRARY_PATH=/app/sdk:/app/sdk/HCNetSDKCom:$LD_LIBRARY_PATH

# Copy application code
COPY app/ /app/app/

# Expose ports: 9500=API, 7660=ISUP
EXPOSE 9500 7660

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9500"]
