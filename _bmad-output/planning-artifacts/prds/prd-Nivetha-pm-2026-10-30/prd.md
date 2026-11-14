---
title: Nivetha Packers and Movers — Business Website
status: draft
created: 2026-10-30
updated: 2026-10-30 (rev 1 — notification model, cloud storage, phone vars, hosting confirmed)
---

# PRD: Nivetha Packers and Movers Website

## 0. Document Purpose

This PRD is for the PM, the architect (Winston), and the developer (Amelia). It covers a five-page marketing and lead-capture website for a small packers-and-movers business in Tiruppur, Tamil Nadu. The tech stack is fixed (Django + Tailwind + PostgreSQL/Neon + Render). Scope is intentionally tight — two goals, five pages, eight stories, no enterprise features. This document's vocabulary is anchored in §3 Glossary; all downstream artifacts must use those terms verbatim.

--- 

## 1. Vision

Nivetha Packers and Movers needs to be findable when someone in Tiruppur searches Google for moving help, and then immediately capture that person's interest as a phone call, WhatsApp message, or quote request — before they tap the next result. Today the business has no web presence. A search-optimised, mobile-first site with frictionless contact options fills that gap.

The site is not a booking platform, a portal, or a catalogue. It is a trust-building handshake: here is who we are, here is what we do, here is how to reach us — right now, from your phone. Every design and engineering decision should serve that single purpose.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **Find a trusted mover quickly** — someone relocating in or from Tiruppur searches on a phone in 5 minutes and needs to feel confident enough to call or send a message.
- **Request a quote without friction** — visitor wants to describe their move and get a response from the business without creating an account or downloading an app.
- **Owner: know about every lead the moment it arrives** — the business owner must not miss an enquiry, even if they are away from a computer.

### 2.2 Key User Journeys

- **UJ-1. Ravi requests a quote from his phone.**
  Ravi, a salaried employee relocating within Tiruppur, searches "packers and movers Tiruppur" on his phone. He taps the result, scans the hero, sees the highway-sign route board, reads "Tiruppur: Within Tiruppur, Across Tamil Nadu" and knows this is local. He taps the floating WhatsApp button. Alternatively, he scrolls to the quote form, fills in name, phone, "house move", from/to, and submits. He sees a confirmation message. **Edge case:** if he enters a past date, the form rejects it inline and explains why.

- **UJ-2. Owner Nivetha receives and acts on an enquiry.**
  Nivetha is on-site supervising a move. Her phone buzzes with a Telegram message: "New enquiry — Ravi, 9xxxxxxxx, House move, Tiruppur, 15 Nov." She calls him back within minutes. Later at home she opens `/panel/`, finds the enquiry, marks it "Called", adds a note.

- **UJ-3. A searcher validates the business before calling.**
  A first-time visitor reads the Services page, browses Gallery photos, and reads the About page. Nothing is fabricated; all content is accurate or clearly placeholder. They tap the floating Call button.

---

## 3. Glossary

- **Enquiry** — a QuoteRequest record submitted through the contact form; has a Status.
- **Status** — one of: New, Called, Confirmed, Closed. Applied to an Enquiry by the Client user.
- **Client user** — the business owner; a Django staff user in the "Client" group with restricted panel access.
- **Panel** — the Django admin interface mounted at `/panel/` (not `/admin/`).
- **Quote form** — the HTML form on the Contact page (and embedded on Home) that captures an Enquiry.
- **Notification** — a message dispatched through the pluggable channels layer after a new Enquiry is saved. In this phase: admin panel highlighting only; Telegram is optional via env vars. Email and WhatsApp Business API are out of scope for this phase.
- **Floating buttons** — fixed-position Call and WhatsApp action buttons visible on mobile on every page.
- **Service** — a record with title, description, display order, and active flag; managed by the Client user.
- **GalleryImage** — a record with an uploaded image, caption, and active flag; managed by the Client user.

---

## 4. Features

### 4.1 Public Five-Page Site

**Description:** Five server-rendered Django template pages — Home, Services, Gallery, About, Contact — each with a unique `<title>` and `<meta description>`, one `<h1>`, a canonical `<link>`, and semantic HTML. Pages are mobile-first via Tailwind CSS (built locally with the Tailwind CLI, not CDN). Images use `loading="lazy"` and descriptive `alt` text. The visual theme is road-sign inspired: dark asphalt background, highway green and signal amber accents, a condensed display font for headings. The hero on Home contains a highway-sign style route board (e.g. "Tiruppur: Within Tiruppur, Across Tamil Nadu") as the one memorable design element.

Floating Call and WhatsApp buttons appear on every page on mobile viewports. They link to `tel:` and `https://wa.me/` respectively.

