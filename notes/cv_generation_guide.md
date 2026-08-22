# CV Generator — Setup & API Reference

Lets a seeker pick a professionally designed template and generate a real, downloadable PDF resume
from their existing profile data (personal info, experience, education, skills, languages,
training). Code lives under `src/domains/profile/seeker_profile/` (schema/service/route named
`cv_*`) and `src/templates/cv/` (the actual template designs).

## 1. How it works

1. Seeker picks a template (`GET /api/seeker/cv/templates`).
2. Their full profile is pulled from MongoDB and assembled into one context dict — this includes
   resolving `province_id`/`district_id`/`expertise_category_ids` (stored as ObjectId references)
   into actual readable names, and formatting dates nicely (`"Jan 2023"` instead of a raw
   timestamp). None of that resolution existed elsewhere in the codebase, so it's done fresh in
   `cv_service.py`.
3. The chosen Jinja2 HTML template (`src/templates/cv/{modern,classic,elegant}.html`) is rendered
   with that context — same templating engine already used for the OTP email, just a different
   template.
4. **WeasyPrint** converts that rendered HTML/CSS into an actual PDF (byte-for-byte from the CSS —
   this is what makes the template designs look like real resumes instead of a plain Word doc).
5. The PDF is uploaded to Cloudinary (via the existing `upload_document()` helper, same one already
   used for uploaded resumes) and the link is saved onto the seeker's profile as `cv_url`,
   `cv_template_id`, `cv_generated_at` — regenerating just overwrites these (the previous Cloudinary
   file is not deleted, matching how resume re-uploads already behave elsewhere in this codebase).

## 2. ⚠️ Required system libraries (WeasyPrint)

This is the one thing that's different from every other dependency in `requirements.txt` — WeasyPrint
needs a few native libraries installed on the machine running the server (Pango, Cairo,
GDK-Pixbuf, libffi). `pip install weasyprint` alone is **not enough** — without these, the app will
fail the moment someone calls `/generate` (everything else, including `/templates` and `/preview`,
still works fine since those don't touch WeasyPrint at all — the import is deliberately deferred
into `generate_pdf()` for exactly this reason, so a missing system lib doesn't crash the whole app
on startup).

**Local Mac (for testing with `uvicorn main:app --reload`):**
```bash
brew install pango cairo gdk-pixbuf libffi
```

**Docker / Railway (production):** add this to whatever Dockerfile builds your API image:
```dockerfile
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```
If you're deploying via Railway's default Python buildpack (no Dockerfile) rather than a Docker
image, you'll need to switch to a Dockerfile-based deploy for this feature to work — Railway's
default Python buildpack doesn't let you install arbitrary apt packages. Ask if you want help
setting that up when you're ready to deploy this.

## 3. API reference

All routes require `Authorization: Bearer <token>` and are seeker-only (`require_seeker`).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/seeker/cv/templates` | List available templates (id, name, description) |
| GET | `/api/seeker/cv/preview/{template_id}` | Raw HTML preview — fast, no PDF/upload, good for a live WebView preview while picking a template |
| POST | `/api/seeker/cv/generate` | Body: `{ "template_id": "modern" }` — renders, converts to PDF, uploads, returns `{ cv_url, template_id, generated_at }` |
| GET | `/api/seeker/cv/current` | Returns the seeker's most recently generated CV info (or nulls if they've never generated one) |

## 4. Templates

Three distinct designs, all A4, all in `src/templates/cv/`:

- **modern** — dark sidebar (photo, contact, skills as pills, language bars) + main content area. Most visually distinctive.
- **classic** — traditional single-column, serif headings, ATS-friendly (no multi-column layout that trips up resume-parsing software).
- **elegant** — bold purple gradient header band, soft accent colors throughout.

To add a new template: drop a new `.html` file in `src/templates/cv/` (copy one of the existing ones
as a starting point — same Jinja2 variables are available in all of them: `full_name`,
`current_position`, `email`, `phone_number`, `location`, `photo_url`, `biography`, `linkedin_url`,
`portfolio_url`, `date_of_birth`, `gender`, `marital_status`, `nationality`, `skills`,
`expertise_categories`, `experiences`, `educations`, `trainings`, `languages`), then add one entry
to the `CV_TEMPLATES` dict at the top of `cv_service.py`. No other code changes needed.
