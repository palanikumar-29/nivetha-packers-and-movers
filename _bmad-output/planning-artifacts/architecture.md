---
title: Nivetha Packers and Movers — Architecture
status: final
created: 2026-11-03
updated: 2026-11-03
---

# Architecture: Nivetha Packers and Movers Website

> This document describes invariants only. Implementation detail belongs in code. Where a decision has trade-offs, they are named. The tech stack is fixed; do not re-open it.

---

## 1. Django Project and App Layout

```
nivetha_pm/                  ← repo root
├── config/                  ← Django project package
│   ├── settings/
│   │   ├── base.py          ← shared settings
│   │   ├── local.py         ← SQLite, DEBUG=True, local media
│   │   └── production.py    ← Neon PG, DEBUG=False, Cloudinary, HTTPS
│   ├── urls.py              ← root URL conf (public + /panel/ + sitemap/robots)
│   └── wsgi.py
├── core/                    ← single Django app (all models, views, forms)
│   ├── models.py            ← QuoteRequest, Service, GalleryImage
│   ├── forms.py             ← QuoteForm (with honeypot field)
│   ├── views.py             ← public page views + form POST handler
│   ├── admin.py             ← custom admin: /panel/ registration, Client group
│   ├── channels/            ← notification channels layer (§5)
│   │   ├── __init__.py      ← dispatch() function
│   │   └── telegram.py      ← optional Telegram channel
│   ├── management/
│   │   └── commands/
│   │       └── create_client_group.py
│   ├── templates/
│   │   ├── base.html        ← layout, floating buttons, meta block
│   │   ├── home.html
│   │   ├── services.html
│   │   ├── gallery.html
│   │   ├── about.html
│   │   └── contact.html
│   └── tests/
│       ├── test_models.py
│       ├── test_forms.py
│       ├── test_views.py
│       ├── test_channels.py
│       ├── test_permissions.py
│       └── test_seo.py
├── static/
│   └── css/
│       └── output.css       ← compiled Tailwind (committed or built on Render)
├── media/                   ← local dev only; gitignored
├── tailwind.config.js
├── .env.example
├── requirements.txt         ← includes Django 5.2, psycopg2-binary, dj-database-url, python-decouple, whitenoise, gunicorn, django-cloudinary-storage, cloudinary, requests
├── build.sh                 ← Render build script: pip, curl tailwind standalone, compile css, collectstatic, migrate
├── render.yaml              ← (or documented build/start commands in README)
└── README.md
```

**One app rule:** Everything lives in `core`. No separate `enquiries`, `gallery`, or `pages` apps. This is a 5-page site — premature splitting adds indirection with no benefit.

**Settings selection:** `DJANGO_SETTINGS_MODULE` env var switches between `config.settings.local` and `config.settings.production`. python-decouple reads `.env` for local; Render dashboard env vars for production.

---

## 2. Data Models

All models live in `core/models.py`. One migration file per story that touches models.

### QuoteRequest (Enquiry)

| Field | Type | Notes |
|---|---|---|
| `id` | AutoField PK | — |
| `name` | CharField(100) | required |
| `phone` | CharField(10) | validated: 10 digits, starts 6–9 |
| `move_type` | CharField choices | house / office / vehicle / other |
| `moving_from` | CharField(100) | required |
| `moving_to` | CharField(100) | required |
| `preferred_date` | DateField null/blank | optional; must be ≥ today if supplied |
| `details` | TextField blank | optional |
| `status` | CharField choices | New / Called / Confirmed / Closed; default=New |
| `notes` | TextField blank | internal; Client user only |
| `created_at` | DateTimeField auto_now_add | — |
| `status_updated_at` | DateTimeField null/blank | set on status change |

`__str__`: `"{name} — {move_type} ({status})"`

### Service

| Field | Type | Notes |
|---|---|---|
| `id` | AutoField PK | — |
| `title` | CharField(120) | — |
| `description` | TextField | — |
| `order` | PositiveIntegerField default=0 | ascending sort |
| `is_active` | BooleanField default=True | — |

### GalleryImage

| Field | Type | Notes |
|---|---|---|
| `id` | AutoField PK | — |
| `image` | ImageField / CloudinaryField | switched by USE_CLOUDINARY (§6) |
| `caption` | CharField(200) | used as `alt` text |
| `is_active` | BooleanField default=True | — |
| `order` | PositiveIntegerField default=0 | ascending sort |

