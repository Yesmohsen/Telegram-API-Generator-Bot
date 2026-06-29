FROM python:3.12-slim

WORKDIR /app

# Install system dependencies: wireguard-tools for wg-quick, curl for downloading wgcf
RUN apt-get update && apt-get install -y --no-install-recommends \
    wireguard-tools \
    openresolv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download wgcf CLI for automatic WARP registration and config generation
RUN curl -sL "https://github.com/ViRb3/wgcf/releases/latest/download/wgcf_2.2.22_linux_amd64" \
    -o /usr/local/bin/wgcf && \
    chmod +x /usr/local/bin/wgcf

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY config.py scraper.py bot.py main.py ./

RUN mkdir -p /app/data

ENV CONFIG_FILE=/app/data/config.json
ENV WARP_DATA_DIR=/app/data

COPY entrypoint.sh /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
