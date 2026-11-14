---
status: draft
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-Nivetha-pm-2026-10-30/prd.md
---

# Nivetha Packers and Movers — Epic Breakdown

## Overview

Two epics, nine stories. Fixed stack: Django + Tailwind CSS CLI + PostgreSQL/Neon (prod) / SQLite (local) + Render + gunicorn + whitenoise. No architecture doc yet; implementation decisions within the stack belong to the developer.

**Story dependency order within each epic must be respected.** Story 1.2 depends on 1.1 (models exist). Story 1.3 depends on 1.2 (base layout exists). Gallery uses local disk storage until Story 2.2 adds Cloudinary.

---

## Requirements Inventory

### Functional Requirements

FR-1: Every public page (/, /services/, /gallery/, /about/, /contact/) returns HTTP 200 and passes mobile-friendliness checks (no horizontal scroll, tap targets ≥ 44 px).
FR-2: Each page has a unique <title> (≤ 60 chars), <meta description> (≤ 160 chars), one <h1>, and a <link rel="canonical"> with local keywords.
FR-3: On viewports ≤ 768 px, fixed Call (tel:) and WhatsApp (wa.me) buttons are visible on every page without obscuring primary content.
FR-4: Home page renders: hero with highway-sign route board + CTA, active Services summary (from DB), how-a-move-works steps, embedded Quote form.
FR-5: Quote form validates phone (10-digit Indian mobile, starts 6–9) and preferred date (today or future). Invalid submissions return inline errors. Valid submissions save Enquiry with status=New.
FR-6: A hidden honeypot field rejects bot submissions silently (fake success returned, no Enquiry saved).
FR-7a: New Enquiries are visually highlighted in the /panel/ enquiry list. Each Enquiry detail shows a pre-filled "WhatsApp customer" wa.me link. (Owned by Story 2.1)
FR-7b: A pluggable channels layer fires after a valid Enquiry is saved. Telegram channel fires only when TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID are set; silently skipped otherwise. All channel failures are caught, logged, and never surface to the visitor. (Owned by Story 1.5)
FR-8: Client user (staff, "Client" group) sees only Enquiries, Services, Gallery in /panel/. Cannot access Users, Groups, or settings.
FR-9: Client user can change Enquiry Status (New → Called → Confirmed → Closed) and add internal notes. Status change saved with timestamp.

### Non-Functional Requirements

NFR-1: Stack — Django (Python), Tailwind CSS via CLI (not CDN), PostgreSQL/Neon in prod, SQLite locally, Render + gunicorn + whitenoise. No React, no separate API.
NFR-2: Security — No secrets in Git (.env via python-decouple). DEBUG=False in prod. HTTPS redirect. Secure cookies. Admin only at /panel/.
NFR-3: Images — Gallery uploads to Cloudinary (free tier) in prod (Story 2.2). Local dev uses local disk storage (Story 1.1 onwards). USE_CLOUDINARY env var switches storage. Credentials never hardcoded.
NFR-4: Phone/WhatsApp — BUSINESS_PHONE and BUSINESS_WHATSAPP read from env vars. Placeholders in code and tests. Never hardcoded.
NFR-5: Performance — whitenoise for static files. Tailwind purged in prod. Images lazy-loaded. Target < 3 s LCP on mid-range Android/4G.
NFR-6: Accessibility — WCAG 2.1 AA colour contrast. Semantic HTML (nav, main, section, footer).
NFR-7: SEO — sitemap.xml, robots.txt (blocks /panel/), LocalBusiness + MovingCompany JSON-LD schema on Home.
NFR-8: Content — no invented facts; placeholder text clearly marked.
NFR-9: Config — all env-specific values via python-decouple + dj-database-url.
NFR-10: Tests — every story must have tests written and passing before it is considered done.
NFR-11: README — local setup and Render + Neon deployment docs, including staging deploy verification.

### Additional Requirements

- Management command `create_client_group` sets up Client group permissions programmatically.
- Tailwind CSS built via CLI (build step); output collected by whitenoise — not CDN.
- Gallery uses local disk storage from Story 1.1 through Story 2.1; Cloudinary added in Story 2.2.
- BUSINESS_PHONE and BUSINESS_WHATSAPP must never be hardcoded anywhere.
- Telegram is optional and off by default. Owner does NOT use Telegram. No bot setup required.

