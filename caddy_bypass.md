# Diamond Link — Caddy Bypass & Internet Connectivity

## Overview

Diamond Link runs on **port 7777** using a raw TCP protocol with JSON messages and 4-byte length-prefix framing. Caddy (reverse proxy) must NOT intercept or proxy this port, as it would attempt to parse the raw TCP stream as HTTP, breaking the protocol entirely.

This guide explains how to ensure port 7777 remains isolated from Caddy and accessible over LAN and WAN.

---

## Key Rules

1. **Never add a reverse_proxy rule for port 7777**
   - Caddy should not touch this port
   - Raw TCP (port 7777) is handled by the kernel/firewall, not by Caddy

2. **Caddy manages ports 443 (HTTPS) and 8443 (HTTPS)**
   - All other ports are outside Caddy's scope
   - Diamond Link is a separate service

3. **Port 7777 must be:
   - Open in local firewall (ufw, iptables)
   - Open in cloud security groups
   - Not bound to any other service

---

## Caddyfile Configuration

If you're using Caddy with Layer4 plugins or complex routing, explicitly exclude port 7777:

```caddyfile
# ============================================
# Caddy HTTP/HTTPS Proxy (ports 443, 8443)
# ============================================
# Diamond Link (port 7777) is NOT managed by Caddy.
# Caddy only handles HTTP/HTTPS traffic on 443 and 8443.

# HTTPS for example.com on port 443
example.com:443 {
    reverse_proxy localhost:3000
    encode gzip
}

# Custom HTTPS on port 8443
:8443 {
    tls internal
    reverse_proxy localhost:8001
}

# ============================================
# DIAMOND LINK — Raw TCP (port 7777)
# DO NOT add a proxy or listener here.
# ============================================
# The kernel routes raw TCP on port 7777 directly
# to the Diamond Brain service.
# Caddy never sees these connections.
```

### If Using Caddy Layer4 Plugin

If you have Caddy Layer4 configured for custom TCP routing, explicitly exclude port 7777:

```caddyfile
{
    layer4 {
        :5555 {
            @not_diamond_link not tcp {port 7777}
            route @not_diamond_link {
                # Your Layer4 rules here
            }
        }
    }
}
```

---

## Firewall Configuration

### Linux — ufw

```bash
# Allow Diamond Link TCP traffic on port 7777
sudo ufw allow 7777/tcp comment "Diamond Link"

# Verify
sudo ufw status | grep 7777
```

### Linux — iptables (if not using ufw)

```bash
# Allow incoming TCP on port 7777
sudo iptables -A INPUT -p tcp --dport 7777 -j ACCEPT

# Make persistent (save to /etc/iptables/rules.v4)
sudo iptables-save > /etc/iptables/rules.v4
```

### Cloud VMs (AWS, GCP, Azure, etc.)

Add an inbound rule to your security group / firewall policy:

| Protocol | Port | Source | Purpose |
|----------|------|--------|---------|
| TCP | 7777 | 0.0.0.0/0 or your IP range | Diamond Link |

**Example (AWS Security Group):**
- Type: Custom TCP Rule
- Protocol: TCP
- Port Range: 7777
- Source: 0.0.0.0/0 (or restrict to your IP)
- Description: "Diamond Link"

---

## Testing Diamond Link

### Local LAN Test (UDP Discovery)

```python
from brain.diamond_brain import DiamondBrain

# Terminal 1: Server
brain_server = DiamondBrain()
brain_server.link_init("ServerBrain")
brain_server.link_serve(port=7777)

# Terminal 2: Client (on same LAN)
brain_client = DiamondBrain()
brain_client.link_init("ClientBrain")
result = brain_client.establish_diamond_link("passphrase")
print(result)  # → {"status": "connected", "peer_ip": "192.168.x.x", ...}
```

### WAN / Internet Test (Direct IP)

```python
from brain.diamond_brain import DiamondBrain

# Cloud VM: Server on port 7777
brain_server = DiamondBrain()
brain_server.link_init("CloudBrain")
brain_server.link_serve(port=7777)

# Local machine: Connect to cloud IP
brain_client = DiamondBrain()
brain_client.link_init("LocalBrain")
result = brain_client.establish_diamond_link(
    "passphrase",
    host="1.2.3.4",  # Cloud VM public IP
    port=7777,
    timeout=10
)
print(result)  # → {"status": "connected", "peer_ip": "1.2.3.4", ...}
```

### Verify No Caddy Interference

Test that Caddy does NOT intercept port 7777:

```bash
# Should timeout or refuse (NOT respond with HTTP)
curl -v http://localhost:7777
# Expected: Connection refused or timeout
# NOT Expected: HTTP 400 Bad Request (Caddy error)
```

---

## rathin_utils.Brain Integration

Both LAN and WAN Diamond Link are available via the high-level `Brain` API:

```python
from rathin_utils.brain import Brain

brain = Brain()

# LAN pairing (auto-discovery)
result = brain.establish_diamond_link("secret-passphrase")
print(result)

# WAN pairing (direct IP, e.g., Nextcloud server)
result = brain.establish_diamond_link(
    "secret-passphrase",
    host="cloud.example.com",
    port=7777,
    timeout=10
)
print(result)

# Check status
status = brain.diamond_link_status()
print(status)  # → {"connected": True, "peer_ip": "...", "peer_name": "..."}

# Disconnect
brain.disconnect_diamond_link()
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Connection refused` on 7777 | Firewall blocked | `sudo ufw allow 7777/tcp` |
| `Connection timeout` (WAN) | Cloud security group | Add TCP 7777 inbound rule |
| `HTTP 400 Bad Request` from 7777 | Caddy is proxying | Remove reverse_proxy rule for 7777 |
| `No peers found on LAN` | UDP broadcast blocked | Check multicast routing |
| `[ERRORED] Invalid response from peer` | Protocol mismatch | Ensure both brains run same version |

---

## Architecture Notes

### Port Assignment

- **7777**: Diamond Link (raw TCP, no Caddy)
- **443**: Caddy HTTPS (main site)
- **8443**: Caddy HTTPS (custom services)
- **8080**: Caddy HTTP (if enabled)
- **7776**: UDP broadcast discovery (optional future enhancement)

### Protocol Stack

Diamond Link (port 7777):
```
TCP (socket) ← JSON messages
↓
4-byte length prefix (big-endian)
↓
JSON payload (UTF-8)
```

Caddy (443/8443):
```
TCP (socket)
↓
TLS encryption
↓
HTTP/2 or HTTP/1.1
```

These are completely separate.

---

## Future: TLS Encryption for Diamond Link

Currently, Diamond Link uses plaintext JSON over TCP. Future enhancements may add:
- TLS wrapping (X.509 certs)
- Passphrase-based ECDHE key exchange
- AEAD cipher (AES-256-GCM)

This will not affect the Caddy bypass — port 7777 will still be outside Caddy's scope.

---

## Summary Checklist

- [ ] Port 7777 is NOT mentioned in Caddyfile
- [ ] No reverse_proxy rule binds to port 7777
- [ ] Firewall allows TCP 7777 (ufw / security group)
- [ ] Cloud VM security group includes inbound TCP 7777
- [ ] `curl http://localhost:7777` times out or refuses (not HTTP)
- [ ] Local LAN test: `establish_diamond_link()` succeeds
- [ ] WAN test: `establish_diamond_link(host="...")` succeeds
- [ ] `diamond_link_status()` returns correct peer info
