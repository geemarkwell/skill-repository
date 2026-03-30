# Pre-Delivery Checklist & Memory Management

> **Created:** January 23, 2026 | **Updated:** March 16, 2026

Run these checks before delivering any work. The first section is the quality gate; the second covers pattern persistence across sessions.

---

## Pre-Delivery Checklist

### Design Craft

**The Swap Test**
- [ ] Swapping the typeface for a common alternative would feel noticeably different
- [ ] Swapping the layout for a standard template would feel noticeably different
- [ ] The design couldn't belong to a generic product — it reflects this specific domain

**The Squint Test**
- [ ] Hierarchy is still perceivable with blurred vision
- [ ] No single border or surface jumps out harshly
- [ ] Structure is quiet, not loud

**The Signature Test**
- [ ] Can point to 5+ specific elements where the product signature appears
- [ ] Signature is in actual components, not just "the overall feel"

**The Token Test**
- [ ] CSS variable names evoke the product's world, not generic naming
- [ ] Every color traces back to the primitive system (foreground, background, border, brand, semantic)
- [ ] No random hex values outside the token system

**Spacing & Consistency**
- [ ] All spacing values are multiples of the base unit
- [ ] Padding is symmetrical unless there's an explicit reason
- [ ] One depth strategy used throughout (borders-only, subtle shadows, or layered)
- [ ] Border radius is consistent across similar elements

### Interaction States

- [ ] Every button/link has: default, hover, active, focus-visible, disabled
- [ ] Loading state uses skeleton placeholders (not just a spinner)
- [ ] Empty states have helpful guidance and/or a call to action
- [ ] Error states are specific, adjacent to what failed, and offer recovery

### Technical Quality

**Rendering Performance**
- [ ] Animations use only `transform` and `opacity`
- [ ] No `transition: all` — transitions are property-specific
- [ ] `prefers-reduced-motion` is respected (instant transitions, no animation)
- [ ] Complex views use `contain: layout` or `content-visibility: auto` where appropriate

**Loading Performance**
- [ ] Custom fonts use `font-display: swap` or `font-display: optional`
- [ ] Critical fonts are preloaded (`<link rel="preload">`)
- [ ] Images below the fold use `loading="lazy"`
- [ ] Images have explicit dimensions or `aspect-ratio` (no layout shift)
- [ ] Heavy components/routes are code-split if applicable

**Accessibility**
- [ ] All text meets WCAG 4.5:1 contrast against its background (3:1 for large text)
- [ ] Custom controls have keyboard navigation (Tab, Enter, Escape, Arrow keys)
- [ ] Focus indicators visible for keyboard users (`:focus-visible`)
- [ ] Semantic HTML used (`<nav>`, `<main>`, `<button>`, headings in order)
- [ ] Dynamic content uses `aria-live` for screen reader announcements
- [ ] `prefers-color-scheme` detected for dark/light mode preference

**Responsive**
- [ ] Layout adapts at mobile width (375px) — not just "doesn't break" but intentionally designed
- [ ] Touch targets are minimum 44×44 CSS pixels
- [ ] Typography uses `clamp()` or scales appropriately between viewports
- [ ] Hover-gated interactions have touch alternatives
- [ ] Full-height layouts use `dvh` units, not `100vh`

**Large Datasets** (if applicable)
- [ ] Tables/lists over ~100 items use virtualization
- [ ] Search/filter inputs are debounced (150-300ms)
- [ ] Dashboard widgets load progressively (skeleton → data)

---

## Memory Management

When and how to update `.interface-design/system.md`.

### When to Add Patterns

Add to system.md when:
- Component used 2+ times
- Pattern is reusable across the project
- Has specific measurements worth remembering

### Pattern Format

```markdown
### Button Primary
- Height: 36px
- Padding: 12px 16px
- Radius: 6px
- Font: 14px, 500 weight
- Keyboard: Enter/Space triggers click
```

### Don't Document

- One-off components
- Temporary experiments
- Variations better handled with props

### Pattern Reuse

Before creating a component, check system.md:
- Pattern exists? Use it.
- Need variation? Extend, don't create new.

Memory compounds: each pattern saved makes future work faster and more consistent.