### UX Design Requirements

No UX design document exists. Direction from PRD:
- Road-sign theme: dark asphalt background, highway-green + signal-amber accents.
- Condensed display font for headings; plain readable body font.
- Hero: highway-sign route board "Tiruppur: Within Tiruppur, Across Tamil Nadu" — the single memorable element.
- Mobile-first; quiet, clear, readable on small screens.

### FR Coverage Map

| FR | Story |
|----|-------|
| FR-1 | 1.2, 1.3 |
| FR-2 | 1.2, 1.3 |
| FR-3 | 1.2 (base layout) |
| FR-4 | 1.2 (Home) |
| FR-5 | 1.4 |
| FR-6 | 1.4 |
| FR-7a (panel highlighting + wa.me) | 2.1 |
| FR-7b (channels layer) | 1.5 |
| FR-8 | 2.1 |
| FR-9 | 2.1 |
| NFR-3 (Cloudinary) | 2.2 |
| NFR-7 (SEO infra) | 1.6 |
| NFR-10 (Tests) | Every story |
| NFR-11 (README + staging) | 2.3 |

---

## Epic List

- **Epic 1: Public Website** — Project foundation, data models, five public pages, quote form, channels layer, SEO.
- **Epic 2: Owner Tools** — Client panel (enquiry management with highlighting + wa.me, services, gallery), Cloudinary, README + staging deploy.

---

## Epic 1: Public Website

### Story 1.1: Django Project Foundation and Data Models

As a developer,
I want a working Django project with the correct stack, settings, and data models,
So that all subsequent stories can build on a solid, deployable base with real database tables.

**Acceptance Criteria:**

**Given** a fresh clone with a populated `.env` (copied from `.env.example`)  
**When** I run `python manage.py migrate` then `python manage.py runserver`  
**Then** Django serves a placeholder page at `http://localhost:8000/` with HTTP 200 and connects to SQLite.

**Given** `DATABASE_URL` is set to a Neon PostgreSQL connection string  
**When** the app starts  
**Then** Django connects to PostgreSQL with no code change.

**Given** `DEBUG=False` and an HTTP request  
**When** processed by Django  
**Then** the request is redirected to HTTPS (`SECURE_SSL_REDIRECT=True`); secure cookie flags are set.

**Given** Tailwind CSS CLI is configured as a build step  
**When** the standalone Tailwind CLI binary is run (e.g. via `build.sh`)  
**Then** a minified, purged `output.css` is produced in the static files directory and is collected by `whitenoise`.

**Given** gunicorn and whitenoise are installed  
**When** `gunicorn config.wsgi:application` runs  
**Then** the app starts and static files are served without a separate CDN.

**Given** the three data models are defined: QuoteRequest, Service, GalleryImage  
**When** `python manage.py migrate` runs  
**Then** the corresponding tables are created in the database with all fields specified in the PRD data model section (QuoteRequest: name, phone, move_type, moving_from, moving_to, preferred_date, details, status=New, notes, created_at, status_updated_at; Service: title, description, order, is_active; GalleryImage: image, caption, is_active).

**Given** `GalleryImage.image` uses Django's default `ImageField` with `MEDIA_ROOT` local storage  
**When** an image is uploaded in the admin  
**Then** it is saved to local disk — no Cloudinary required until Story 2.2.

**Given** `BUSINESS_PHONE` and `BUSINESS_WHATSAPP` are absent from the environment  
**When** the app starts  
**Then** it starts without error (safe defaults or empty strings; templates render without crashing).

**Tests written and passing:**
- A test that runs `migrate` and confirms all three model tables exist.
- A test that creates a `Service` record and reads it back.
- A test that creates a `QuoteRequest` record with `status=New` and reads it back.

**Scope note:** No public-facing pages yet beyond the placeholder. No Tailwind design. Just: Django project skeleton, settings split (base/local/prod), three models + migrations, gunicorn + whitenoise, Render build/start config documented, `.env.example` with all vars listed.

---

