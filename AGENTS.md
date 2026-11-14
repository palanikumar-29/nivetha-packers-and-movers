# Agent Instructions: Nivetha Packers and Movers

Read these primary reference documents before making any changes:
- [`docs/HANDOFF.md`](file:///e:/Nivetha-p&m/docs/HANDOFF.md): Project architecture, client context, and design decisions.
- [`docs/STATUS.md`](file:///e:/Nivetha-p&m/docs/STATUS.md): Current completion state, open items, and next recommended task.
- [`docs/RUNBOOK.md`](file:///e:/Nivetha-p&m/docs/RUNBOOK.md): Environment variables, setup, deploy, backup, and troubleshooting.

## Standing Rules for All Agents

1. **Design System & Tokens Only**:
   - Use existing CSS variable tokens (`--color-*`, `--btn-*`, `--intro-*`) and Tailwind utility classes.
   - Never add ad-hoc hex codes, gradients, neon accents, or unapproved palettes.
2. **No Invented Facts**:
   - Only state what is confirmed: household moves, office moves, vehicle transport within Tiruppur and all over Tamil Nadu, with main focus on Tiruppur.
   - **Forbidden words**: `regular`, `reliable`, `trusted`, `fast`, `experienced`, `years`, `guaranteed`, `free quote`, `no hidden charges`, `Coimbatore`, `Chennai`, `Madurai`.
3. **Security & Privacy**:
   - No hardcoded secrets, phone numbers, email addresses, or credentials. Use environment variable names only.
   - Never print or log personal user data (names, phones) or secret tokens in console, admin, or logs.
4. **Stack Conventions**:
   - Django 5.2 with `STORAGES` dictionary (never legacy `DEFAULT_FILE_STORAGE`).
   - Tailwind CSS standalone binary (recompile `output.css` with `--minify` whenever templates or tokens change).
   - Single Django app architecture: all core logic lives in `core/`.
5. **Testing & Verification**:
   - Write unit and integration tests for every change.
   - Run the full test suite (`python manage.py test`) and ensure 100% pass rate before completing a task.
6. **Reporting**:
   - Keep final responses concise and scannable (maximum 15 lines).
