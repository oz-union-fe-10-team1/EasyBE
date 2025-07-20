FROM python:3.12

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip (더 안정적)
RUN pip install uv

# Set workdir
WORKDIR /hanjan

# Install dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy project files
COPY . .

# Default command
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]