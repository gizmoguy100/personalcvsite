# personalcvsite

A personal CV and project notebook for Alex Ferriroli, styled after the Windows XP
"Luna" Olive Green theme. Built with Hugo, with a theme written from scratch in `layouts/` and `assets/`.

There is no JavaScript, no web font, and no framework. Pages are ordinary documents
inside a single XP window frame.

## Requirements

- Hugo extended 0.169 or newer (`hugo version`)
- Python 3 with Pillow, only for regenerating the social card

## Local development

```sh
hugo server --disableFastRender
# http://localhost:1313/
```

Production build (what CI runs):

```sh
hugo --gc --minify
# output in ./public/
```

## Structure

```
content/            Home, CV, About, Projects
layouts/            baseof, home, page, cv, projects, project, 404 + partials
assets/css/         tokens.css → chrome.css → pages.css (concatenated)
assets/img/         headshot.jpg (source for Hugo image processing)
static/             favicon.svg, og.png, robots.txt
scripts/make-og.py  regenerates static/og.png
.github/workflows/  GitHub Pages deployment
```

## Editing content

- **Home** — `content/_index.md` (welcome line and bio). The CV/About/Contact tiles
  and the Contact panel are in `layouts/home.html`.
- **CV** — `content/cv.md`. Experience, education and volunteering are structured
  front matter; add an entry to the relevant list and it renders in the details view.
  Interests come from `params.interests` in `hugo.yaml`.
- **About** — `content/about.md`, plus the "System Properties" box in
  `layouts/page.html`.
- **Projects** — the section landing page is `content/projects/_index.md`
  (`layout: projects`). Add each project as `content/projects/<slug>.md` with
  `layout: project`; the cards and Properties box read `title`, `description`,
  `icon`, `status`, `stage`, `hardware`, `hardware_detail`, `firmware`,
  `network`, `streaming`, `storage`, `recovery` and `date` from front matter.
  Write the body as normal Markdown.
  Order entries with `weight` (lowest first). The list and detail layouts are
  `layouts/projects.html` and `layouts/project.html`.
- **Code in write-ups** — fenced code blocks are not syntax-highlighted; they
  render as scrollable `<pre>` panels styled in `assets/css/chrome.css`.
- **Shared details** — name, role, email, location and GitHub live in `hugo.yaml`
  under `params` and are reused in the task pane, status bar, About and metadata.
- **Headshot** — replace `assets/img/headshot.jpg`; Hugo generates the WebP variants
  and keeps the aspect ratio automatically.
- **Social card** — edit `scripts/make-og.py` and run `python3 scripts/make-og.py`.

Old inbound links are preserved: `/cv/` and `/about/` keep their trailing slashes,
and `/en/` and `/de/` redirect to `/` via Hugo aliases on the home page.

## Design notes

- Palette and bevels are defined once in `assets/css/tokens.css`.
- Type is a system stack (`Tahoma, Verdana, "Segoe UI", ...`); nothing is downloaded.
- Title bar text and all body copy are checked at 4.5:1 contrast or better.
- All icons are hand-authored SVG in `layouts/_partials/icon.html`. No Microsoft
  bitmaps, wallpapers or logos are used; this is an homage, not a clone.
- The site works without JavaScript, and the CV has a dedicated print stylesheet
  (`Ctrl/Cmd + P` produces a clean paper CV).

## Deployment (GitHub Pages)

The workflow in `.github/workflows/deploy.yml` builds with Hugo and publishes the
artifact to Pages. It derives `baseURL` from `actions/configure-pages`, so the same
workflow works for the `github.io` preview and for the custom domain.

1. Create `gizmoguy100/personalcvsite` on GitHub and push `main`.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Push to `main` and wait for the workflow. Preview URL:
   `https://gizmoguy100.github.io/personalcvsite/`.
4. When the preview looks right, in **Settings → Pages → Custom domain** enter
   `ferriroli.com` and save (this writes the `CNAME`).
5. At your DNS provider, replace the current A record (`178.238.154.176`, the Caddy
   server) with GitHub Pages:

   ```
   A     @    185.199.108.153
   A     @    185.199.109.153
   A     @    185.199.110.153
   A     @    185.199.111.153

   AAAA  @    2606:50c0:8000::153
   AAAA  @    2606:50c0:8001::153
   AAAA  @    2606:50c0:8002::153
   AAAA  @    2606:50c0:8003::153

   CNAME www  gizmoguy100.github.io.
   ```

   Leave MX/TXT records alone so email keeps working.
6. Wait for the certificate, then enable **Enforce HTTPS**.

The workflow only sets the custom domain when you configure it in step 4. Do not add
`static/CNAME` before the preview has been checked — a CNAME makes GitHub redirect
the `github.io` URL to the custom domain.

## Notes

- `public/`, `resources/_gen/` and `.hugo_build.lock` are ignored.
- The site is English-only (`en-GB`); the previous machine-translated German pages
  are intentionally gone, with redirects in their place.
