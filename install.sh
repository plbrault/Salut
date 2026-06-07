#!/bin/bash
set -euo pipefail

SERVICE_NAME="salut"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/$SERVICE_NAME.service"

PORT=8000
PORT_SET=""

usage() {
    cat <<EOF
Usage: ./install.sh [OPTIONS]

Install Salut as a systemd user service.

Options:
  --port PORT       Server port (default: 8000)
  --help            Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            PORT="$2"
            PORT_SET="1"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

SALUT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "${PORT_SET:-}" ]; then
    read -rp "What port do you want Salut to use? (default 8000): " input_port
    PORT="${input_port:-8000}"
fi

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Please install Python 3.11+."
    exit 1
fi

if ! command -v pipenv &>/dev/null; then
    echo "Error: pipenv not found. Install it with: pip install pipenv"
    exit 1
fi

if ! command -v systemctl &>/dev/null; then
    echo "Error: systemd not detected. This script requires a Linux system with systemd."
    exit 1
fi

if [ ! -d "$SALUT_DIR/.venv" ]; then
    echo "Creating virtualenv..."
    PIPENV_VENV_IN_PROJECT=1 pipenv install
else
    echo "Using existing .venv"
fi

PYTHON_PATH="$SALUT_DIR/.venv/bin/python"

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Salut - Self-Hosted Start Page
After=network.target

[Service]
Type=simple
WorkingDirectory=$SALUT_DIR
ExecStart=$PYTHON_PATH -m src.main
Environment=PORT=$PORT
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

echo "Service file written to: $SERVICE_FILE"

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"

loginctl enable-linger "$USER"

echo ""
echo "Salut is installed and running!"
echo "  URL:    http://localhost:$PORT"
echo "  Status: systemctl --user status $SERVICE_NAME"
echo "  Logs:   journalctl --user -u $SERVICE_NAME -f"
echo "  Stop:   systemctl --user stop $SERVICE_NAME"
echo "  Restart: systemctl --user restart $SERVICE_NAME"

if [ ! -f "$SALUT_DIR/config.yml" ]; then
    echo ""
    echo "Warning: config.yml not found. To customize your page, copy the example config:"
    echo "  cp $SALUT_DIR/starter.yml $SALUT_DIR/config.yml"
    echo "Then edit config.yml and restart the service:"
    echo "  systemctl --user restart salut"
fi
