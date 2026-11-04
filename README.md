# Nivetha Packers and Movers — Web Platform

Small business website and lead-capture platform for Nivetha Packers and Movers (Tiruppur, Tamil Nadu).

## Tech Stack

- **Backend:** Python 3.12+ / Django 5.2
- **Styling:** Tailwind CSS v3.4.17 (via standalone CLI binary; no Node.js/npm required)
- **Database:** SQLite (local development) / PostgreSQL on Neon (production)
- **Static & Media:** WhiteNoise (`CompressedManifestStaticFilesStorage`) + Cloudinary (production) / local disk (development) via Django 5.2 `STORAGES`
- **WSGI Server:** Gunicorn
- **Deployment:** Render (Web Service)

---

## Local Development Setup

### 1. Prerequisites
- Python 3.12+ installed
- Git

### 2. Clone and Setup Virtual Environment
```bash
git clone <repo-url>
cd Nivetha-p&m

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```
Ensure `DJANGO_SETTINGS_MODULE=config.settings.local` and `DEBUG=True` for local development.

### 4. Database Migrations
Run migrations against the local SQLite database:
```bash
python manage.py migrate
```

### 5. Tailwind CSS Standalone CLI Setup (v3.4.17)

Tailwind CSS v3.4.17 is compiled using the standalone CLI binary. **Do not commit binaries to Git.**

Download the appropriate binary for your OS into the project `bin/` directory:

- **Windows (x64):**
  Download `tailwindcss-windows-x64.exe` from [Tailwind CSS v3.4.17 Releases](https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-windows-x64.exe) and save as `bin/tailwindcss.exe`.
  ```powershell
  mkdir bin -Force
  Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-windows-x64.exe" -OutFile "bin/tailwindcss.exe"
  ```
  Watch and auto-recompile styles during development:
  ```powershell
  .\bin\tailwindcss.exe -i static/css/input.css -o static/css/output.css --watch
  ```
  Or perform a one-time minified production build:
  ```powershell
  .\bin\tailwindcss.exe -i static/css/input.css -o static/css/output.css --minify
  ```

- **macOS (Apple Silicon / ARM64):**
  ```bash
  mkdir -p bin
  curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-macos-arm64
  mv tailwindcss-macos-arm64 bin/tailwindcss && chmod +x bin/tailwindcss
  ./bin/tailwindcss -i static/css/input.css -o static/css/output.css --watch
  ```

- **macOS (Intel / x64):**
  ```bash
  mkdir -p bin
  curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-macos-x64
  mv tailwindcss-macos-x64 bin/tailwindcss && chmod +x bin/tailwindcss
  ./bin/tailwindcss -i static/css/input.css -o static/css/output.css --watch
  ```

- **Linux (x64 / Render environment):**
  Handled automatically during deployment in `build.sh`:
  ```bash
  mkdir -p bin
  curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64
  mv tailwindcss-linux-x64 bin/tailwindcss && chmod +x bin/tailwindcss
  ./bin/tailwindcss -i static/css/input.css -o static/css/output.css --minify
  ```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://localhost:8000/` to verify the application. The Django admin is mounted at `http://localhost:8000/panel/` (`/admin/` returns 404).

---

## Running Automated Tests

Run the test suite with:
```bash
python manage.py test
```
All tests use an in-memory SQLite database and require no external services.

---

## Render + Neon Deployment

### 1. Neon Database Setup
1. Create a project on [Neon](https://neon.tech).
2. Copy the connection string (`postgres://...`).
3. Set the `DATABASE_URL` environment variable on Render.

### 2. Render Web Service Configuration
- **Environment:** Python 3
- **Build Command:**
  ```bash
  ./build.sh
  ```
  (`build.sh` installs requirements, downloads `tailwindcss-linux-x64` v3.4.17, compiles minified CSS, executes `collectstatic --no-input`, and runs `python manage.py migrate`).
- **Start Command:**
  ```bash
  gunicorn config.wsgi:application --workers 2 --bind 0.0.0.0:$PORT
  ```

### 3. Required Environment Variables on Render
| Variable | Value / Description |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` (Required for Render; `config/wsgi.py` also defaults to this as a fail-safe so production never runs with `DEBUG=True`) |
| `SECRET_KEY` | Strong random secret string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-service.onrender.com,yourcustomdomain.com` |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `USE_CLOUDINARY` | `True` (Production) / `False` (Staging) |
| `CLOUDINARY_URL` | Cloudinary API credentials URL (required if `USE_CLOUDINARY=True`) |
| `BUSINESS_PHONE` | Customer support phone number |
| `BUSINESS_WHATSAPP` | WhatsApp number (for `wa.me` links) |
| `TELEGRAM_BOT_TOKEN` | (Optional) Telegram bot token |
| `TELEGRAM_CHAT_ID` | (Optional) Telegram chat ID |

---

## Cloudinary Media Storage Setup

### 1. Creating a Cloudinary Account
1. Sign up for a free account at [Cloudinary](https://cloudinary.com).
2. Complete verification and log into the Cloudinary Console.

### 2. Finding Your CLOUDINARY_URL
1. From the Cloudinary Dashboard (Programmable Media), find **API Environment variable** under Product Environment Credentials.
2. Click the copy icon to copy the URL format:
   `cloudinary://<api_key>:<api_secret>@<cloud_name>`
3. Never commit this URL or API keys to version control.

### 3. Configuration & Render Ephemeral Disk Warning
- **Local Development:** `USE_CLOUDINARY=False` is the default in `.env`. Uploaded images are stored locally under `media/`.
- **Render Production:** Must set `USE_CLOUDINARY=True` and add `CLOUDINARY_URL` in the Render dashboard environment variables.
- **Render Ephemeral Filesystem:** Render free web services have an ephemeral filesystem. Any files written to local disk are wiped on container restart or redeployment. Production must use Cloudinary to ensure uploaded gallery photos persist permanently.