**Functional Requirements:**

#### FR-1: Page rendering and HTTP 200
Every public page (`/`, `/services/`, `/gallery/`, `/about/`, `/contact/`) returns HTTP 200 and passes a basic mobile-friendliness check (no horizontal scroll, tap targets ≥ 44 px).

#### FR-2: Per-page SEO metadata
Each page has a unique `<title>` (≤ 60 chars), `<meta name="description">` (≤ 160 chars), one `<h1>`, and a `<link rel="canonical">`. Local keywords (Tiruppur, Tamil Nadu) appear naturally in headings and copy.

#### FR-3: Floating contact buttons
On viewports ≤ 768 px, a fixed Call button (`tel:`) and a fixed WhatsApp button (`https://wa.me/`) are visible and tappable on every page. They do not obstruct primary content.

#### FR-4: Home page content blocks
Home page renders: hero with CTA, services summary (pulls active Services from DB), how-a-move-works steps, and the Quote form. The highway-sign route board is present in the hero.

---

### 4.2 Quote Form and Enquiry Capture

**Description:** A Django form on `/contact/` (and embedded on `/`) captures Enquiries. Fields: name, phone (Indian mobile, validated), move type (house / office / vehicle / other), moving from, moving to, preferred date (optional, must be today or future), details (optional). CSRF protection is enabled. A honeypot field (hidden via CSS) rejects any submission that fills it. On valid submission the Enquiry is saved to the database, then a Notification is dispatched through a pluggable channels layer. Channel failures are caught, logged at ERROR level, and never surfaced to the visitor — the visitor always sees a success message.

**Notification channels (this phase):**
- **Admin panel** — "New" Enquiries are visually highlighted in the panel list. Each Enquiry detail page shows a one-tap "WhatsApp customer" link (`wa.me/?text=…`) pre-filled with the customer's name and phone.
- **Telegram (optional)** — activated only when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars are set. Off by default. The channels layer checks for their presence at startup.
- **Email** — out of scope for this phase (Render free tier blocks outbound SMTP ports).
- **WhatsApp Business Cloud API** — future story, not in this phase.

**Functional Requirements:**

#### FR-5: Enquiry save and validation
System validates: phone matches a 10-digit Indian mobile pattern; if preferred date is supplied, it is today or later. Invalid submissions return the form with inline errors. Valid submissions save an Enquiry with `status=New`.

#### FR-6: Spam protection
A hidden honeypot field (`id="website"` or similar) is present. Any submission where that field is non-empty is silently discarded (returns a fake success page to the spammer).

#### FR-7: Owner notification via pluggable channels
After a valid Enquiry is saved, the system dispatches notifications through a channels layer:
- **Admin panel** — New Enquiries appear highlighted (e.g. amber badge) in the `/panel/` enquiry list. Each Enquiry detail shows a pre-filled `wa.me` link: "WhatsApp customer" opens WhatsApp with the customer's name and phone pre-populated.
- **Telegram (optional)** — if `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, a message is sent via Bot API. If either var is absent, the channel is silently skipped.
- All channel calls are wrapped in try/except; any failure is logged at ERROR level and does not affect the visitor's response.

**Consequences (testable):**
- Submitting a valid enquiry with Telegram vars unset → visitor sees success, no exception raised, error logged at most.
- Submitting a valid enquiry with Telegram vars set but bot unreachable → visitor still sees success; error logged.
- New enquiry appears with visual highlight in `/panel/` enquiry list.
- Enquiry detail page contains a rendered `wa.me` link with customer phone number.

---

### 4.3 Client Panel

**Description:** The Django admin is re-mounted at `/panel/` (the default `/admin/` path is removed or redirected to 404). A management command `create_client_group` sets up a "Client" Django group with permissions: view/change QuoteRequest, view/change/add/delete Service, view/change/add/delete GalleryImage. Client users cannot see Users, Groups, or site Settings in the panel.

**Functional Requirements:**

#### FR-8: Restricted panel access
A staff user in the "Client" group who logs in to `/panel/` sees only: Enquiries (list + detail with status dropdown and notes field), Services (list + add/edit), Gallery (list + add/edit with image upload). They cannot navigate to Users, Groups, or any other app.

#### FR-9: Enquiry status management
The Client user can change an Enquiry's Status (New → Called → Confirmed → Closed) and add internal notes from the panel. Status change is saved with a timestamp. [ASSUMPTION: no email is sent to the visitor on status change — confirmed by scope.]

---

## 5. Constraints and Non-Functional Requirements

| Concern | Requirement |
|---|---|
| **Stack** | Django (Python), Tailwind CSS (CLI build, not CDN), PostgreSQL/Neon in prod, SQLite locally, Render + gunicorn + whitenoise. No React, no separate API. |
| **Security** | No secrets in Git (.env via python-decouple). `DEBUG=False` in prod. HTTPS redirect enforced. Secure cookies (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`). Admin path is `/panel/`. |
| **Images** | Gallery images stored in Cloudinary (free tier). Credentials via env vars (`CLOUDINARY_URL` or `CLOUDINARY_CLOUD_NAME` / `API_KEY` / `API_SECRET`). Local development falls back to local disk storage (Django `DEFAULT_FILE_STORAGE` switchable via `USE_CLOUDINARY` env var). |
| **Phone / WhatsApp** | `BUSINESS_PHONE` and `BUSINESS_WHATSAPP` read from env vars. Placeholder values used in code and tests. Never hardcoded. |
| **Hosting** | Render (gunicorn + whitenoise) + Neon PostgreSQL. Staging on free tiers; production on Render paid plan. Not Vercel. |
| **Performance** | `whitenoise` serves static files. Images lazy-loaded. Tailwind purged in production build. Target < 3 s LCP on a mid-range Android over 4G. |
| **Accessibility** | WCAG 2.1 AA for colour contrast. Semantic HTML (`<nav>`, `<main>`, `<section>`, `<footer>`). |
| **SEO** | `sitemap.xml` at `/sitemap.xml`, `robots.txt` at `/robots.txt` (blocks `/panel/`). `LocalBusiness` + `MovingCompany` JSON-LD schema on Home. |
| **Content** | No invented facts. Placeholder copy used where real content is missing, clearly marked. |
| **Config** | All secrets and environment-specific values via env vars (python-decouple + dj-database-url). |

