# Deploying to a VPS with Docker

This gets the app running on a VPS you control, with real outbound internet
access - needed for the "Fetch from eTenders" feature to work (the sandbox
this app was originally built in blocks that, see README).

## 1. Provision a VPS

Any Ubuntu 22.04+ droplet/instance works (DigitalOcean, Hetzner, EC2, etc).
2GB RAM is plenty for this app. If you want HTTPS with a real domain (see
step 5), point that domain's A record at the VPS's IP now, before
continuing, so it has time to propagate.

## 2. Install Docker

SSH into the VPS, then:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

## 3. Get the code onto the VPS

```bash
git clone https://github.com/hugardmoolman1-glitch/Meyer-Beton-Tender-APP.git
cd Meyer-Beton-Tender-APP
git checkout claude/tender-management-automation-74jahc
```

## 4. Configure

```bash
cp .env.example .env
nano .env   # optional: fill in SMTP_* if you want RFQ emails to actually send
```

Leaving `.env` mostly blank is fine to start - the app works fully without
SMTP configured, RFQ sending just stays disabled until you add it.

## 5. Start it

**Quick start, no domain (reachable at `http://<vps-ip>/`):**

```bash
docker compose -f docker-compose.yml -f docker-compose.http.yml up -d --build
```

**With a domain and automatic HTTPS** (requires the DNS step above to have
propagated - check with `dig +short yourdomain.com`):

```bash
DOMAIN=yourdomain.com docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

Put `DOMAIN=yourdomain.com` in your `.env` file instead of prefixing the
command if you'll be running compose commands repeatedly.

Either way, open a firewall for the ports you're using:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp   # only if using the TLS variant
sudo ufw allow OpenSSH
sudo ufw enable
```

## 6. Verify

- Visit the site (`http://<vps-ip>/` or `https://yourdomain.com/`) and confirm the Tenders page loads.
- Click "Fetch from eTenders" and confirm it returns real tenders instead of a network error - that's the thing that couldn't be tested during development.
- `docker compose logs -f backend` to watch backend logs if anything looks off.

## Data persistence & backups

The SQLite database (all your tenders, line items, prices, suppliers, RFQ
drafts) lives in the `tender_data` Docker volume, mounted at `/app/data`
inside the backend container. It survives `docker compose down` and
container rebuilds - only `docker compose down -v` or manually deleting the
volume would remove it.

Back it up periodically:

```bash
docker run --rm -v meyer-beton-tender-app_tender_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/tender_data_backup_$(date +%F).tar.gz -C /data .
```

## Updating after a code change

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.http.yml up -d --build
# (swap in docker-compose.tls.yml if that's the variant you're running)
```

## Notes

- The frontend calls the backend via the same origin (`/api/...`), proxied internally by nginx to the backend container - so there's no separate public backend URL to manage or keep in sync.
- If you'd rather run without Docker at all, the plain `python`/`npm` instructions are in the main [README](README.md).