### Story 1.2: Base Layout and Home Page

As a public visitor,
I want to see a well-designed, mobile-friendly Home page with the brand identity and all its content blocks,
So that I immediately understand what the business does and how to contact them.

**Acceptance Criteria:**

**Given** a request to `/`  
**When** the server responds  
**Then** HTTP 200 is returned with valid HTML containing exactly one `<h1>`, a unique `<title>` (≤ 60 chars), a `<meta name="description">` (≤ 160 chars), and a `<link rel="canonical" href="https://{domain}/">`.

**Given** the base layout template  
**When** any public page renders  
**Then** it includes: `<nav>`, `<main>`, `<footer>` semantic elements; floating Call button linking to `tel:{BUSINESS_PHONE}`; floating WhatsApp button linking to `https://wa.me/{BUSINESS_WHATSAPP}` — both visible and tappable on mobile (≤ 768 px) without obscuring primary content; no phone number hardcoded in templates or Python.

**Given** the Home page  
**When** it renders  
**Then** it contains all four content blocks: (1) hero section with the highway-sign route board showing "Tiruppur", "Within Tiruppur", and "Across Tamil Nadu" and a primary CTA button; (2) active Services summary drawn from the Service table; (3) "how a move works" steps section; (4) the embedded Quote form markup.

**Given** the embedded Quote form on the Home page  
**When** it renders  
**Then** the form fields, labels, and CSRF token are rendered as markup only; form submission processing, server-side validation, and DB save are deferred to Story 1.4 (form action may point to `/contact/`).

**Given** the design direction  
**When** any page using the base layout renders  
**Then** the page applies: dark asphalt background colour, highway-green and signal-amber accents, a condensed display font for headings, a plain readable body font.

**Given** a mobile viewport (375 px wide)  
**When** the Home page renders  
**Then** there is no horizontal scroll and all interactive elements have tap targets ≥ 44 px.

**Given** `BUSINESS_PHONE` and `BUSINESS_WHATSAPP` are set as env vars  
**When** the floating buttons render  
**Then** they contain the correct `tel:` and `wa.me` values; no number is hardcoded.

**Tests written and passing:**
- `GET /` returns HTTP 200.
- Response contains exactly one `<h1>`.
- Response contains unique `<title>` (length ≤ 60 chars) and unique `<meta name="description">` (length ≤ 160 chars).
- Response contains `<link rel="canonical" href="https://{domain}/">`.
- Response contains `<nav>` and `<footer>`.
- Response contains Quote form HTML markup with CSRF token.
- Response does not contain any hardcoded phone number (assert against known placeholder values).

---

### Story 1.3: Services, Gallery, About, and Contact Pages

As a public visitor,
I want to browse the Services, Gallery, About, and Contact pages,
So that I can learn about the business in detail and reach the quote form from multiple entry points.

**Acceptance Criteria:**

**Given** each of `/services/`, `/gallery/`, `/about/`, `/contact/`  
**When** requested  
**Then** each returns HTTP 200, uses the base layout from Story 1.2, has exactly one `<h1>`, a unique `<title>` (≤ 60 chars), a `<meta name="description">` (≤ 160 chars), and a `<link rel="canonical">` with the correct URL.

**Given** the Services page  
**When** it renders  
**Then** it lists all Service records where `is_active=True`, ordered by `order`. Each service shows its title and description.

**Given** the Gallery page  
**When** it renders  
**Then** it shows all GalleryImage records where `is_active=True`. Each image has `loading="lazy"` and a non-empty `alt` attribute equal to the caption. Local disk storage is used (Cloudinary not required yet).

**Given** the About page  
**When** it renders  
**Then** it contains placeholder text only — no invented facts (no specific years of experience, no invented customer counts, no fabricated awards).

**Given** the Contact page  
**When** it renders  
**Then** it includes the Quote form (submission handled in Story 1.4) and a visible phone/WhatsApp contact option.

**Given** local keywords (Tiruppur, Tamil Nadu)  
**When** the Services and Contact pages render  
**Then** they appear naturally in at least one heading or paragraph on each page.

**Given** a mobile viewport (375 px wide)  
**When** any of the four pages renders  
**Then** there is no horizontal scroll and tap targets are ≥ 44 px.