**No soft-delete.** `is_active=False` hides from public; hard delete from admin.

---

## 3. URL Structure and Admin Path

```python
# config/urls.py
urlpatterns = [
    path("",          include("core.urls")),
    path("panel/",    admin.site.urls),        # custom admin path
    path("sitemap.xml", sitemap_view),
    path("robots.txt",  robots_view),
    # /admin/ is NOT included — 404 by omission
]
```

### Public URLs (core/urls.py)

| URL | View | Name |
|---|---|---|
| `/` | `HomeView` | `home` |
| `/services/` | `ServicesView` | `services` |
| `/gallery/` | `GalleryView` | `gallery` |
| `/about/` | `AboutView` | `about` |
| `/contact/` | `ContactView` (GET + POST) | `contact` |

`ContactView` handles both the standalone contact page form AND processes POST from the embedded Home form (both POST to `/contact/`). On success: redirect to `?submitted=1` or a named success URL — no re-render with the same POST.

**Story 1.2 renders the Quote form markup only.** The POST handler (`ContactView.post`) and all save/validation/channels logic belongs to Story 1.4. In Story 1.2, the form `action` can point to `#` or `/contact/`; it will simply not process yet.

---

## 4. Roles and Permissions

Three roles, no custom auth backend needed — Django's built-in permission system is sufficient.

| Role | Django representation | Panel access |
|---|---|---|
| Public visitor | Anonymous | None |
| Client user | `is_staff=True`, in "Client" group | Enquiries, Services, Gallery only |
| Superuser (developer) | `is_superuser=True` | Full Django admin |

### Client Group — exact permissions

Set by `python manage.py create_client_group`. Idempotent (safe to re-run).

```
core.view_quoterequest
core.change_quoterequest
core.view_service
core.add_service
core.change_service
core.delete_service
core.view_galleryimage
core.add_galleryimage
core.change_galleryimage
core.delete_galleryimage
```

**No** `auth.*`, `sessions.*`, `admin.*`, `contenttypes.*` permissions.

### Admin registration pattern

In `core/admin.py`, each `ModelAdmin` overrides `get_queryset` and `has_module_perms` as needed. The simplest enforcement is that Django's built-in permission check already hides models the Client group has no permissions for — the command above is the only configuration needed. No custom middleware required.

---

## 5. Notification Channels Layer

**Design constraint:** A notification failure must never raise an exception that reaches the view. The view saves the Enquiry, calls `dispatch(enquiry)`, then returns the success response — regardless of what `dispatch` does.

### Interface

```python
# core/channels/__init__.py

def dispatch(enquiry: QuoteRequest) -> None:
    """Call all registered channels. Swallow every exception."""
    for channel_fn in _get_channels():
        try:
            channel_fn(enquiry)
        except Exception:
            logger.exception("Channel %s failed", channel_fn.__name__)

def _get_channels():
    channels = []
    # Telegram: only if both env vars present
    from django.conf import settings
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        from .telegram import send
        channels.append(send)
    return channels
```

Adding a new channel (e.g. WhatsApp Business API) = create `core/channels/whatsapp.py`, add it to `_get_channels()`. Zero changes to views or models.

### Telegram channel (optional)

- Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from settings (sourced from env vars).
- If either is absent, the channel is not registered — `_get_channels()` simply doesn't include it.
- Uses `requests.post()` to `https://api.telegram.org/bot{TOKEN}/sendMessage`.
- **Dependency:** `requests` is an explicit dependency listed in `requirements.txt`.
- Timeout: 5 seconds. Any exception is caught by the outer `dispatch` loop.

**In this phase:** The admin panel is the primary (and only guaranteed) owner notification channel. Telegram is scaffolded and optional. There is no email, no WhatsApp Business API push.

---

## 6. Image Storage

In Django 5.1+, `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` are removed in favor of the `STORAGES` dictionary. The `default` storage backend switches based on `USE_CLOUDINARY`:

```python
# config/settings/base.py
USE_CLOUDINARY = env.bool("USE_CLOUDINARY", default=False)

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if USE_CLOUDINARY
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
```

| Environment | `USE_CLOUDINARY` | Storage backend |
|---|---|---|
| Local dev | `false` (default) | Local disk (`media/`) |
| Render staging | `false` | Local disk (acceptable for staging) |
| Render production | `true` | Cloudinary free tier |

