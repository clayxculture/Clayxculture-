# Photos on the storefront

All photos live in `site/img/` as WebP (plus one JPG for link previews). File names carry a content hash, so they are cached for a year and refresh automatically when a file changes.

| Where on the site | File in `site/img/` | Original upload |
|---|---|---|
| Home hero, photo 1 (full-bleed on portrait phones; left card on landscape screens) | `hero-*` | 1794893333167_image.png (same photo as GULMARG.jpg) |
| Home hero, photo 2 (landscape screens only: right card; never downloaded on portrait phones) | `navy-*` | _india.jpg (full-height original, 736x1308) |
| Lookbook: Baggy denim | `denim-*` | the file named "Pin…ʀᴘɪᴛ_ᴛʜ__ᴀᴋᴜʀ.jpg" |
| Lookbook: Winter layers | `knit-*` | 972636850791636239.jpg |
| Lookbook: Light linen | `linen-*` | _.jpg |
| Our story strip (home) and About page | `back-*`, `street-*`, `navy-*` | download.jpg, casual_fit.jpg, _india.jpg |
| Link preview (WhatsApp, Google, social) | `og.*.jpg` | square crop of the hero |

Not used (duplicates of the above): `1135681231062897500__1_.jpg`, `GULMARG.jpg`.

## Rights: NOT confirmed
I could not verify who owns these photos or what licence they carry. The file names and the uniform 736 px width look like downloads from Pinterest-style sites, which usually means the photographer (and the person pictured) did not give a licence for commercial use. Before real customers see them:
- keep only photos you took yourself, or that the photographer and the person shown have agreed in writing can be used to promote calyxculture;
- for any photo that fails that test, delete its `<img class="hl">` or `<picture class="hl2">` (hero), its `<button class="lk">` (Lookbook) or its entry in the story strip, and add a photo you own.

## Screens
- Portrait phones and tablets: one full-bleed hero photo with a slow zoom, as before.
- Landscape screens (phones turned sideways, tablets, laptops, desktops, ultra-wide): two framed photos side by side with a staggered entrance, a gentle float, and (mouse only) a subtle parallax. Motion is switched off for people who ask their device to reduce motion.
- Short landscape phones get a more compact heading so the buttons stay above the bottom bar.
- If an owner hero image is set in the admin settings, it replaces both built-in photos once loaded.

## Loading speed
- Hero photo 1 is a real `<img>` in the HTML with a matching `preload` hint and `fetchpriority="high"`: about 22 KB on small phones, 48 KB at full size. The second hero photo only downloads on landscape screens.
- Every other photo is `loading="lazy"` with width and height set (no layout shift) and a 240/400/736 px set so each screen downloads the smallest size that stays sharp.
- `_headers` caches `/img/*` for a year; `sw.js` keeps them for instant repeat visits and offline.

## Higher quality
The uploads are only 736 px wide. Originals of 1600 px or more would look sharper on large and high-density screens.
