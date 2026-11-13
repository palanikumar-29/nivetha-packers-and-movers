# Project Status: Nivetha Packers and Movers

**Last Updated**: November 2026  
**Test Suite Status**: 144 / 144 tests passing (100% green)

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

## 2. Open Items (Pending Client & Live Launch)

1. **Client Content & Photos**: Receive authentic high-resolution packing and transport photos from the business owner to populate the gallery.
2. **Brand Logo**: Receive the official vector or transparent PNG logo from the client to place in the header logo slot.
3. **Custom Domain**: Connect the production domain (e.g. `nivethapackers.in`) to the Render service and update DNS CNAME records.
4. **Cloudinary Production Setup**: Enter live `CLOUDINARY_URL` credentials in Render environment variables and toggle `USE_CLOUDINARY=True`.
5. **Google Business Profile**: Verify the client's Google Business Profile with matching name, phone number, and Tiruppur address.
6. **Analytics (Optional Story 2.5)**: If client requests visitor metrics, integrate a privacy-friendly, cookie-free tool (e.g. Plausible or Cloudflare Web Analytics).
7. **Production Go-Live Checklist**: Complete the final deployment checklist in `docs/RUNBOOK.md` before publicly launching.

---

## 3. Known Constraints & Edge Cases

- **Render Free Tier Spin-Down**: On Render's free tier, the web service sleeps after 15 minutes of inactivity. First load after sleep takes approximately 30–50 seconds (cold start). For zero downtime, upgrade to the Starter tier ($7/mo).
- **Ephemeral Storage on Free Tier**: Local disk storage on Render is reset whenever the service rebuilds or restarts. Gallery images MUST use Cloudinary (`USE_CLOUDINARY=True`) in production to persist across deploys.
- **SMS / WhatsApp Direct Messaging**: Outbound SMS gateways or official WhatsApp Business APIs are not configured. The site uses direct customer-initiated `wa.me` links, which requires no recurring monthly API fees.

---

## 4. Next Recommended Task

**Task**: Execute the staging deployment on Render following [`docs/RUNBOOK.md`](file:///e:/Nivetha-p&m/docs/RUNBOOK.md).  
1. Create free Neon PostgreSQL database and copy `DATABASE_URL`.
2. Connect repo to Render, enter environment variables, and trigger initial deploy.
3. Run `python manage.py createsuperuser` and `python manage.py create_client_group` in the Render shell.
4. Verify all 5 public pages load and submit a test quote request to confirm database persistence.
