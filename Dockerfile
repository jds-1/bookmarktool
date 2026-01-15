# Use Alpine Linux for smaller image size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache curl

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ ./templates/
COPY bookmarks.yaml .

# Create data directory for persistent storage
RUN mkdir -p /data/icons

# Create non-root user for security
RUN useradd -m -u 1000 bookmarkuser && \
    chown -R bookmarkuser:bookmarkuser /app /data

USER bookmarkuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV BOOKMARKS_PATH=/data/bookmarks.yaml
ENV ICONS_PATH=/data/icons

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "app.py"]