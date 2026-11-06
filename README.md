# Nivetha Packers and Movers — Web Platform

Small business website and lead-capture platform for Nivetha Packers and Movers (Tiruppur, Tamil Nadu), serving routes to Chennai, Madurai, and nearby towns.

## Tech Stack

- **Backend:** Python 3.12+ / Django 5.2
- **Styling:** Tailwind CSS v3.4.17 (standalone CLI binary; no Node.js/npm required)
- **Database:** SQLite (local development) / PostgreSQL on Neon (production)
- **Static & Media:** WhiteNoise (`CompressedManifestStaticFilesStorage`) + Cloudinary (production) / local disk (development) via Django 5.2 `STORAGES`
- **WSGI Server:** Gunicorn
- **Deployment:** Render (Web Service) + Neon (Serverless Postgres)

---

## Local Development Setup

### 1. Prerequisites
- Python 3.12+ installed
- Git
- PowerShell (Windows) or Terminal (macOS/Linux)

### 2. Clone Repository & Setup Virtual Environment

**Windows (PowerShell):**
```powershell
git clone <repo-url>
cd Nivetha-p&m

# Create virtual environment
python -m venv .venv

# If script execution is restricted in PowerShell, run once:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
git clone <repo-url>
cd Nivetha-p&m

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```
For local development, the defaults in `.env.example` work out of the box (`DEBUG=True`, SQLite database, local media storage).

### 4. Tailwind CSS Standalone CLI Setup (v3.4.17)
Tailwind CSS v3.4.17 compiles via the standalone CLI binary. **Do not commit binaries to Git.**

- **Windows (x64):**
  ```powershell
  mkdir bin -Force
  Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-windows-x64.exe" -OutFile "bin/tailwindcss.exe"
  ```
  Watch and auto-recompile during design tweaks:
  ```powershell
  .\bin\tailwindcss.exe -i static/css/input.css -o static/css/output.css --watch
  ```
  Or one-time production minification:
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

### 5. Database Migrations & Initial Data
Run database migrations:
```powershell
python manage.py migrate
```

Setup initial moving services and client permissions:
```powershell
# 1. Seed initial moving services (Household, Office, Vehicle)
python manage.py seed_services

# 2. Configure the "Client" user group with restricted model permissions
python manage.py create_client_group
```

### 6. Create Users (Superuser & Client Staff)

**Create Developer Superuser:**
```powershell
python manage.py createsuperuser
```

**Create Client Staff User (Restricted to Enquiries, Services, Gallery):**
Run the Django shell:
```powershell
python manage.py shell
```
Execute the following snippet:
```python
from django.contrib.auth.models import User, Group

# Create client staff user
client_user = User.objects.create_user(
    username='nivetha_client',
    password='ReplaceWithSecurePassword123!',
    is_staff=True  # Grants access to log into /panel/
)

# Assign to restricted Client group
client_group = Group.objects.get(name='Client')
client_user.groups.add(client_group)
print("Client staff user created and assigned to 'Client' group successfully.")
exit()
```

### 7. Run the Development Server
```powershell
python manage.py runserver
```
- Public website: `http://localhost:8000/`
- Owner management panel: `http://localhost:8000/panel/` (Note: `/admin/` intentionally returns 404)

---

## Running Automated Tests

Run the test suite:
```powershell
python manage.py test
```
The test suite executes against an isolated SQLite test database and tests models, forms, channels, SEO tags, storage, and permission boundaries without requiring external network services.

---

## Environment Variables Reference