**Tests written and passing:**
- `GET /services/` → HTTP 200.
- `GET /gallery/` → HTTP 200.
- `GET /about/` → HTTP 200.
- `GET /contact/` → HTTP 200.
- Each of the four pages contains exactly one `<h1>`.
- Each of the four pages contains unique `<title>` (≤ 60 chars) and unique `<meta name="description">` (≤ 160 chars).
- Each of the four pages contains `<link rel="canonical">` matching its URL.
- Services page with two active + one inactive Service in DB → response contains two service titles, not the inactive one.
- Gallery page with one active GalleryImage → response contains `loading="lazy"` and the image caption as alt text.

---

### Story 1.4: Quote Form — Validation, Spam Protection, and Save

As a public visitor,
I want to submit a quote request easily from my phone,
So that the business receives my enquiry accurately and I get immediate confirmation.

**Acceptance Criteria:**

**Given** the Quote form on `/contact/` or `/`  
**When** I submit with valid fields: 10-digit Indian mobile (starts 6–9), move type, moving from, moving to, and an optional future preferred date  
**Then** an Enquiry is saved to the database with `status=New` and the visitor sees a success confirmation message.

**Given** the Quote form  
**When** I submit with a phone number that is not 10 digits or does not start with 6–9  
**Then** the form re-renders with an inline error on the phone field; zero Enquiries are saved.

**Given** the Quote form  
**When** I submit with a preferred date in the past  
**Then** the form re-renders with an inline error on the date field; zero Enquiries are saved.

**Given** the Quote form  
**When** I submit with the required fields missing (name, phone, move_type, moving_from, moving_to)  
**Then** the form re-renders with inline errors on each missing required field; zero Enquiries are saved.

**Given** a bot submission where the hidden honeypot field is non-empty  
**When** the form is submitted  
**Then** the server returns a fake success response; zero Enquiries are saved and no exception is raised.

**Given** a browser with JavaScript disabled  
**When** the form is submitted  
**Then** CSRF protection is active and all server-side validation still applies.

**Tests written and passing:**
- Valid submission → HTTP redirect/200, one Enquiry in DB with `status=New`.
- Bad phone (e.g. 8 digits) → form re-rendered, zero Enquiries in DB.
- Past preferred date → form re-rendered, zero Enquiries in DB.
- Missing required field → form re-rendered, zero Enquiries in DB.
- Honeypot non-empty → fake success response, zero Enquiries in DB.
- CSRF token absent → HTTP 403.

---

### Story 1.5: Pluggable Notification Channels Layer

As a developer,
I want a channels layer that fires after each new Enquiry is saved,
So that owner notifications can be added or changed without touching the form view or save logic.

**Acceptance Criteria:**

**Given** a valid Enquiry is saved and `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are not set  
**When** the channels layer runs  
**Then** the visitor sees the success page; the Telegram channel is silently skipped; no exception propagates; an INFO or DEBUG log entry is recorded.

**Given** a valid Enquiry is saved and `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set but the Telegram API is unreachable (mocking `requests.post` to raise a connection error)  
**When** the channels layer runs  
**Then** the visitor still sees the success page; the failure is logged at ERROR level; no exception propagates.

**Given** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set and the Telegram API responds successfully (mocking `requests.post` to return HTTP 200)  
**When** a valid Enquiry is saved  
**Then** a Telegram message is sent via `requests.post` containing: customer name, phone, move type, moving from, moving to, and preferred date (if supplied).

**Given** any channel raises an unexpected exception  
**When** the channels layer handles it  
**Then** the exception is caught, logged at ERROR level, and the visitor's HTTP response is unaffected.

**Given** a developer wants to add a new channel (e.g. WhatsApp Business API) in a future story  
**When** they look at the channels layer  
**Then** adding a new channel requires only creating a new channel module and registering it — no changes to the form view or Enquiry save logic.

**Tests written and passing:**
- Channel layer called with Telegram vars unset → no exception; mock confirms no HTTP call made to Telegram API.
- Channel layer called with Telegram vars set, `requests.post` mocked to raise `requests.exceptions.ConnectionError` → no exception; ERROR logged.
- Channel layer called with Telegram vars set, `requests.post` mocked to return HTTP 200 → mock confirms `requests.post` called with correct payload (name, phone, move type).

