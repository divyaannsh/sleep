FROM python:3.10-slim

USER root

# Install system dependencies needed for OpenCV and Node.js
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set up user permissions (Hugging Face Spaces runs as UID 1000 for security)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy dependency specifications and install them
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application files
COPY . .

# Build React frontend
WORKDIR $HOME/app/frontend
RUN npm install
RUN npm run build

# Reset workdir to app root
WORKDIR $HOME/app

# Set appropriate permissions for user 1000
RUN chown -R 1000:1000 $HOME/app

USER user

# Expose port 7860 (Hugging Face default routing port)
EXPOSE 7860

# Run FastAPI app with src as the application directory
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "7860"]