| Variable | Required | Default | Example Value | Description |
|---|---|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Yes | `config.settings.local` | `config.settings.production` | Determines whether local or production settings are active. |
| `SECRET_KEY` | Yes | (insecure dev key) | `c-!v@79#@e&8f8*@^5*j453$5+k&j*s-6#d@p...` | Cryptographic secret key (50+ random characters in production). |
| `DEBUG` | Yes | `True` (local) | `False` | Debug mode. Must strictly be `False` in production. |
| `ALLOWED_HOSTS` | Yes | `localhost,127.0.0.1` | `nivetha-pm.onrender.com,nivethapackers.in` | Comma-separated list of host/domain names. |
| `CSRF_TRUSTED_ORIGINS` | No | `http://localhost:8000...` | `https://*.onrender.com,https://nivethapackers.in` | Comma-separated HTTPS origins permitted to submit forms. |
| `DATABASE_URL` | Prod | (empty: uses SQLite) | `postgres://user:pass@ep-xyz.neon.tech/neondb` | PostgreSQL connection string from Neon. |
| `USE_CLOUDINARY` | No | `False` | `True` | Switch between local disk media (`False`) and Cloudinary (`True`). |
| `CLOUDINARY_URL` | If Cloudinary | (empty) | `cloudinary://123456789:abcdefgh@cloudname` | Cloudinary API environment variable. |
| `SITE_URL` | No | `http://localhost:8000` | `https://nivethapackers.in` | Absolute domain used in `sitemap.xml`, `robots.txt`, and JSON-LD. |
| `ADMIN_URL` | No | `panel` | `panel` | Custom URL prefix for the Django management panel. |
| `ALLOW_INDEXING` | No | `False` | `True` | When `False`, blocks all crawlers (`Disallow: /`) and adds `noindex, nofollow` to all pages. Set `True` on the final domain. |
| `BUSINESS_PHONE` | No | (empty) | `+91 98765 43210` | Display phone number and `tel:` links. |
| `BUSINESS_WHATSAPP` | No | (empty) | `+91 98765 43210` | WhatsApp number for direct click-to-chat links. |
| `BUSINESS_ADDRESS` | No | `Tiruppur, Tamil Nadu` | `123 Kangeyam Road, Tiruppur, Tamil Nadu` | Address string used in footer and JSON-LD schema. |
| `TELEGRAM_BOT_TOKEN` | No | (empty) | `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ` | Telegram bot token for instant enquiry push alerts. |
| `TELEGRAM_CHAT_ID` | No | (empty) | `-1001234567890` | Telegram target chat ID for enquiry notifications. |
| `SECURE_SSL_REDIRECT` | No | `True` (in prod) | `True` | Enforces HTTP to HTTPS redirection in production. |

---

## Render + Neon Deployment Guide