---

### Story 1.6: SEO Infrastructure

As the business owner,
I want the site to be discoverable on Google for local search terms,
So that people searching "packers and movers Tiruppur" find the business.

**Acceptance Criteria:**

**Given** a request to `/sitemap.xml`  
**When** the server responds  
**Then** it returns HTTP 200 with a valid XML sitemap listing all five public page URLs (`<loc>`) with `<lastmod>` dates. No `/panel/` URL is present.

**Given** a request to `/robots.txt`  
**When** the server responds  
**Then** it returns HTTP 200 with plain text that: allows all crawlers on public pages and contains `Disallow: /panel/`.

**Given** the Home page  
**When** it renders  
**Then** a `<script type="application/ld+json">` block is present with a valid `LocalBusiness` + `MovingCompany` JSON-LD schema containing: `"name": "Nivetha Packers and Movers"`, `"address"` with `"addressLocality": "Tiruppur"` and `"addressRegion": "Tamil Nadu"`, `"telephone"` from `BUSINESS_PHONE` env var, and `"areaServed"` including Tiruppur and Tamil Nadu.

**Given** any public page's `<title>` and `<meta name="description">`  
**When** their lengths are checked  
**Then** title is ≤ 60 characters and description is ≤ 160 characters on every page.

**Tests written and passing:**
- `GET /sitemap.xml` → HTTP 200, response contains all five public URLs.
- `GET /robots.txt` → HTTP 200, response contains `Disallow: /panel/`.
- `GET /` → response contains `application/ld+json` and `"MovingCompany"`.
- `GET /` → `<title>` length ≤ 60 chars.
- Each of the five pages → assert `<meta name="description">` length ≤ 160 chars.

---

## Epic 2: Owner Tools

### Story 2.1: Client Panel — Enquiry Management with Highlighting and wa.me, Services, Gallery

As the business owner (Client user),
I want a mobile-friendly admin panel restricted to my data, with clear highlighting of new enquiries and one-tap WhatsApp links,
So that I never miss a lead and can follow up immediately from my phone.

**Acceptance Criteria:**

**Given** the Django admin is mounted at `/panel/`  
**When** a browser requests `/admin/`  
**Then** it returns HTTP 404 (not found; the default admin URL is removed).

**Given** the management command `create_client_group` is run  
**When** it completes  
**Then** a Django group named "Client" exists with exactly these permissions: view+change QuoteRequest; add+change+delete+view Service; add+change+delete+view GalleryImage — and no other model permissions.

**Given** a staff user in the "Client" group logs in to `/panel/`  
**When** they view the panel home  
**Then** they see only three model sections: Enquiries, Services, Gallery. No Users, Groups, LogEntry, or any other app sections are visible.

**Given** a staff user in the "Client" group is authenticated  
**When** they request `/panel/auth/user/` or `/panel/auth/group/`  
**Then** they receive HTTP 403 (or are redirected to the panel login page, effectively denied).

**Given** a superuser logs in to `/panel/`  
**When** they view the panel home  
**Then** they see all Django admin sections (full superuser access is unchanged).

**Given** one or more Enquiries with `status=New` exist  
**When** a Client user views the Enquiries list in `/panel/`  
**Then** those rows are visually distinct from non-New rows (e.g. amber row background or badge); the visual distinction is present in the rendered HTML.

**Given** a Client user opens an Enquiry detail  
**When** they view the page  
**Then** they can: change Status via a dropdown (New / Called / Confirmed / Closed); add/edit an internal notes field; see a "WhatsApp customer" link rendered as `https://wa.me/{enquiry.phone}?text=…` pre-filled with the customer name and move summary. The wa.me link is a tappable anchor tag.

**Given** a Client user submits a Status change  
**When** saved  
**Then** the new Status and a `status_updated_at` timestamp are persisted in the database.

