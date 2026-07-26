ARG platform=amd64
FROM --platform=linux/${platform} mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
       git \
       curl \
       unzip \
       postgresql-client

# Install uv for lightning-fast Python package management
RUN pip install --no-cache-dir uv

# Install rtk so it persists permanently across container rebuilds
RUN curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh \
    && if [ -f /root/.local/bin/rtk ]; then mv /root/.local/bin/rtk /usr/local/bin/rtk; fi

# Dynamically install AWS CLI v2 based on the target platform architecture
RUN ARCH=$(case ${platform} in amd64) echo "x86_64" ;; arm64) echo "aarch64" ;; *) echo "x86_64" ;; esac) \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Clean up apt cache to keep image small
RUN apt-get clean && rm -rf /var/lib/apt/lists/*