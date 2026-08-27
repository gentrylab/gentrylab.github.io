# Gentry Laboratory — website

Static site for the Gentry Laboratory, Department of Biochemistry & Molecular
Biology, University of Florida. Plain HTML and CSS, no build step, no
dependencies. Hosted on GitHub Pages.

```
index.html          the whole homepage (content + styles in one file)
assets/
  hero-1000.jpg     hero image, three widths; the browser picks one
  hero-1600.jpg
  hero-2400.jpg
  logo-lockup.png   logo + wordmark (colour, brown mark / blue type)
  logo-mark.png     icon only
  favicon-*.png     browser tab icons
  apple-touch-icon.png
```

## Editing the site

Everything readers see lives in `index.html`. To change a sentence:

1. Open `index.html` here on GitHub.
2. Click the pencil icon (top right of the file).
3. Edit the text, then **Commit changes**.
4. The live site updates in about a minute.

Text still to fill in is marked with `[SQUARE BRACKETS]` — lab email, phone,
member names, funders. Search the file for `[` to find them all.

## Adding a page

1. Copy `index.html` to a new file, e.g. `research.html`.
2. Replace everything between `<section class="hero">` and `</footer>` with the
   new page's content.
3. Add a link to it in the `<nav>` of every page:
   `<a href="research.html">Research</a>`

## Publishing

Settings → Pages → Source: *Deploy from a branch* → Branch: `main`, folder: `/ (root)`.

Every commit to `main` republishes the site automatically.

## Custom domain

Ask UF IT for a subdomain (e.g. `gentrylab.med.ufl.edu`) pointing at
`<username>.github.io` via a CNAME record. Then Settings → Pages → Custom
domain, and tick **Enforce HTTPS**.

## Credits

Hero image: fluorescence micrograph, Gentry Lab. Type: Lora, Archivo and
IBM Plex Mono via Google Fonts.
