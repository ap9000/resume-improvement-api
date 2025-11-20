FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Build timestamp: 2025-11-12 - Force Railway rebuild

# Install system dependencies required for PDF processing and NLP
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libharfbuzz-subset0 \
    libcairo2 \
    libjpeg-dev \
    libopenjp2-7 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy English model (using direct pip install for Docker compatibility)
RUN pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Create startup script that checks WORKER_MODE
RUN echo '#!/bin/bash\n\
if [ "$WORKER_MODE" = "true" ]; then\n\
    echo "Starting ARQ worker..."\n\
    exec arq app.worker.WorkerSettings\n\
else\n\
    echo "Starting API server..."\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
fi\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check (only for API mode, will fail gracefully for worker mode)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:${PORT:-8000}/health', timeout=5.0)" 2>/dev/null || exit 0

# Run the startup script
CMD ["/app/start.sh"]
