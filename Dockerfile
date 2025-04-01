# Copyright (c) 2025 Shiva Hanumanthaiah
# All rights reserved.
# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for OpenCV headless)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libx11-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements (or install directly)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose Flask's default port
EXPOSE 5000

# Set environment variables to disable multi-threaded decoding
# OpenCV configuration for single-threaded decoding
ENV OPENCV_NUM_THREADS=1
ENV FFMPEG_THREADS=1

# Run the Flask app
CMD ["python", "app.py"]