### 1. Neon Database Setup
1. Log in to [Neon](https://neon.tech) and create a new project named `nivetha-pm`.
2. In the Neon Console Dashboard, locate **Connection Details**.
3. Select **Connection string** with **PostgreSQL** and copy the URI:
   `postgres://username:password@ep-cool-fog-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
4. This URI is your `DATABASE_URL` for Render.

### 2. Render Web Service Configuration
1. Log in to [Render](https://render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the service settings:
   - **Name:** `nivetha-pm`
   - **Region:** `Singapore` (recommended for lowest latency in Tamil Nadu / India) or `Frankfurt`
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn config.wsgi:application --workers 1 --bind 0.0.0.0:$PORT`
   - **Plan Type:** `Free` (512 MB RAM; 1 worker configured for safe memory headroom)

### 3. Configure Production Environment Variables in Render
Under the **Environment** tab of your Render Web Service, add the following variables:

```ini
PYTHON_VERSION = 3.12.8
DJANGO_SETTINGS_MODULE = config.settings.production
DEBUG = False
SECRET_KEY = <generate-a-strong-random-50-character-string>
ALLOWED_HOSTS = <your-service-name>.onrender.com,nivethapackers.in
CSRF_TRUSTED_ORIGINS = https://<your-service-name>.onrender.com,https://nivethapackers.in
SITE_URL = https://nivethapackers.in
DATABASE_URL = <your-neon-postgres-connection-string>
USE_CLOUDINARY = False
CLOUDINARY_URL = 
ADMIN_URL = panel
ALLOW_INDEXING = False
BUSINESS_PHONE = +91 93442 66547
BUSINESS_WHATSAPP = +91 93442 66547
BUSINESS_ADDRESS = Tiruppur, Tamil Nadu
```

> **Cloudinary Staging Note:** In `render.yaml`, `USE_CLOUDINARY` defaults to `False` for the initial staging deployment. Once you obtain your `CLOUDINARY_URL` credentials from Cloudinary, paste it into the Render Environment tab and switch `USE_CLOUDINARY=True`.

> **Optional Notifications:** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are optional. If omitted, the site functions normally, and enquiries are logged directly to `/panel/`.

### 4. Post-Deploy First-Time Setup (Render Shell)
Once the first deployment finishes, open the **Shell** tab in the Render Dashboard and run:

```bash
# 1. Create developer superuser
python manage.py createsuperuser

# 2. Ensure Client group permissions are created
python manage.py create_client_group

# 3. Seed standard moving services (if not already populated)
python manage.py seed_services

# 4. Create the Client staff user
python manage.py shell
```
Inside the python shell:
```python
from django.contrib.auth.models import User, Group
user = User.objects.create_user('client_owner', password='SecurePassword123!', is_staff=True)
user.groups.add(Group.objects.get(name='Client'))
exit()
```

### 5. Custom Domain Setup
1. In Render, go to **Settings** → **Custom Domains**.
2. Add your root domain (`nivethapackers.in`) and subdomain (`www.nivethapackers.in`).
3. Update your DNS provider:
   - CNAME for `www` pointing to `<your-service-name>.onrender.com`
   - ANAME / ALIAS for root pointing to Render's DNS targets.
4. Update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL` in Render environment variables to reflect the custom domain.

### 6. Storage & Render Free Tier Notes
- **Render Free Tier Spin-down:** On the free tier, web services spin down after 15 minutes of inactivity. The first request after idle can take 30–50 seconds to wake up the service.
- **Ephemeral Disk Warning:** Render free tier instances wipe the local container filesystem on every restart or deploy. Local media storage (`USE_CLOUDINARY=False`) will lose uploaded images on restart. **Production must set `USE_CLOUDINARY=True` with valid Cloudinary credentials to persist uploaded photos.**

---

## Staging Verification & Smoke Test Sequence

*(Status: Documentation complete; execution pending manual deploy)*

After deploying to staging or production, run the following verification checks:

### Automated cURL Smoke Test
```bash
STAGING_URL="https://<your-service-name>.onrender.com"

# 1. Verify all 5 public pages return HTTP 200
curl -s -o /dev/null -w "%{http_code} Home\n" "$STAGING_URL/"
curl -s -o /dev/null -w "%{http_code} Services\n" "$STAGING_URL/services/"
curl -s -o /dev/null -w "%{http_code} Gallery\n" "$STAGING_URL/gallery/"
curl -s -o /dev/null -w "%{http_code} About\n" "$STAGING_URL/about/"
curl -s -o /dev/null -w "%{http_code} Contact\n" "$STAGING_URL/contact/"

# 2. Verify SEO files return HTTP 200 and disallow admin
curl -s -o /dev/null -w "%{http_code} Sitemap\n" "$STAGING_URL/sitemap.xml"
curl -s "$STAGING_URL/robots.txt" | grep "Disallow: /panel/"

# 3. Verify default /admin/ returns 404
curl -s -o /dev/null -w "%{http_code} Default admin 404 check\n" "$STAGING_URL/admin/"
```

### Manual Verification Checklist
1. **Public Pages:** Open Home, Services, Gallery, About, and Contact in a mobile browser. Verify layout, fonts, and theme toggle.
2. **Quote Form Submission:** Submit a quote request on Home or Contact page. Verify success message displays without error.
3. **Admin Verification:** Log into `/panel/` with `client_owner`:
   - Verify only **Enquiries**, **Services**, and **Gallery** appear (no Users or Groups).
   - Check that the new enquiry has an amber highlight.
   - Click into the enquiry detail and tap the **WhatsApp customer** link.
4. **Gallery Upload:** Upload a JPEG under 5 MB in Gallery admin and confirm it displays on `/gallery/`.

---

## Cloudinary Media Storage Setup

### 1. Creating a Cloudinary Account
1. Sign up for a free account at [Cloudinary](https://cloudinary.com).
2. Complete verification and log into the Cloudinary Console.

### 2. Finding Your CLOUDINARY_URL
1. From the Cloudinary Dashboard (Programmable Media), find **API Environment variable** under Product Environment Credentials.
2. Copy the URL format:
   `cloudinary://<api_key>:<api_secret>@<cloud_name>`
3. Set `CLOUDINARY_URL` in the Render dashboard. Never commit this key to version control.

---

## Production Go-Live Checklist

Before public launch, verify:
- [ ] `DEBUG=False` in Render environment variables.
- [ ] A cryptographically secure 50+ character `SECRET_KEY` is configured.
- [ ] `SECURE_SSL_REDIRECT=True` and HTTPS automatically redirects.
- [ ] Admin panel is secured at custom `/panel/` path; default `/admin/` returns 404.
- [ ] `SITE_URL` matches the production custom domain (`https://nivethapackers.in`).
- [ ] Set `ALLOW_INDEXING=True` on the final domain (enables search engine indexing and advertises sitemap).
- [ ] `/sitemap.xml` lists all five public URLs with the live domain.
- [ ] `/robots.txt` disallows `/panel/` and points to the live sitemap.
- [ ] Submit `https://nivethapackers.in/sitemap.xml` to [Google Search Console](https://search.google.com/search-console).
- [ ] Verify or update the [Google Business Profile](https://business.google.com) with matching business name, phone number, and Tiruppur address.
- [ ] Verify automated database backups and point-in-time recovery on the Neon console.
