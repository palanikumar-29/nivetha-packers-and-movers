# Project Handoff: Nivetha Packers and Movers

This document outlines the business context, technical architecture, design decisions, and operating boundaries for developers and AI agents working on this codebase.

---

## 1. Client & Business Context

- **Client**: Nivetha Packers and Movers.
- **Location**: Tiruppur, Tamil Nadu, India.
- **Service Categories**: Household shifting, office relocation, two-wheeler and vehicle transport.
- **Service Coverage**: Tiruppur moves with primary focus, plus moves all over Tamil Nadu.
- **Primary Goals**:
  1. High-speed local SEO ranking for "packers and movers Tiruppur".
  2. Frictionless enquiry capture via phone calls, WhatsApp click-to-chat, and a lightweight web quote form.
  3. Simple, non-technical admin panel for the business owner to manage incoming customer leads and update photos/services.
- **Deal Summary**: Fixed-scope website delivery covering a 5-page responsive public site, an authenticated client management panel, production deploy preparation (Render + Neon), and handoff documentation.

---

## 2. Technical Stack & Architecture

- **Backend Framework**: Django 5.2 (Python 3.12+).
- **Database**:
  - Local development: SQLite 3.
  - Production: Managed PostgreSQL via Neon (serverless).
- **CSS & Design System**: Tailwind CSS v3 (standalone CLI binary without Node.js dependency).
- **Static Assets**: WhiteNoise with compressed manifest storage (`CompressedManifestStaticFilesStorage`).
- **Media Storage**:
  - Local development: Local disk (`FileSystemStorage`).
  - Production: Cloudinary (`MediaCloudinaryStorage`) toggled via `USE_CLOUDINARY`.
- **WSGI Server**: Gunicorn (single worker configuration for 512 MB RAM free tier).
- **Configuration**: `python-decouple` reading environment variables from `.env` locally and dashboard secrets in production.

---

## 3. Repository Folder Map

```
Nivetha-p&m/
├── config/                      # Project configuration & settings
│   ├── settings/
│   │   ├── base.py              # Shared Django settings & context processors
│   │   ├── local.py             # SQLite, DEBUG=True, local media
│   │   └── production.py        # Neon PG, DEBUG=False, SSL redirect, Cloudinary
│   ├── urls.py                  # Root URLconf (pages, custom admin, sitemap, robots)
│   └── wsgi.py                  # WSGI entrypoint with production fallback
├── core/                        # Single application holding all domain logic
│   ├── channels/                # Pluggable notification layer
│   │   ├── __init__.py          # dispatch() router
│   │   └── telegram.py          # Optional Telegram bot notification channel
│   ├── management/commands/     # Custom management commands
│   │   ├── create_client_group.py # Scaffolds Client group permissions
│   │   └── seed_services.py     # Idempotent initial services seeder
│   ├── migrations/              # Database migrations (0001 to 0004)
│   ├── templates/               # Public HTML templates & partials
│   │   ├── partials/            # quote_form.html, intro_animation.html
│   │   ├── base.html            # Main layout, header, footer, bottom bar
│   │   └── home, services, gallery, about, contact, 404.html
│   ├── tests/                   # Test suite (144 automated tests)
│   ├── admin.py                 # Panel configuration & Client group rules
│   ├── context_processors.py    # Business contact, SEO schema, palette context
│   ├── forms.py                 # QuoteForm with honeypot & GalleryImage admin form
│   ├── models.py                # QuoteRequest, Service, GalleryImage, SiteSettings
│   └── views.py                 # Page views & quote submission handler
├── docs/                        # Project handoff, status, and runbook
├── static/css/                  # Tailwind input.css & compiled output.css
├── bin/                         # Local Tailwind standalone executable (gitignored)
├── build.sh                     # Render deployment script
├── render.yaml                  # Render Infrastructure-as-Code blueprint
├── AGENTS.md                    # Standing rules for future AI agents
├── requirements.txt             # Pinned Python package dependencies
└── README.md                    # Developer onboarding & deployment guide
```

---

## 4. User Roles & Admin Permissions

The admin panel is mounted at `ADMIN_URL` (`/panel/` by default; `/admin/` returns 404).

1. **Superuser (`is_superuser=True`)**:
   - Access to full Django admin: Users, Groups, Site Settings (palette & logo), Enquiries, Services, and Gallery.
