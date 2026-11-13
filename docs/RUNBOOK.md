# Operations Runbook: Nivetha Packers and Movers

Operational guide for setup, deployment, configuration, backups, troubleshooting, and maintenance.

---

## 1. Local Setup on Windows (PowerShell)

```powershell
# 1. Clone repository and navigate to project root
git clone <repo-url>
cd Nivetha-p&m

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# If PowerShell script execution is restricted, run once:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment template
Copy-Item .env.example .env
# Edit .env if custom values are needed; defaults work for local dev.

# 5. Download standalone Tailwind CSS CLI (v3.4.17)
mkdir bin -Force
Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-windows-x64.exe" -OutFile "bin/tailwindcss.exe"

# 6. Compile CSS (one-time minified or watch mode)
.\bin\tailwindcss.exe -i static/css/input.css -o static/css/output.css --minify

# 7. Apply migrations
python manage.py migrate

# 8. Create superuser and client group
python manage.py createsuperuser
python manage.py create_client_group

# 9. (Optional) Seed standard services
python manage.py seed_services

# 10. Run local development server
python manage.py runserver
```

---

## 2. Environment Variables Reference

| Variable Name | Required | Default / Example | Purpose |
| :--- | :---: | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Yes | `config.settings.production` | Active Django settings module. |
| `SECRET_KEY` | Yes (Prod) | `<generate-secure-random-key>` | Cryptographic secret for signing and sessions. |
| `DEBUG` | No | `False` | Debug mode. Must strictly be `False` in production. |
| `ALLOWED_HOSTS` | Yes (Prod) | `example.onrender.com,example.com` | Comma-separated list of valid hostnames. |
| `CSRF_TRUSTED_ORIGINS` | Yes (Prod) | `https://example.onrender.com` | Comma-separated list of trusted CSRF scheme/domains. |
| `SITE_URL` | Yes (Prod) | `https://example.com` | Canonical site URL for sitemaps and schema markup. |
| `ADMIN_URL` | No | `panel` | Custom URL prefix for Django admin dashboard. |
| `ALLOW_INDEXING` | No | `False` | `True` enables search crawlers; `False` blocks all bots. |
| `DATABASE_URL` | Yes (Prod) | `postgresql://user:pass@host/db?sslmode=require` | PostgreSQL connection string (Neon). |
| `USE_CLOUDINARY` | No | `False` | Set `True` when Cloudinary credentials are configured. |
| `CLOUDINARY_URL` | Conditional | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME` | Cloudinary storage connection string. |
| `BUSINESS_PHONE` | No | `919XXXXXXXXX` | Primary contact number for click-to-call links. |
| `BUSINESS_WHATSAPP` | No | `919XXXXXXXXX` | WhatsApp number for pre-filled chat links. |
| `BUSINESS_ADDRESS` | No | `Tiruppur, Tamil Nadu` | Physical office location displayed in footer/contact. |
| `TELEGRAM_BOT_TOKEN` | No | `<bot-token-from-botfather>` | Optional Telegram bot token for lead notifications. |
| `TELEGRAM_CHAT_ID` | No | `<chat-or-channel-id>` | Optional Telegram target chat ID for lead alerts. |
| `SITE_PALETTE` | No | `beige` | Active color palette preset (`beige` or `navy`). |
| `SITE_LOGO` | No | `img/logo.png` | Optional static path or URL for header brand logo. |
| `SECURE_SSL_REDIRECT` | No | `True` | Forces HTTP to HTTPS redirection in production. |

---

## 3. Render + Neon Deployment Guide

### A. Neon PostgreSQL Database
1. Sign up / log in to [Neon](https://neon.tech).
2. Create a new project (Region: `ap-southeast-1` Singapore or nearest).
3. Copy the pooled connection string ending in `?sslmode=require`.

### B. Render Web Service Settings
1. Create a **New Web Service** connected to your Git repository.
2. Configure settings:
   - **Name**: `nivetha-packers-movers`
   - **Region**: `Singapore` (matches Neon database region)
   - **Runtime**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 120`
   - **Plan**: `Free` (or `Starter` for zero cold starts)
3. In **Environment Variables**, add:
   - `DJANGO_SETTINGS_MODULE` = `config.settings.production`
   - `SECRET_KEY` = `<strong-random-key>`
   - `DEBUG` = `False`
   - `DATABASE_URL` = `<neon-connection-string>`
   - `ALLOWED_HOSTS` = `<your-subdomain>.onrender.com`
   - `CSRF_TRUSTED_ORIGINS` = `https://<your-subdomain>.onrender.com`
   - `SITE_URL` = `https://<your-subdomain>.onrender.com`
   - `ADMIN_URL` = `panel`
   - `ALLOW_INDEXING` = `False` (switch to `True` on final domain)
   - `USE_CLOUDINARY` = `False` (switch to `True` after setting `CLOUDINARY_URL`)
   - `PYTHON_VERSION` = `3.12.8`

