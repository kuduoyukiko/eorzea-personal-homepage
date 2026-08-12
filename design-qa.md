# Design QA — 职业灵魂水晶卡片

## Comparison target

- Source visual truth: `C:\Users\10426\.codex\generated_images\019fe510-74fa-72b3-96cf-fa668bfe3e8b\exec-f2ab187b-b5e7-437a-a8e6-e8882113dd1c.png`
- Source pixels: 1888 × 833.
- Implementation: local Flask route `/jobs`.
- State: public page, default scroll position; desktop and compact responsive layout.
- Design scope: preserve the existing site shell and job-card density while reproducing the selected soul-crystal treatment inside combat job cards.

## Evidence

- Desktop implementation screenshot: `tmp/jobs-crystals-desktop-v2.png`.
- Compact implementation screenshot: `tmp/jobs-crystals-mobile-500.png`.
- Full-view comparison: `tmp/jobs-crystals-comparison-full.png`.
- Focused tank-section comparison: `tmp/jobs-crystals-comparison-focused.png`.
- Desktop viewport: 1910 × 1080 CSS pixels, device scale factor 1.
- Compact viewport: 500 × 900 CSS pixels, device scale factor 1.
- Full desktop screenshot pixels: 1910 × 1080; compact screenshot pixels: 500 × 900.
- The source is a component-focused mock rather than a full site screenshot. The focused comparison normalizes both tank sections to the same 1075-pixel comparison width; the existing sidebar and page shell are intentionally excluded from the component judgment.

## Required fidelity surfaces

- Fonts and typography: existing site typography, Chinese names, abbreviations and level badges are unchanged. Hierarchy and optical weights remain consistent with the selected target.
- Spacing and layout rhythm: four cards remain aligned on desktop and two cards per row at the 500px breakpoint. The extra lower card space gives each crystal a dedicated visual field without changing category order.
- Colors and visual tokens: existing navy, antique-gold borders and glass panels are preserved. No new global color tokens were introduced.
- Image quality and asset fidelity: all 19 combat jobs use their real 80 × 80 in-game soul-crystal item images. The images are not redrawn or replaced with CSS/vector approximations. Perspective, saturation and shadow are applied non-destructively in CSS.
- Copy and content: all existing Chinese category labels, job names, abbreviations and levels remain data-driven and unchanged. Crafters and gatherers receive no soul crystal.

## Findings

- No actionable P0/P1/P2 mismatch remains in the selected component scope.
- The production implementation is deliberately denser vertically than the concept mock because the existing site displays all combat, crafting and gathering groups on one page. The crystal scale, right-bottom placement, side-leaning angle, job matching and foreground/content layering match the selected treatment.

## Comparison history

1. Initial implementation evidence: `tmp/jobs-crystals-desktop.png`.
   - [P2] The 51-degree X rotation made the item frames appear too flat, and the negative bottom offset clipped too much of the images.
   - Fix: reduced X rotation to 38 degrees, increased crystal size to 106px, moved the images upward, and retained them at `z-index: 0` behind the card content.
2. Post-fix evidence: `tmp/jobs-crystals-desktop-v2.png` and `tmp/jobs-crystals-comparison-focused.png`.
   - The crystals now retain readable facets and job marks, sit inside the lower-right card area, and remain behind the existing content.
   - Compact evidence at 500px confirms two-column wrapping with no card or crystal clipping.

## Functional and static checks

- `/jobs` renders HTTP 200 with 19 soul-crystal elements.
- All 19 committed soul-crystal PNG assets return HTTP 200.
- Python compilation passes for `app.py`, `config.py`, and `utils/data_utils.py`.
- `git diff --check` reports no whitespace errors.
- The browser component has no new controls or changed navigation behavior; the existing job-card hover state remains functional and only adds a restrained crystal lift.

## Follow-up polish

- P3: if desired after viewing on the production monitor, crystal brightness can be tuned globally by adjusting only the `opacity` and `filter` values on `.job-soul-crystal`.

final result: passed
