# Use an official Python runtime as the base image
FROM python:3.9-slim

# Install system dependencies required for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxkbcommon0 \
    libxcomposite1 \ 
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libpangocairo-1.0-0 \
    libcups2 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and dependencies
RUN pip install --no-cache-dir playwright
RUN playwright install

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . .

# Command to run the script
CMD ["python", "scraper.py"]
