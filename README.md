# Telegram API Bot

A Telegram bot that provides **API ID** and **API Hash** from `my.telegram.org` — no manual website login needed.

## How it works

1. User sends `/start` to the bot
2. User sends their **phone number** (international format, e.g. `+989123456789`)
3. Bot requests a login code from `my.telegram.org`
4. User sends the **code** they received via SMS
5. Bot logs in, creates a new app (or finds an existing one), and returns **API ID + API Hash**

## Run Locally

```bash
python main.py
```

On first run, it asks for your **bot token** (from [@BotFather](https://t.me/BotFather)) and **admin user ID**.

### With Docker

```bash
docker compose up -d
```

Set `BOT_TOKEN` and `ADMIN_ID` as environment variables (or in a `.env` file).

## Docker Image

The Docker image is built automatically and published to **GitHub Container Registry**:

```
ghcr.io/yesmohsen/telegram-api-generator-bot:latest
```

## Known Issue: `my.telegram.org` returns ERROR

In some countries (Iran, China, etc.), `my.telegram.org` blocks API credential creation
and returns **"ERROR"**. This is an IP-based block.

### Solution: Cloudflare WARP (Docker)

The Docker setup includes automatic Cloudflare WARP configuration via `wgcf`:

```yaml
# docker-compose.yml
environment:
  - WARP_ENABLED=true    # enables the WARP tunnel
cap_add:
  - NET_ADMIN            # required for WireGuard
```

On first run, the bot will:
1. Register a free Cloudflare WARP account (generates a key)
2. Create a WireGuard config
3. Route all traffic through the WARP tunnel — bypassing the IP block

### If WARP doesn't solve it

This is a known open issue. If you know how to fix it, please contribute:

https://github.com/Yesmohsen/Telegram-API-Generator-Bot

## Project Structure

```
├── main.py          # Entry point
├── bot.py           # Telegram bot handlers
├── scraper.py       # my.telegram.org login + scraping
├── config.py        # Config management (env vars / config.json)
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/docker-build.yml
```

## Disclaimer

For educational purposes. Users are responsible for complying with Telegram's Terms of Service.