**Library:** `django-cloudinary-storage` + `cloudinary`. The `GalleryImage.image` field type stays standard `models.ImageField` — the storage backend is swapped under `STORAGES["default"]`. No model migration needed when switching.

**Render ephemeral disk note:** Render free web services have an ephemeral filesystem. Images uploaded to local disk on a staging Render instance will be lost on container restart. This is expected for staging; production must set `USE_CLOUDINARY=true`.

---

## 7. SEO Approach

### Per-page metadata (Stories 1.2 and 1.3)

Each page template extends `base.html` and fills a `{% block seo %}` (or individual blocks):

```html
<!-- base.html -->
<title>{% block title %}Nivetha Packers and Movers{% endblock %}</title>
<meta name="description" content="{% block meta_description %}{% endblock %}">
<link rel="canonical" href="{{ request.build_absolute_uri }}">
```

Every page template overrides `block title` (≤ 60 chars) and `block meta_description` (≤ 160 chars). Exactly one `<h1>` per page — enforced by convention and tested.

**Per-page metadata is owned by Stories 1.2 and 1.3, not 1.6.** Story 1.6 owns only sitemap, robots.txt, and JSON-LD schema.

### Sitemap (Story 1.6)

Use `django.contrib.sitemaps`. Register a `StaticViewSitemap` covering the five public URL names. Mount at `/sitemap.xml` in root `urls.py`. No `/panel/` URLs included.

### robots.txt (Story 1.6)

Serve as a plain-text Django view (no third-party package needed):

```
User-agent: *
Allow: /
Disallow: /panel/
Sitemap: https://{domain}/sitemap.xml
```

### JSON-LD schema (Story 1.6)

Rendered inline in `home.html` using a Django template. Schema type: `["LocalBusiness", "MovingCompany"]`. Fields: `name`, `address` (Tiruppur, Tamil Nadu), `telephone` from `BUSINESS_PHONE` env var, `areaServed: ["Tiruppur", {"@type": "AdministrativeArea", "name": "Tamil Nadu"}]`. No external library.

---

## 8. Security and Configuration

### Environment variables (complete list)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | Yes | `False` | Never `True` in prod |
| `ALLOWED_HOSTS` | Yes | — | Comma-separated; Render domain + custom domain |
| `DATABASE_URL` | Prod | SQLite | dj-database-url parses Neon connection string |
| `USE_CLOUDINARY` | No | `false` | Switch gallery storage backend |
| `CLOUDINARY_URL` | If USE_CLOUDINARY | — | Cloudinary credentials (single URL form) |
| `BUSINESS_PHONE` | Yes | `""` | tel: link and JSON-LD; never hardcoded |
| `BUSINESS_WHATSAPP` | Yes | `""` | wa.me link; never hardcoded |
| `TELEGRAM_BOT_TOKEN` | No | `""` | Enables Telegram channel if both set |
| `TELEGRAM_CHAT_ID` | No | `""` | Enables Telegram channel if both set |

### Production security settings

```python
# config/settings/production.py
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = "DENY"
```

### CSRF

Django's built-in `CsrfViewMiddleware` is active. All POST views use `{% csrf_token %}`. The quote form POST is not exempt. A missing token returns HTTP 403.

### Honeypot spam protection

`QuoteForm` includes a hidden field (e.g. `name="website"`, hidden via CSS class `hidden` — not `display:none` in inline style, which some bots detect). The view checks: if `request.POST.get("website")` is non-empty, return a fake success response and do not save.

### Password policy

Django's built-in validators are active in production: `UserAttributeSimilarityValidator`, `MinimumLengthValidator(12)`, `CommonPasswordValidator`, `NumericPasswordValidator`. Applied to the Client user account.

### No SMTP

Render free tier blocks outbound SMTP. `EMAIL_BACKEND` is not configured. No `django.core.mail` calls are made anywhere. The notification layer is channels-only.

---

## 9. Testing Approach

**Runner:** Django's built-in test runner (`python manage.py test`). No pytest required, but pytest-django is acceptable if the developer prefers it.

**Database:** Tests use an in-memory SQLite database. No external services (Cloudinary, Telegram) are called in tests — use `unittest.mock.patch`.

**Per-story test scope:**

