# Project Status: Nivetha Packers and Movers

**Last Updated**: November 2026  
**Test Suite Status**: 145 / 145 tests passing (100% green)  
**Staging Status**: Live on Render with Neon PostgreSQL and Cloudinary

---

## 1. Implemented Stories Summary

- **Story 1.1 (Foundation & Data Models)**: Initialized Django 5.2, split settings, STORAGES dictionary, QuoteRequest, Service, and GalleryImage models.
- **Story 1.2 (Base Layout & Home Page)**: Built responsive navigation, hero section, highway route board sign, and light/dark theme toggle.
- **Story 1.3 (Public Pages)**: Created Services list, Gallery grid, About narrative, and Contact page with office details.
- **Story 1.4 (Quote Form & Lead Capture)**: Implemented QuoteForm with validation, Indian phone regex, honeypot spam protection, and database save.
- **Story 1.5 (Pluggable Notifications)**: Built `core/channels/` layer with non-blocking dispatcher and optional Telegram bot channel.
- **Story 1.6 (SEO & Indexing Control)**: Added dynamic XML sitemap, robots.txt, schema.org JSON-LD, and `ALLOW_INDEXING` crawler guard.
- **Story 1.7 (Opening Animation)**: Built Home-page-only branded intro animation (< 4 KB, CSS/SVG, accessibility-aware, Skip button).
- **Story 2.1 (Client Panel & WhatsApp Link)**: Configured custom `/panel/`, restricted 10-perm "Client" group, amber highlight, and `wa.me` customer link.
- **Story 2.2 (Cloudinary Storage)**: Integrated Cloudinary for media uploads with local fallback, 5 MB file size limit, and real magic-byte validation.
- **Story 2.3 (Deployment Preparation & Documentation)**: Created Render blueprint (`render.yaml`), `build.sh`, `.env.example`, and deployment runbook.
- **Story 2.4 (Palette Presets & Logo Slot)**: Built `beige` and `navy` color presets with WCAG AA contrast, admin switching via `SiteSettings`, and header logo slot.

---

## 2. Service Area & Brand Rules

- **Service Area**: Tiruppur (main focus) and all over Tamil Nadu.
- **Strict Copy Rule**: Chennai and Madurai are NOT mentioned anywhere in templates, copy, SEO, docs, or tests.
- **Palette Presets**: `navy` and `beige`, switchable in Site settings (`SiteSettings` singleton model in `/panel/`).

---

## 3. Current Live Status & Pending Items

- **Current Environment**: Staging is **LIVE on Render** connected to Neon PostgreSQL and Cloudinary storage.
- **Pending Items (Client & Go-Live)**:
  1. **Real photos from client**: High-resolution packing and shifting photos from client.
  2. **Custom domain**: Client will purchase domain later; configure DNS CNAME and update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL` when bought.
  3. **Render paid upgrade**: Optional upgrade from Free to Starter ($7/mo) to eliminate 15-minute spin-down cold starts.
  4. **`ALLOW_INDEXING=True`**: Switch from `False` to `True` on final domain to enable search engine indexing.
  5. **Analytics**: Optional GA4 or privacy-friendly analytics integration upon client request.
  6. **Google Business Profile**: Verify listing with matching Tiruppur address and phone number.
  7. **Balance payment**: Final payment upon client content sign-off and custom domain rollout.

---

## 4. Known Constraints & Operating Notes

- **Render Free Tier Spin-Down**: Free tier sleeps after 15 minutes of inactivity (30–50s cold start). Upgrade to Starter ($7/mo) for zero cold starts.
- **Media Persistence**: Staging verified with Cloudinary (`USE_CLOUDINARY=True`). Ephemeral disk reset will not affect uploaded media.
- **Customer Leads**: Client manages quotes in `/panel/` with 1-click WhatsApp (`wa.me`) follow-up links.
