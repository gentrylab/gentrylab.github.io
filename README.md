# Gentry Laboratory website

Static site for the Gentry Laboratory, Department of Biochemistry & Molecular
Biology, University of Florida. Plain HTML and CSS, no build step, no
dependencies. Hosted on GitHub Pages.

```
index.html            homepage
people.html           People page
assets/
  site.css            all styles, shared by every page
  hero-*.jpg          hero image, three widths; the browser picks one
  group-photo-*.jpg   lab group photograph, two widths
  logo-lockup.png     logo + wordmark (brown mark, blue type)
  logo-mark.png       icon only
  favicon-*.png       browser tab icons
  apple-touch-icon.png
```

## Editing the site

Page text lives in `index.html` and `people.html`. Styling lives in `assets/site.css`,
shared by both. To change a sentence:

1. Open `index.html` here on GitHub.
2. Click the pencil icon (top right of the file).
3. Edit the text, then **Commit changes**.
4. The live site updates in about a minute.

Text still to fill in is marked with `[SQUARE BRACKETS]`: lab email, phone,
member names, funders. Search the file for `[` to find them all.

## Adding a page

1. Copy `people.html` to a new file, e.g. `research.html`.
2. Keep the header, masthead and footer; replace the middle.
3. Add a link to it in the `<nav>` of every page:
   `<a href="research.html">Research</a>`

House style: no em dashes anywhere in the copy.

## Publishing

Settings → Pages → Source: *Deploy from a branch* → Branch: `main`, folder: `/ (root)`.

Every commit to `main` republishes the site automatically.

## Custom domain

Ask UF IT for a subdomain (e.g. `gentrylab.med.ufl.edu`) pointing at
`<username>.github.io` via a CNAME record. Then Settings → Pages → Custom
domain, and tick **Enforce HTTPS**.

## Credits

Hero image and group photograph: Gentry Lab. Type: Lora, Archivo and IBM Plex
Mono via Google Fonts.