---

## 6. MVP Scope

### 6.1 In Scope
- Five public pages with SEO metadata, semantic HTML, Tailwind styling
- Quote form: validation, honeypot, DB save, email + Telegram notification
- Floating Call and WhatsApp buttons on mobile
- Highway-sign hero design element
- Client panel at `/panel/`: enquiry management, service management, gallery management
- `sitemap.xml`, `robots.txt`, JSON-LD schema
- Cloud image storage for gallery uploads
- Tests: quote form (validation, honeypot, notification failure), permissions (client can/cannot access), public pages (HTTP 200)
- README: local setup and Render + Neon deployment instructions

### 6.2 Out of Scope for MVP
- Google Ads integration
- Tamil language version
- Online payments or booking calendar
- Customer registration / login
- Blog
- Review aggregation or star ratings
- Social media feed embedding

---

## 7. Success Metrics

**Primary**
- **SM-1:** Site appears in Google Search results for "packers and movers Tiruppur" within 4 weeks of going live. Validated via Google Search Console impressions.
- **SM-2:** Every enquiry submitted triggers a Telegram notification to the owner (when `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are set) within 30 seconds, measured in staging. When those vars are absent, no exception is raised.

**Secondary**
- **SM-3:** All five public pages return HTTP 200 and score ≥ 80 on Google PageSpeed Insights (mobile) within one week of launch.
- **SM-4:** Client user can log in, view enquiries, update status, and manage gallery without developer assistance.

**Counter-metrics (do not optimise)**
- **SM-C1:** Do not optimise for raw page count or word count — SEO should come from relevance and performance, not content bloat.

---

## 8. Open Questions

1. **Telegram bot** — Does the owner already have a Telegram account? (You'll need to create a bot token and provide the owner's chat ID before enabling Telegram notifications. Optional feature — site works without it.)
2. **Real gallery photos** — Placeholder images used at launch; owner to supply real photos via the panel post-launch.
3. **Real services content** — Services copy (titles, descriptions) to be supplied by owner. Placeholder text at launch.

---

## 9. Assumptions Index

- **A-FR-5:** Indian mobile phone validation is 10 digits starting with 6–9.
- **A-FR-7:** Notification failures are logged but never block the visitor response.
- **A-FR-8:** Client group permissions are set via a management command, not manually in the panel.
- **A-§5-Images:** Cloudinary free tier is acceptable for gallery image hosting on Render. Local dev uses local disk storage via `USE_CLOUDINARY=false`.
- **A-§5-Phone:** `BUSINESS_PHONE` and `BUSINESS_WHATSAPP` read from env vars; never hardcoded.
- **A-§5-Hosting:** Render + Neon is the only target deployment. Not Vercel.
- **A-FR-7:** Notification channels are pluggable. Email is out of scope (Render SMTP blocked). Telegram is optional. WhatsApp Business API is a future story.
- **A-FR-9:** No visitor-facing email is sent on status change.

