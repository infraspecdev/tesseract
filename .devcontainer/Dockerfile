# .devcontainer/Dockerfile
# Constant layer for the Shield devcontainer. Hand-written instance of the
# template at shield/skills/devcontainer/templates/Dockerfile.tmpl (which
# Story 5 will create as the source of truth).
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates iptables ipset dnsutils jq sudo \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid "$USER_GID" "$USERNAME" \
    && useradd -m -s /bin/bash --uid "$USER_UID" --gid "$USER_GID" "$USERNAME" \
    && echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/shield-firewall.sh" \
       > /etc/sudoers.d/shield-firewall \
    && chmod 0440 /etc/sudoers.d/shield-firewall

# Pin Claude Code to a concrete version. Bump deliberately.
ARG CLAUDE_CODE_VERSION=2.0.0
RUN curl -fsSL https://claude.ai/install.sh \
      | CLAUDE_VERSION="${CLAUDE_CODE_VERSION}" bash

# Install uv globally so /implement's Python steps work.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && chmod 0755 /usr/local/bin/uv

COPY shield-firewall.sh /usr/local/bin/shield-firewall.sh
RUN chmod 0755 /usr/local/bin/shield-firewall.sh

USER dev
WORKDIR /workspaces
