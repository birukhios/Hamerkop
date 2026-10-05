# Hamerkop Systems website

Static site served by GitHub Pages from the root of `main`. Pages are generated — edit the sources, then rebuild.

## Editing

| What | Where |
| --- | --- |
| Solutions, products, services, industries, Insights categories and articles, Odoo milestone, site settings | `src/content.json` |
| One-off pages (home, hubs, company, contact, legal, 404) | `src/pages/*.html` |
| Styles / behaviour | `styles.css`, `main.js` |

Then run:

```bash
python3 build.py
```

This regenerates every `*.html` page, `sitemap.xml` and `robots.txt` in the repo root. Commit the sources and the generated files together. Python 3 is the only requirement.

## Common tasks

- **Publish an article:** add an entry to `articles` in `src/content.json` (the shape is described in `articles_note`). It appears on the homepage, the Insights page and its category page.
- **Odoo badge and photos:** put the files in `assets/odoo/` and fill in the `odoo` block (`badge`, `photos`, dates, `partner_url`). Galleries appear once photos are listed.
- **Contact form delivery:** by default the form opens the visitor's email app. Set `site.form_endpoint` to a form service URL (e.g. Formspree) to send directly, and `site.routes` to send each Area of Interest to a different inbox.
- **Custom domain:** update `site.url`, add a `CNAME` file, and rebuild.
