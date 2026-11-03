#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download pinned standalone Tailwind CLI binary (v3.4.17) if not already present
TAILWIND_VERSION="v3.4.17"
TAILWIND_BIN="./bin/tailwindcss"

mkdir -p bin
if [ ! -f "$TAILWIND_BIN" ]; then
    echo "Downloading Tailwind CSS standalone binary ($TAILWIND_VERSION)..."
    curl -sLO "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-x64"
    mv tailwindcss-linux-x64 "$TAILWIND_BIN"
    chmod +x "$TAILWIND_BIN"
fi

# 3. Compile minified production stylesheet
"$TAILWIND_BIN" -i static/css/input.css -o static/css/output.css --minify

# 4. Collect static files and apply database migrations
python manage.py collectstatic --no-input
python manage.py migrate