2. **Client Group (`name='Client'`)**:
   - Designed for the non-technical business owner.
   - Restricted to exactly 10 permissions managed via `python manage.py create_client_group`:
     - `QuoteRequest`: view, change (cannot delete customer records).
     - `Service`: view, add, change, delete.
     - `GalleryImage`: view, add, change, delete.
   - Excluded from: Users, Groups, and Site Settings.
   - Readonly enquiry details protect customer inputs; action button generates pre-filled WhatsApp response link (`wa.me`).

---

## 5. Key Architecture Features

### Pluggable Notification Channels
- Located in `core/channels/`.
- Function `dispatch(enquiry)` runs non-blocking notification channels when a quote request arrives.
- Telegram bot channel activates only when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set.
- Fails gracefully without throwing errors or blocking customer form submissions.

### Palette Presets System
- Two built-in presets: `beige` (warm neutral with rust accents) and `navy` (classic navy with orange buttons).
- Defined via CSS custom properties on `:root[data-palette="..."]` in `static/css/input.css`.
- Both presets support light mode, system dark mode (`prefers-color-scheme`), and manual toggle (`[data-theme="dark"]`).
- Managed dynamically in `/panel/` via the `SiteSettings` singleton model with zero-cost memory caching.
- **How to add a new preset**:
  1. Add `:root[data-palette="<key>"]` light and dark token rules in `static/css/input.css`.
  2. Add `('<key>', '<Label>')` to `PALETTES` in `core/models.py`.
  3. Run `tailwindcss --minify` to recompile `output.css`.

### Opening Animation
- Lightweight Home-page-only intro animation implemented with pure CSS and inline SVG.
- Kept strictly under 4 KB.
- Respects accessibility: automatically disabled if `prefers-reduced-motion` is active or connection has `saveData`.
- Shows once per session using `sessionStorage` (`intro_seen`).
- Provides a visible, keyboard-accessible "Skip" button.

### SEO & Indexing Architecture
- Controlled via `ALLOW_INDEXING` env var:
  - `ALLOW_INDEXING=False` (staging default): returns `Disallow: /` in `robots.txt` and `<meta name="robots" content="noindex, nofollow">` on all pages.
  - `ALLOW_INDEXING=True` (production): advertises `sitemap.xml`, disallows `/panel/`, and allows normal indexing.
- Includes dynamic schema.org `MovingCompany` JSON-LD structured data with telephone, address, and service cities.

### Media & Cloudinary Storage
- Uses Django 5.2 `STORAGES` setting.
- `USE_CLOUDINARY=False` routes uploads to local disk (`media/`), ideal for development and smoke testing.
- `USE_CLOUDINARY=True` uploads images directly to Cloudinary folder `nivetha/gallery`.
- Admin enforces 5 MB file size limit and inspects real binary magic numbers (JPEG, PNG, WebP only).

---

## 6. Architectural Decision Records (ADRs)

| Decision | Rationale |
|---|---|
| Single app (`core`) | Project has 5 public pages and 4 models. Splitting into multiple apps adds maintenance overhead with no tangible benefit. |
| Server-rendered templates (No React/Vue) | Delivers instant First Contentful Paint, perfect Core Web Vitals, and effortless indexing for local search crawlers. |
| Standalone Tailwind CLI binary | Eliminates Node.js, `npm`, and `package.json` dependencies from Python runtime containers. |
| Neon serverless PostgreSQL | Free tier includes compute auto-suspend and automatic storage branching for production database reliability. |
| WhatsApp link (`wa.me`) over complex CRM | Direct mobile chat aligns with how moving quotes are negotiated and booked in Tamil Nadu. |

---

## 7. Strict "Do Not Do" Boundaries

1. **Do NOT introduce frontend JS frameworks** (React, Vue, Svelte, Next.js). Keep templates server-rendered.
2. **Do NOT use SMTP email sending on Render free tier** (outbound port 25/465/587 is frequently blocked or rate-limited; use WhatsApp or Telegram).
3. **Do NOT deploy this project to Vercel** (Vercel is tailored for Node/serverless; Render web services handle persistent Gunicorn + WSGI cleanly).
4. **Do NOT invent marketing claims**: Never state unverified facts, years in business, or unserved cities (strictly avoid words like `regular`, `reliable`, `trusted`, `fast`, `experienced`, `years`, `guaranteed`, `free quote`, `no hidden charges`, `Coimbatore`, `Chennai`, `Madurai`).