### C. First Deploy Steps
1. Trigger deploy and verify `build.sh` runs migrations and `collectstatic`.
2. Open Render **Shell** tab for the service:
   ```bash
   python manage.py createsuperuser
   python manage.py create_client_group
   python manage.py seed_services
   ```
3. In the admin `/panel/`, create the client's staff user, mark `Staff status` = True, and assign to `Client` group.

---

## 4. Rollback Procedure (Render)

1. Navigate to the **Deploys** tab in the Render Dashboard.
2. Locate the last known good deployment.
3. Click the three dots menu `...` on that deploy and select **Rollback to this deploy**.
4. If database schema was modified in a recent migration, run a backward migration via the Render Shell before or immediately after rollback:
   ```bash
   python manage.py migrate core <previous_migration_number>
   ```

---

## 5. Database Backup and Restore (Neon)

### Backup to Local Machine:
```bash
# Set connection string in shell session (do not hardcode in scripts)
pg_dump "$DATABASE_URL" -F c -b -v -f "nivetha_backup_$(date +%Y%m%d).dump"
```

### Restore to Neon Database:
```bash
# WARNING: Drops and restores into target database
pg_restore -d "$DATABASE_URL" --clean --no-owner --no-privileges "nivetha_backup_YYYYMMDD.dump"
```

*Note: Neon also provides instant point-in-time branch snapshots directly within the Neon Web Console.*

---

## 6. Troubleshooting Matrix

| Issue | Symptom / Error | Root Cause & Resolution |
| :--- | :--- | :--- |
| **Host Blocked** | `HTTP 400 Bad Request` | Domain is missing from `ALLOWED_HOSTS`. Add hostname to env var and redeploy. |
| **CSRF Failed** | `HTTP 403 Forbidden` on form post | Origin missing from `CSRF_TRUSTED_ORIGINS`. Add full `https://domain` scheme. |
| **Missing Static Files** | Missing styles / 500 on CSS request | Run `collectstatic`. Ensure `tailwindcss` minified output exists before collectstatic. |
| **Cloudinary Error** | Upload crash or startup failure | Ensure `CLOUDINARY_URL` is set when `USE_CLOUDINARY=True`. Revert to `False` if credentials invalid. |
| **Cold Start Delay** | First request takes 30–50 seconds | Render Free tier spins down after 15m inactivity. Normal behavior on Free tier; upgrade to Starter for 24/7 uptime. |
| **Admin Missing** | `HTTP 404 Not Found` on `/admin/` | Admin URL is customized via `ADMIN_URL`. Visit `/<ADMIN_URL>/` (default `/panel/`). |
| **Environment Inactive** | `ModuleNotFoundError: No module named 'django'` | Virtual environment not active. Run `.\.venv\Scripts\Activate.ps1`. |

---

## 7. Production Go-Live Checklist

- [ ] `DEBUG` is set to `False`.
- [ ] `SECRET_KEY` is a unique 50+ character random string.
- [ ] Custom domain connected on Render; DNS CNAME configured.
- [ ] `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL` match custom domain.
- [ ] `SECURE_SSL_REDIRECT=True` and HTTPS loads cleanly without certificate errors.
- [ ] Superuser created; client user created and assigned to `Client` group.
- [ ] `USE_CLOUDINARY=True` and `CLOUDINARY_URL` verified with a test image upload.
- [ ] `ALLOW_INDEXING=True` enabled on final production domain.
- [ ] `robots.txt` and `/sitemap.xml` verified via browser.
- [ ] Google Search Console verified via HTML meta tag or DNS TXT record.
- [ ] Google Business Profile verified with matching phone, name, and address.
- [ ] Submit test quote on live site; confirm record appears in `/panel/`.

---

## 8. Monthly Maintenance Checklist

- [ ] Inspect `/panel/` quote inquiries and verify no orphaned leads.
- [ ] Check Render deployment logs for 5xx errors or unexpected restart loops.
- [ ] Review Neon storage metrics and connection pool health.
- [ ] Run `pip list --outdated` locally and test security patch updates.
- [ ] Create and download a fresh monthly `pg_dump` snapshot from Neon.