**Tests written and passing:**
- Client user `GET /panel/` → HTTP 200; response contains "Enquiries"; response does NOT contain "Users".
- Client user `GET /panel/auth/user/` → HTTP 403 or redirect to login.
- Client user `GET /panel/auth/group/` → HTTP 403 or redirect to login.
- Superuser `GET /panel/auth/user/` → HTTP 200.
- Enquiry list with one `status=New` enquiry → response HTML contains the amber highlight class or badge element.
- Enquiry detail → response HTML contains a `wa.me` anchor tag with the correct phone number.
- Status change from New to Called → DB record updated; `status_updated_at` is not null.
- `create_client_group` command → "Client" group exists; Client user with that group cannot access `/panel/auth/user/`; a fresh Client user can access `/panel/core/quoterequest/`.

---

### Story 2.2: Cloudinary Image Uploads for Gallery

As the business owner,
I want gallery photos to survive Render deploy restarts,
So that uploaded images are never lost when the container is replaced.

**Acceptance Criteria:**

**Given** `USE_CLOUDINARY=true` and valid Cloudinary credentials (`CLOUDINARY_URL` or `CLOUDINARY_CLOUD_NAME` + `CLOUDINARY_API_KEY` + `CLOUDINARY_API_SECRET`) are set  
**When** a Client user uploads an image via the Gallery admin  
**Then** `STORAGES["default"]` uses `cloudinary_storage.storage.MediaCloudinaryStorage`, the image is stored in Cloudinary, and `GalleryImage.image` stores the Cloudinary URL or public ID.

**Given** `USE_CLOUDINARY=false` or the var is absent  
**When** a Client user uploads an image via the Gallery admin  
**Then** `STORAGES["default"]` falls back to `django.core.files.storage.FileSystemStorage`, and the image is saved to local disk (`MEDIA_ROOT`) — suitable for local development.

**Given** a GalleryImage with `is_active=True` is stored in Cloudinary  
**When** the Gallery public page renders  
**Then** the image tag uses the Cloudinary-served URL, includes `loading="lazy"`, and has a non-empty `alt` attribute equal to the caption.

**Given** Cloudinary credentials are missing or incorrect  
**When** an upload is attempted  
**Then** Django raises a validation error or the admin shows a clear error message; the site does not crash and no traceback is exposed to the user.

**Given** a `.env.example` file  
**When** a developer reads it  
**Then** it documents all required env vars with comments and safe placeholders: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`, `USE_CLOUDINARY`, `CLOUDINARY_URL` (or the three separate vars), `BUSINESS_PHONE`, `BUSINESS_WHATSAPP`, `TELEGRAM_BOT_TOKEN` (optional), `TELEGRAM_CHAT_ID` (optional).

**Tests written and passing:**
- With `USE_CLOUDINARY=false`: upload a test image → file exists under `MEDIA_ROOT`; `GalleryImage.image` is a local path.
- With `USE_CLOUDINARY=true` and Cloudinary mocked: upload attempt → mock confirms the Cloudinary upload API was called.
- Gallery public page with Cloudinary-stored image (URL mocked): response contains `loading="lazy"` and the caption as `alt`.

---

### Story 2.3: README, Deployment Docs, and Staging Verification

As a developer,
I want clear setup and deployment instructions and a verified working staging environment,
So that any developer can run the project locally and deploy to Render + Neon without guessing.

**Acceptance Criteria:**

**Given** a developer clones the repo and reads `README.md`  
**When** they follow the local setup section step by step  
**Then** they can: create a virtualenv, install dependencies from `requirements.txt`, copy `.env.example` to `.env`, run `python manage.py migrate`, run `python manage.py create_client_group`, run the Tailwind CSS build step, and run `python manage.py runserver` — reaching a working site at `http://localhost:8000/`.

**Given** a developer reads the Render + Neon deployment section  
**When** they follow it  
**Then** they know: how to create a Neon PostgreSQL database and copy the connection string to `DATABASE_URL`; what all required env vars are and where to enter them in the Render dashboard; what the Render build command is (`./build.sh` which installs deps, downloads standalone Tailwind CLI, builds CSS, runs `collectstatic` and `migrate`); what the Render start command is (`gunicorn config.wsgi:application` with worker count); how to run `create_client_group` as a one-off Render job after first deploy.

