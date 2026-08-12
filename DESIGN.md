# Yukiko's Chronicle — Design System

## Direction

An intimate FFXIV adventurer archive: cinematic character art in the foreground, quiet navy structure behind it, antique-gold editorial typography, and cyan aether light as the rare luminous accent. The interface should feel authored and atmospheric, not like a generic game dashboard.

## Hierarchy

1. Character imagery and the dual-name title establish identity.
2. Profile records and the central crystal explain the two-character premise.
3. Journal, sanctuary, memories, and beyond-Eorzea panels continue the journey.
4. Utility controls, administration, views, and music remain visually subordinate.

## Color and materials

- Base: near-black navy and blue-black gradients.
- Primary accent: muted antique gold for labels, borders, and calls to action.
- Secondary light: aether cyan only for crystal glow and small orientation cues.
- Liquid glass: use a cool translucent tint, one bright inner edge, one dark lower edge, and moderate blur. Keep text on an independently darkened surface so character art cannot lower contrast.
- Opaque or near-opaque navy is preferred for dense reading and long-form content.

## Typography

- Chinese and utility copy: Montserrat / Noto Sans SC with system fallbacks.
- Display and literary text: Georgia or another restrained serif.
- Handwritten English: reserved for the brand, character signature, hero name, and Moogle greeting. Never use it for long copy or small metadata.

## Shape, spacing, and motion

- Main surfaces: 14–18 px radius; compact buttons: 7–9 px radius.
- Use an 8 px spacing rhythm, with 24–40 px between major sections.
- Hover motion is subtle and directional; no large floating loops on content surfaces.
- Always honor reduced-motion and reduced-transparency preferences.

## Responsive behavior

- Desktop: fixed left navigation; decorative characters may peek from its outer edge only on the homepage and stay inside a narrow safety gutter.
- Tablet/mobile: navigation returns to a top collapsible bar; decorative sidebar characters are hidden.
- Hero content may overlap compositionally, but profile actions must keep at least 42 px touch height and never depend on hover.

## Accessibility and resilience

- Strong visible focus, skip navigation, semantic headings, aria-current, and explicit button labels.
- Critical Bootstrap and Font Awesome assets are served locally.
- Images may be expressive; foreground copy must retain its own scrim, shadow, or material rather than relying on the image being dark.
