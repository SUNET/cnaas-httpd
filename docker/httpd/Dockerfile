# Build stage
FROM debian:trixie-slim AS build

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get install -y \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/cnaas/venv
ENV PATH="/opt/cnaas/venv/bin:$PATH"

WORKDIR /opt/cnaas
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Runtime stage
FROM debian:trixie-slim AS runtime

LABEL org.opencontainers.image.vendor="SUNET"
LABEL org.opencontainers.image.source="https://github.com/SUNET/cnaas-httpd"
LABEL org.opencontainers.image.description="CNaaS HTTPd"

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/cnaas/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y \
        libpython3.13 \
        nginx \
        supervisor \
        git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=build /opt/cnaas/venv /opt/cnaas/venv
COPY docker/httpd/config/supervisord_app.conf /etc/supervisor/supervisord.conf
COPY docker/httpd/config/nginx_app.conf /etc/nginx/sites-available/nginx_app.conf
COPY docker/httpd/config/nginx.conf /etc/nginx/nginx.conf
COPY docker/httpd/cert/* /etc/nginx/conf.d/
COPY docker/httpd/http.sh /opt/cnaas/

# Remove default site
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/nginx_app.conf /etc/nginx/sites-enabled/default

# Create folders
RUN mkdir -p /opt/cnaas/www/firmware /opt/cnaas/www/templates

# Fix ownership
RUN chown -R www-data:www-data /opt/cnaas /var/lib/nginx /var/log/nginx

# Copy full source code
COPY src /opt/cnaas/venv/cnaas-httpd/src

# Expose HTTPS
EXPOSE 1443

ENTRYPOINT ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
