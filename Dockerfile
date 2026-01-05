# Use a lightweight Python image
FROM python:3.9-slim

# Install ffmpeg (Required for yt-dlp)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
