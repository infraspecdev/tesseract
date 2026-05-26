#!/bin/bash
# .devcontainer/shield-firewall.sh
# Default-deny outbound + per-stack allowlist.
# Hand-written instance of the template at
# shield/skills/devcontainer/templates/shield-firewall.sh (Story 5 source).
# Named shield-firewall.sh (not init-firewall.sh) to avoid silent overwrite
# by upstream Feature ghcr.io/anthropics/devcontainer-features/claude-code
# (claude-code#32113).
set -euo pipefail

# IMPORTANT: do all network-dependent work (dig, curl) BEFORE setting
# OUTPUT DROP. If we drop first, the GitHub meta fetch below would be
# blocked by our own firewall, the script would exit on the empty
# response check, and the container would end up with OUTPUT DROP and
# no allowlist ACCEPT rules — making api.anthropic.com unreachable.

# Resolve & allowlist Anthropic + extra hosts. The ipsets are IPv4-only
# (hash:ip / hash:net default to family=inet), so we filter out any
# non-IPv4 entries — dig occasionally includes CNAME chains and the
# GitHub meta API returns IPv6 CIDRs alongside the v4 ones.
ipset create allowlist hash:ip -exist
DEFAULT_HOSTS="api.anthropic.com statsig.anthropic.com claude.ai console.anthropic.com"
HOSTS="${DEFAULT_HOSTS} ${EXTRA_HOSTS:-}"
for host in $HOSTS; do
  for ip in $(dig +short A "$host"); do
    # Skip anything that isn't a bare dotted-quad IPv4 address
    case "$ip" in
      *[!0-9.]*|"") continue ;;
    esac
    ipset add allowlist "$ip" -exist
  done
done

# GitHub meta CIDRs (filter out IPv6 — colons are the giveaway)
ipset create allowlist_cidr hash:net -exist
github_meta=$(curl -fsSL https://api.github.com/meta)
[ -n "$github_meta" ] || { echo "shield-firewall: failed to fetch api.github.com/meta" >&2; exit 1; }
echo "$github_meta" | jq -r '.git[] | select(test(":") | not)' | while read -r cidr; do
  ipset add allowlist_cidr "$cidr" -exist
done

# Now apply the firewall — default-deny + the rules we built above.
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Loopback always
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Established / related return traffic
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DNS only to the resolvers /etc/resolv.conf declares (claude-code#36907
# mitigation). Locking to a fixed IP — e.g. Docker's 127.0.0.11 — breaks
# Podman (uses 169.254.1.1 / 192.168.127.1) and other runtimes. Reading
# resolv.conf preserves the intent (no arbitrary DNS exfiltration; only
# the configured resolvers are reachable) while supporting any runtime.
RESOLVERS=$(awk '/^nameserver/ { print $2 }' /etc/resolv.conf | grep -E '^[0-9.]+$')
[ -n "$RESOLVERS" ] || { echo "shield-firewall: no IPv4 nameservers in /etc/resolv.conf" >&2; exit 1; }
for ns in $RESOLVERS; do
  iptables -A OUTPUT -p udp --dport 53 -d "$ns" -j ACCEPT
  iptables -A OUTPUT -p tcp --dport 53 -d "$ns" -j ACCEPT
done

iptables -A OUTPUT -m set --match-set allowlist      dst -j ACCEPT
iptables -A OUTPUT -m set --match-set allowlist_cidr dst -j ACCEPT