**Given** a staging environment on Render free tier + Neon free tier is configured with all env vars  
**When** the staging deploy completes  
**Then** ALL of the following pass (verified manually or by a smoke-test script):
  - All five public pages (`/`, `/services/`, `/gallery/`, `/about/`, `/contact/`) return HTTP 200.
  - Submitting the quote form saves an Enquiry to the Neon database (verified in `/panel/`).
  - `/panel/` login works for both a superuser and a Client user; Client user sees only Enquiries, Services, Gallery.
  - `/sitemap.xml` and `/robots.txt` return HTTP 200 with correct content.
  - Static files (CSS, fonts) load correctly (no 404s for static assets).

**Given** the README  
**When** a developer reads the storage instructions  
**Then** it explicitly notes: "Staging uses local disk storage (`USE_CLOUDINARY=false`); uploaded images on Render free-tier will disappear when the container restarts. This is expected. Production uses Cloudinary (`USE_CLOUDINARY=true`)." And: "Telegram notifications are optional. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` only if you want them. The site works without them."

**Tests written and passing:**
- All existing tests from Stories 1.1–2.2 pass.
- (Optional) A smoke-test script or `curl` sequence is documented in the README that verifies the five pages and form submission on the staging URL.

---

### Story 2.4: Palette Presets

As a site administrator,
I want to switch the website color scheme between ready-made presets without code changes,
So that we can refresh or adjust the site branding easily while preserving WCAG AA contrast and theme support.

**Acceptance Criteria:**

**Given** the CSS stylesheets and theme token definitions  
**When** inspecting `:root[data-palette="navy"]` and `:root[data-palette="beige"]`  
**Then** both define the full set of shared tokens (page, alternate, surface, lines, headings, body, muted, header, footer, button primary, button secondary, focus ring, intro overlay colors); route board green stays `#0B6B3A` across all presets; and dark variants are provided for both system dark mode (`prefers-color-scheme`) and explicit `data-theme="dark"`.

**Given** the `SiteSettings` singleton model in `core`  
**When** reading or updating `palette`  
**Then** it allows selecting from predefined palette choices (`beige`, `navy`), defaults to `SITE_PALETTE` env var (default `"beige"`), enforces a single row, and prevents row deletion.

**Given** the `palette_context` context processor and `base.html`  
**When** any public page (`/`, `/services/`, `/gallery/`, `/about/`, `/contact/`) is requested  
**Then** the `<html>` root element renders `data-palette="<active_palette>"` server-side with zero layout shift or flash; unknown values safely fall back to the default palette.

**Given** the `/panel/` administration interface  
**When** a superuser accesses the admin  
**Then** they can view and update the `Site settings` palette dropdown with helpful description text; creating duplicate rows or deleting the row is prevented.

**Given** a Client staff user logged into `/panel/`  
**When** viewing the admin index or attempting direct URL access to Site settings  
**Then** `Site settings` is hidden and permission is denied; the Client group permissions remain strictly limited to the required 10 permissions.

**Given** the WCAG AA contrast requirements  
**When** computing contrast ratios for each preset in light and dark variants  
**Then** text elements achieve ≥ 4.5:1 contrast against their backgrounds and UI components (focus rings, button borders) achieve ≥ 3:1 contrast.

**Given** the opening animation on the Home page  
**When** the intro plays in either preset  
**Then** all overlay elements, SVG components, and Skip buttons use the active preset's CSS tokens without hardcoded hex values outside token definitions.

**Tests written and passing:**
- Default palette matches `SITE_PALETTE` env var or defaults to `"beige"`.
- Switching palette via `SiteSettings` updates `data-palette` attribute across all five public pages.
- Unknown or invalid palette values fall back safely to default.
- Singleton behavior: `SiteSettings` cannot have a second row created or be deleted.
- Permissions: Superuser can manage Site settings; Client user cannot view, add, change, or delete Site settings.
- Group permissions: `Client` user group retains exactly 10 permissions.
- Contrast verification: Test asserts WCAG AA ratios (≥ 4.5:1 text, ≥ 3:1 UI borders) for all presets in light and dark themes.
- No hardcoded hex values outside token definitions in templates.
