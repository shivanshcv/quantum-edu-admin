# Cloudflare Tunnel as Systemd Service on EC2

Run Cloudflare Tunnel (`cloudflared`) as a **systemd service** on your EC2 instance so it keeps running when you disconnect SSH or shut down your laptop.

---

## Prerequisites

- SSH access to EC2
- Cloudflare account (free tier works)
- Apps to expose: Django Admin (port 8000), Spring Boot (port 8080), or both

---

## Option A: Quick Tunnel (single service)

Exposes one local service via `https://xxx.trycloudflare.com`. The default service file exposes **Spring Boot BE (port 8080)**.

### 1. Install cloudflared on EC2

```bash
ssh -i ~/path/to/your-key.pem ubuntu@YOUR_EC2_IP

# Download and install
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Verify
cloudflared --version
```

### 2. Create systemd service (Spring Boot BE on 8080)

```bash
sudo tee /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel (Spring Boot BE on port 8080)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

To expose **Django Admin (8000)** instead, change the URL:

```bash
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:8000
```

### 3. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

### 4. Get the public URL

```bash
sudo journalctl -u cloudflared -n 30
```

Look for a line like: `Your quick Tunnel has been created! Visit it at: https://xxxx-xx-xx-xx-xx.trycloudflare.com`

For **Spring Boot**, add this URL to `APP_CORS_ORIGINS` in quantum-edu-be `deploy.env` if the frontend will call the API via the tunnel URL.

---

## Option B: Named Tunnel (multiple services, custom domain)

Use when you need:
- Multiple services (e.g. admin on `admin.yourdomain.com`, API on `api.yourdomain.com`)
- A stable URL or custom domain

### 1. Install cloudflared (same as Option A)

### 2. Login and create tunnel (one-time, from a machine with a browser)

**Option 2a: Login from your laptop, copy credentials to EC2**

```bash
# On your laptop (Mac/Linux)
cloudflared tunnel login
# Browser opens; select your domain; saves cert to ~/.cloudflared/cert.pem

cloudflared tunnel create quantum-edu
# Saves credentials to ~/.cloudflared/<UUID>.json and prints the Tunnel ID
```

Copy these to EC2:

```bash
scp -i ~/path/to/key.pem ~/.cloudflared/cert.pem ubuntu@EC2_IP:~/.cloudflared/
scp -i ~/path/to/key.pem ~/.cloudflared/*.json ubuntu@EC2_IP:~/.cloudflared/
```

**Option 2b: Login directly on EC2 (headless)**

```bash
# On EC2
cloudflared tunnel login
# Prints a URL - open it in your laptop browser and complete auth
# Cert is saved on EC2
cloudflared tunnel create quantum-edu
```

### 3. Create config file on EC2

```bash
mkdir -p ~/.cloudflared

# Replace TUNNEL_ID with output of: cloudflared tunnel list
cat << 'EOF' | sudo tee /etc/cloudflared/config.yml
tunnel: TUNNEL_ID
credentials-file: /home/ubuntu/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: admin.yourdomain.com
    service: http://localhost:8000
  - hostname: api.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
EOF
```

Edit `TUNNEL_ID` and hostnames. Add CNAME records in Cloudflare DNS pointing to `<TUNNEL_ID>.cfargotunnel.com`.

### 4. Create systemd service

```bash
sudo tee /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 5. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

---

## Useful Commands

| Task | Command |
|------|---------|
| View logs | `sudo journalctl -u cloudflared -f` |
| Restart | `sudo systemctl restart cloudflared` |
| Stop | `sudo systemctl stop cloudflared` |
| Disable (no start on boot) | `sudo systemctl disable cloudflared` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `cloudflared: command not found` | Check install path: `which cloudflared` or use `/usr/local/bin/cloudflared` in ExecStart |
| Tunnel stops after SSH disconnect | Ensure you used systemd (this guide), not a manual `cloudflared` process |
| 502 Bad Gateway | Verify Django/Spring Boot is running: `curl http://localhost:8000` or `curl http://localhost:8080` |
| URL changes on restart (quick tunnel) | Quick tunnels get a new URL each run. Use a named tunnel (Option B) for a stable URL |
