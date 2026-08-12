# Yukiko's Chronicle — Product Context

## Product

A personal FINAL FANTASY XIV chronicle built with Flask and Jinja. It preserves two characters' game memories while connecting them with the owner's real-world interests, journal, and social links.

## Audience and core journey

- Primary audience: the owner, friends, and other FFXIV players.
- Primary journey: enter through the dual-character hero, understand the two protagonists, then explore character records, soul crystals, Eorzea memories, real-world life, and the journal.
- Success means the site feels personal and unmistakably FFXIV-inspired, remains readable over expressive screenshots, and loads reliably for visitors in China.

## Brand and content rules

- Preserve the existing name, routes, navigation labels, uploaded images, character data, and user-written copy.
- Core visual vocabulary: deep aether navy, restrained antique gold, cyan crystal light, real character imagery, and occasional handwritten English.
- Liquid glass is a material reserved for navigation, profile records, and a few high-value surfaces; it should not flatten every section into the same translucent card.
- Use only real local content and uploaded game imagery. Do not invent activity, endorsements, or story facts.

## Technical constraints

- Flask/Jinja templates with progressive enhancement.
- Critical layout, icons, and media must work without third-party CDN availability.
- Desktop sidebar and decorative characters must never cover page content or intercept input.
- Mobile layouts must remain usable at 390 px width and support reduced motion/transparency preferences.

## Open decisions

- A self-hosted handwriting font may be added later if consistent cross-platform lettering becomes a priority.
- More aggressive image conversion can be considered after measuring production traffic and hosting limits.
