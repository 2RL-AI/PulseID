#!/bin/sh
set -e

echo "[entrypoint] Starting pcscd daemon..."
pcscd --disable-polkit
sleep 2

echo "[entrypoint] Checking pcscd..."
if pcscd --hotplug 2>/dev/null; then
    echo "[entrypoint] pcscd is running."
else
    echo "[entrypoint] WARNING: pcscd hotplug check failed."
fi

echo "[entrypoint] Launching application..."
exec "$@"
