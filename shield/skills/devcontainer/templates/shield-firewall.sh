#!/bin/bash
# .devcontainer/shield-firewall.sh
# Default-deny outbound + per-stack allowlist.
# Hand-written instance of the template at
# shield/skills/devcontainer/templates/shield-firewall.sh (Story 5 source).
# Named shield-firewall.sh (not init-firewall.sh) to avoid silent overwrite
# by upstream Feature ghcr.io/anthropics/devcontainer-features/claude-code
# (claude-code#32113).
set -euo pipefail

# Default-deny
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Loopback always
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Established / related return traffic
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DNS only to Docker's embedded resolver (claude-code#36907 mitigation)
iptables -A OUTPUT -p udp --dport 53 -d 127.0.0.11 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -d 127.0.0.11 -j ACCEPT

# Resolve & allowlist Anthropic + extra hosts
ipset create allowlist hash:ip -exist
DEFAULT_HOSTS="api.anthropic.com statsig.anthropic.com claude.ai console.anthropic.com"
HOSTS="${DEFAULT_HOSTS} ${EXTRA_HOSTS:-}"
for host in $HOSTS; do
  for ip in $(dig +short A "$host"); do
    ipset add allowlist "$ip" -exist
  done
done

# GitHub meta CIDRs
ipset create allowlist_cidr hash:net -exist
github_meta=$(curl -fsSL https://api.github.com/meta)
[ -n "$github_meta" ] || { echo "shield-firewall: failed to fetch api.github.com/meta" >&2; exit 1; }
echo "$github_meta" | jq -r '.git[]' | while read -r cidr; do
  ipset add allowlist_cidr "$cidr" -exist
done

iptables -A OUTPUT -m set --match-set allowlist      dst -j ACCEPT
iptables -A OUTPUT -m set --match-set allowlist_cidr dst -j ACCEPT
