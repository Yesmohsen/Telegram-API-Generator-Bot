#!/bin/bash
set -e

WARP_DATA_DIR="${WARP_DATA_DIR:-/app/data}"

if [ "$WARP_ENABLED" = "true" ]; then
    echo "[WARP] Setting up Cloudflare WARP..."

    mkdir -p "$WARP_DATA_DIR"
    cd "$WARP_DATA_DIR"

    if [ ! -f wgcf-account.toml ]; then
        echo "[WARP] Registering new WARP account (generating key)..."
        wgcf register
        echo "[WARP] Registration complete"
    else
        echo "[WARP] Account already registered"
    fi

    if [ ! -f wgcf-profile.conf ]; then
        echo "[WARP] Generating WireGuard config..."
        wgcf generate
        echo "[WARP] Config generated"
    else
        echo "[WARP] Config already exists"
    fi

    if ip link show wgcf >/dev/null 2>&1; then
        echo "[WARP] Tunnel already up"
    else
        echo "[WARP] Starting WireGuard tunnel..."
        wg-quick up wgcf-profile.conf
        echo "[WARP] Tunnel is up — all traffic routed through Cloudflare WARP"
    fi
fi

echo "Starting bot..."
exec python main.py