| Story | Test file | Must cover |
|---|---|---|
| 1.1 | `test_models.py` | Model creation, field defaults, `__str__` |
| 1.2 | `test_views.py` | GET `/` → 200, one `<h1>`, `<nav>`, `<footer>`, no hardcoded phone |
| 1.3 | `test_views.py` | GET each of 4 pages → 200; active/inactive Service filter; lazy + alt on gallery image |
| 1.4 | `test_forms.py` | Valid save, bad phone, past date, missing fields, honeypot, CSRF |
| 1.5 | `test_channels.py` | Telegram skipped when vars absent; failure caught when API mocked to raise; payload correct when API mocked to succeed |
| 1.6 | `test_seo.py` | sitemap 200 + 5 URLs; robots.txt Disallow; JSON-LD present; title/desc length |
| 2.1 | `test_permissions.py` | Client sees panel home; Client denied /auth/user/; superuser allowed; New highlight in HTML; wa.me link in detail |
| 2.2 | `test_views.py` + mock | Storage switch by USE_CLOUDINARY; Cloudinary API called when enabled |
| 2.3 | All tests pass | Regression gate |

**No Selenium, no Playwright.** Server-side rendering means Django's `TestClient` is sufficient for all acceptance criteria.

---

## 10. Render + Neon Deployment

### Neon setup

1. Create a Neon project → copy the connection string (postgres://…).
2. Set `DATABASE_URL` in Render env vars.
3. Neon free tier: 0.5 GB storage, 1 compute — sufficient for a small business site.

### Render service configuration

**Build script (`build.sh`):**
```bash
#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download pinned standalone Tailwind CLI binary (not committed to Git)
TAILWIND_VERSION="v3.4.17"
TAILWIND_BIN="./bin/tailwindcss"

mkdir -p bin
if [ ! -f "$TAILWIND_BIN" ]; then
    echo "Downloading Tailwind CSS standalone binary ($TAILWIND_VERSION)..."
    curl -sLO "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-x64"
    mv tailwindcss-linux-x64 "$TAILWIND_BIN"
    chmod +x "$TAILWIND_BIN"
fi

# 3. Build minified production stylesheet
"$TAILWIND_BIN" -i static/css/input.css -o static/css/output.css --minify

# 4. Collect static files and run database migrations
python manage.py collectstatic --no-input
python manage.py migrate
```

**Render Build command:**
```bash
./build.sh
```

**Start command:**
```bash
gunicorn config.wsgi:application --workers 2 --bind 0.0.0.0:$PORT
```

**One-off job (run once after first deploy):**
```bash
python manage.py create_client_group
```

### Tailwind on Render — decision

**Use the standalone Tailwind CLI binary downloaded during `build.sh`.**
- Pinned to version `v3.4.17`.
- Downloaded dynamically during the build step on Render; added to `.gitignore` so the binary is **never committed to Git**.
- Avoids npm/Node.js on Render entirely, eliminating memory overhead and build-time Node issues on free/starter instances.
- Self-contained, ~10 MB Linux executable generating the minified `output.css` before `collectstatic` runs.

Alternative considered: commit `output.css`. Rejected — committed CSS goes stale when templates change and Tailwind classes are added; purging only works at build time.

### Required Render environment variables

All variables from §8 table above, plus:
- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `WEB_CONCURRENCY=2` (gunicorn workers; free tier has 512 MB RAM)
- `PORT` — set automatically by Render

### Health check

Render pings `/` every 30 seconds. The Home view returns 200 in all states (even with an empty Services table). No special health-check endpoint needed.

---

## Alignment with epics.md

All alignment and precision items have been incorporated directly into `epics.md`:

1. **Story 1.1:** Specifies `gunicorn config.wsgi:application` and the standalone Tailwind CLI binary build step.
2. **Story 1.2:** Clarifies that the Home page quote form is markup only with CSRF token (submission logic deferred to Story 1.4), and explicitly specifies per-page SEO metadata (`<title>`, `<meta description>`, `<link rel="canonical">`, single `<h1>`) in AC and tests.
3. **Story 1.3:** Explicitly specifies per-page SEO metadata and tests for Services, Gallery, About, and Contact pages.
4. **Story 1.5:** Explicitly specifies `requests.post` as the mock target for Telegram testing.
5. **Story 2.1:** Uses the accurate Django admin URL `/panel/core/quoterequest/`.
6. **Story 2.2:** Formally specifies Django 5.2 `STORAGES["default"]` configuration switching between Cloudinary and local disk.
7. **Story 2.3:** Includes the warning that Render free-tier staging container restarts lose local-disk uploaded images, and documents `gunicorn config.wsgi:application` and `./build.sh`.

