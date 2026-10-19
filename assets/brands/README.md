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

**Source of truth: the six Claude Design systems below (Oct 2026).** They replace every older brand guide, skill and table. If this table and a design system disagree, the design system wins. In Claude, load the `brand-design-systems` skill first; it links each system and lists the rules (no pricing, no "coming soon", one brand per film).

| Brand | Design system |
|---|---|
| BRMG | https://claude.ai/artifact/Nbuw532WjwcyzmUnp42Pwh |
| DevX | https://claude.ai/artifact/CT87mLszcU7q7qNPUYHTmd |
| Crankington DC | https://claude.ai/artifact/K2XhgeCaANz153ixaEKVFN |
| Go-Go Royalty | https://claude.ai/artifact/Bxj9xz763rivioT2fjTmkm |
| Go-Go Royalty VR | https://claude.ai/artifact/Pzzzq2rrs4iBSZ7pYGWz69 |
| GoGo Maps | https://claude.ai/artifact/Gopfre6Gr7AQrDXHXoR9if |

Quick reference (copy of the systems' tokens):

| Brand | Colours | Fonts |
|---|---|---|
| BRMG | Impact Red #DB1F1F (logo red; letterforms, rules, small accents), Cover Red #ED2F2F (full-bleed covers only), Paper Warm #F2F1ED, Paper Grey #E8E8E8, Parchment #DFD7C7, Charcoal #3D3935, Oxblood #6F4650, Kraft #B58975 (tags only), White, Ink #000000 (outlines only) | Bagel Fat One, Anton, Poppins ExtraBold, Montserrat |
| DevX | Page #F5F7FA, Indigo #4B43DF, Lime #A1E309, Mint #60E8B8, Circuit Purple #6050B0, Ink #14162B and Body Grey #3A3D4D (both provisional), White | Syne, DM Sans |
| Crankington DC | Black #0F0F0F, Gold #FFB612, White; neutrals Surface #1A1A1A, Line #2E2E2E, Muted #9A9A9A | Varsity Team (not committed; use Graduate and say so), Roboto |
| GoGo Maps | Void #0A0E30, Card #0E133F, Archive Navy #151C63 (fill only), Elevated #1A2270, Copper #D3603D (the one accent; light #DE7A5A, deep #B8502E), Silver #B8B9B9 (quiet text and dividers only), White at 100/82/55% | Archivo Black, Instrument Serif Italic, DM Sans |
| Go-Go Royalty | Void #0D0710, Card #1A0D22, Elevated #241030, Royal Purple #612066 (logo purple) and Deep Plum #6C3E7A (surfaces only), Vivid Violet #B45CFD (one CTA/accent per design), Violet Hover #C47AFE, White (hero H1), Blush Lilac #F4E8FE (H2/H3, body), Muted Purple #C4A8D4 (captions), Lavender #E9D3FC (ticker only) | Playfair Display Italic, Barlow Condensed, Inter |
| Go-Go Royalty VR (its own system, not shared with Go-Go Royalty) | Void #0D0710, Void Lift #120A18, Violet #B45CFD plus its alpha steps (glow 38%, dim 15%, border 22%, tint 4%), Lilac #F4E8FE, Muted Lilac #C9A8E0; logo-artwork-only: ring #4E016C, electric #B004F4, silver #94949C. Square corners | Bungee, Bebas Neue, DM Mono, Space Grotesk |

Taglines: BRMG "Where Culture Meets Execution"; DevX "Build Smarter. Automate Everything."; Go-Go Royalty "#NeverMuteDC #KeepRocking"; Go-Go Royalty VR "Experience Go-Go in 360°"; GoGo Maps "Where music meets the map" (hero), "Preserving the legacy, navigating the beat." (headers and footers). Sites: brmgdc.com, devxdoes.com, go-goroyalty.com, go-goroyaltyvr.com, gogomaps.online. Go-Go Royalty hero sections carry the band ticker: RARE ESSENCE · BACKYARD BAND · TCB · JUNKYARD BAND · NEG · BOUNCEBEAT KINGS.

Footers: BRMG "© 2006 Beat Republic Media Group", DevX "© 2026 DevX", Crankington "© 2026 Crankington DC", GoGo Maps and Go-Go Royalty VR "© 2026".

Fonts for every system above are committed under `assets/fonts/latin/` and registered in `assets/fonts/fonts.css`, except Varsity Team.
