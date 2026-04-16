# Linux Deployment Template

This folder contains generic Linux VM deployment templates for the current
Gaokao Agent MVP.

## Included files

- `api.production.env.example`
- `web.production.env.example`
- `systemd/gaokao-agent-api.service`
- `systemd/gaokao-agent-web.service`
- `nginx/gaokao-agent.conf`

## Suggested server layout

```text
/srv/gaokao-agent/
  apps/
  deploy/
  data/
  vendor/
```

Suggested runtime env files:

- `/etc/gaokao-agent/api.env`
- `/etc/gaokao-agent/web.env`

## Setup

### 1. Copy env examples

```bash
sudo mkdir -p /etc/gaokao-agent
sudo cp /srv/gaokao-agent/deploy/linux/api.production.env.example /etc/gaokao-agent/api.env
sudo cp /srv/gaokao-agent/deploy/linux/web.production.env.example /etc/gaokao-agent/web.env
```

Fill in:

- admin token
- database path
- relay settings
- wechat official account callback token
- wechat official account app id
- wechat official account encoding aes key
- domain-facing API URL used by the Web app

### 2. Build the Web app

```bash
cd /srv/gaokao-agent/apps/web
npm install
npm run build
```

### 3. Install systemd units

```bash
sudo cp /srv/gaokao-agent/deploy/linux/systemd/gaokao-agent-api.service /etc/systemd/system/
sudo cp /srv/gaokao-agent/deploy/linux/systemd/gaokao-agent-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gaokao-agent-api
sudo systemctl enable gaokao-agent-web
sudo systemctl start gaokao-agent-api
sudo systemctl start gaokao-agent-web
```

Useful service commands:

```bash
sudo systemctl restart gaokao-agent-api
sudo systemctl restart gaokao-agent-web
sudo systemctl status gaokao-agent-api
sudo systemctl status gaokao-agent-web
sudo journalctl -u gaokao-agent-api -n 100 --no-pager
sudo journalctl -u gaokao-agent-web -n 100 --no-pager
```

### 4. Install nginx config

```bash
sudo cp /srv/gaokao-agent/deploy/linux/nginx/gaokao-agent.conf /etc/nginx/sites-available/gaokao-agent
sudo ln -sf /etc/nginx/sites-available/gaokao-agent /etc/nginx/sites-enabled/gaokao-agent
sudo nginx -t
sudo systemctl reload nginx
```

## Smoke checks

Direct service checks:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/chat/health
curl http://127.0.0.1:3000/
```

If nginx is already wired to your domain:

```bash
curl http://your-domain.example/health
curl http://your-domain.example/api/chat/health
curl http://your-domain.example/
curl http://your-domain.example/api/chat/skills
```

The chat skill listing should include both built-in skills:

- `zhangxuefeng`
- `catalog_lookup`

Official account callback checks:

```bash
curl "http://127.0.0.1:8000/api/chat/channels/wechat/official-account?signature=<signature>&timestamp=<timestamp>&nonce=<nonce>&echostr=hello"
```

## Rollback-oriented checks

If startup fails, inspect in this order:

1. `sudo systemctl status gaokao-agent-api`
2. `sudo systemctl status gaokao-agent-web`
3. `sudo journalctl -u gaokao-agent-api -n 100 --no-pager`
4. `sudo journalctl -u gaokao-agent-web -n 100 --no-pager`
5. `sudo nginx -t`

If the Web service fails after a release:

1. confirm `npm run build` completed in the deployed tree
2. verify `NEXT_PUBLIC_GAOKAO_AGENT_API_URL`
3. restart only the Web service first

If the API fails:

1. verify `/etc/gaokao-agent/api.env`
2. verify SQLite path permissions
3. verify relay configuration and token values

## Notes

- These templates assume a generic Linux VM and are meant to be adapted, not
  copied blindly into production.
- HTTPS and certificate provisioning are intentionally left out of this phase.
