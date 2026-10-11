# Brand assets

Drop each brand's real graphics here. The films load them from this folder, so a logo only has to be added once and every film can use it.

```
assets/brands/
  brmg/          Beat Republic Media Group
  devx/          DevX
  crankington/   Crankington DC
  gogomaps/      GoGo Maps
  ggrvr/         Go-Go Royalty VR
  gogoroyalty/   Go-Go Royalty.com
  shared/        anything used by more than one brand
    <brand>/logos/     primary logo, mark/icon, wordmark, one-colour versions
    <brand>/objects/   props and illustrations (mic, conga, mixing desk, hoodie, phone...)
    <brand>/images/    photos, posters, product shots, textures
```

## Naming

Lower-case, hyphens, no spaces. Say what it is and which version:

- `logos/logo-primary.svg`, `logos/logo-mark.svg`, `logos/logo-wordmark.svg`, `logos/logo-white.svg`, `logos/logo-black.svg`
- `objects/conga.svg`, `objects/microphone.svg`, `objects/hoodie-front.png`
- `images/poster-<name>.jpg`, `images/product-<name>.jpg`

## Rules of thumb

- SVG for logos and objects wherever possible (sharp at 1920x1080 and tiny). PNG with transparency is the fallback. Photos as JPG.
- Keep every file under about 3 MB. Resize photos to 2400 px on the long side before adding.
- Add only what you have the right to publish. The fork is public.
- Never put pricing, launch or "coming soon" wording in a graphic.

## Palettes and fonts (reference for films)

| Brand | Colours | Fonts |
|---|---|---|
| BRMG | Cover Red #ED2F2F, Impact Red #DB1F1F, Paper #F2F1ED, Charcoal #3D3935, Parchment #DFD7C7 | Bagel Fat One, Anton, Poppins ExtraBold |
| DevX | Page #F5F7FA, Indigo #4F46E5, Lime #2DD54A, Violet #7C3AED, Ink #14162B | Syne, DM Sans |
| Crankington DC | #0F0F0F, #FFB612 | Varsity Team, Roboto |
| GoGo Maps | Navy #151C63, Deep Navy #0A0E30, Terracotta #D3603D, Grey #B8B9B9, White | (see brand skill) |
| Go-Go Royalty / Go-Go Royalty VR (one shared system) | Void #0d0710 (canvas only), Card #1a0d22, Elevated #241030, Royal Purple #5d306b and Deep Plum #6c3e7a (surfaces only), Vivid Violet #b45cfd (one CTA/accent per design), White #FFFFFF (hero H1), Blush Lilac #f4e8fe (H2/H3, body), Muted Purple #c4a8d4 (captions), Lavender #e9d3fc (ticker only). No greys, no other brands' colors | Playfair Display Black Italic (display, H1-H3), Barlow Condensed (labels, counters, ticker), Inter (body) |

Go-Go Royalty taglines: "#NeverMuteDC #KeepRocking" (Royalty), "Experience Go-Go in 360°" (VR). Sites: go-goroyalty.com, go-goroyaltyvr.com. Hero sections always carry the band ticker: RARE ESSENCE · BACKYARD BAND · TCB · JUNKYARD BAND · NEG · BOUNCEBEAT KINGS.

Footers: BRMG "© 2006 Beat Republic Media Group", DevX "© 2026 DevX", Crankington "© 2026 Crankington DC", GoGo Maps and Go-Go Royalty VR "© 2026".
