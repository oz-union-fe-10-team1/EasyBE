FROM python:3.12

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh

# Set PATH (uv는 /root/.cargo/bin/uv 등으로 설치됨)
ENV PATH="/root/.cargo/bin:${PATH}"

# Set workdir
WORKDIR /hanjan

# Install dependencies via uv
COPY requirements.txt .
RUN uv pip install -r requirements.txt

# Copy project files
COPY . .

# Default command
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
