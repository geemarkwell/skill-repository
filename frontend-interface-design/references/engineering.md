# Frontend Engineering Reference

> **Created:** March 16, 2026

Craft that doesn't perform is craft that fails. This reference covers the implementation engineering that makes design decisions actually work — in the browser, across devices, for all users.

## Table of Contents
1. [Rendering Performance](#rendering)
2. [Loading Performance](#loading)
3. [Accessibility](#accessibility)
4. [Responsive Implementation](#responsive)
5. [Large Dataset Handling](#datasets)
6. [Error & Edge States](#errors)

---

## 1. Rendering Performance <a name="rendering"></a>

The browser renders in a pipeline: Style → Layout → Paint → Composite. Every CSS change triggers some portion of this pipeline. The goal is to trigger as little as possible, especially during animation and interaction.

### The Frame Budget

At 60fps, each frame gets ~16.67ms for all work: JavaScript execution, style recalculation, layout, paint, and composite. Exceed that budget and the frame drops. The user sees jank — stuttering scroll, laggy hover states, choppy transitions.

### Composite-Only Animation

Only `transform` and `opacity` are GPU-composited. They skip layout and paint entirely, running on the GPU while the main thread stays free.

**Safe to animate:** `transform` (translate, scale, rotate), `opacity`
**Triggers layout (expensive):** `width`, `height`, `top`, `left`, `right`, `bottom`, `margin`, `padding`, `border-width`, `font-size`
**Triggers paint (moderate):** `color`, `background-color`, `box-shadow`, `border-color`

When you want to animate size or position, use `transform: scale()` or `transform: translateX()` instead of changing `width` or `left`. When you want to fade a background, consider animating `opacity` on a pseudo-element rather than transitioning `background-color`.

**Never use `transition: all`.** It transitions every property that changes, including layout-triggering ones. Be explicit:

```css
/* Bad — transitions everything including layout properties */
transition: all 0.15s ease;

/* Good — only transitions composite-friendly properties */
transition: transform 0.15s ease-out, opacity 0.15s ease-out;
```

### Layout Thrashing

Reading a layout property (`offsetHeight`, `getBoundingClientRect()`, `scrollTop`) forces the browser to synchronously recalculate layout if anything has changed. Reading, then writing, then reading again in a loop creates "layout thrashing" — the browser recalculates layout on every read.

Batch all reads together, then all writes together. If you need to read and write in the same frame, use `requestAnimationFrame` to defer writes to the next frame.

### CSS Containment

For complex views with many independent regions (dashboards, card grids, data tables), CSS containment tells the browser that a subtree's layout doesn't affect the rest of the page:

```css
/* The element's internals don't affect outside layout */
contain: layout;

/* Browser can skip rendering entirely if offscreen */
content-visibility: auto;
contain-intrinsic-size: 0 500px; /* estimated height for scrollbar */
```

`content-visibility: auto` is particularly valuable for long pages with many sections — the browser only renders what's in or near the viewport.

### `will-change`

`will-change` promotes an element to its own compositing layer, enabling GPU-accelerated transforms and opacity. Use it for elements you know will animate, remove it after:

```css
/* Apply before animation starts */
.card:hover { will-change: transform; }

/* Don't apply to everything — each layer costs GPU memory */
/* Bad: * { will-change: transform; } */
```

---

## 2. Loading Performance <a name="loading"></a>

The most critical moment in the user experience is from request to usable interface. All your craft work is invisible until the page loads. The goal: show meaningful content as fast as possible, without jarring shifts as late-loading content arrives.

### Font Loading

Custom fonts are render-blocking by default. Without intervention, the user sees invisible text (Flash of Invisible Text, or FOIT) until the font downloads.

**`font-display` strategy:**
- `font-display: swap` — shows fallback font immediately, swaps when custom font loads. User sees a brief flash of different typography but can read immediately.
- `font-display: optional` — uses custom font only if already cached. No layout shift, but first-time visitors see the fallback. Best for body text where the fallback is acceptable.

**Font preloading:** For critical fonts (headlines, brand text), preload them so the browser starts downloading immediately:

```html
<link rel="preload" href="/fonts/brand.woff2" as="font" type="font/woff2" crossorigin>
```

**Subsetting:** If you only use Latin characters, don't load the full Unicode range. Most font services offer subset options. The difference can be 100KB vs 20KB per weight.

**Fallback font matching:** Choose a system font fallback that closely matches your custom font's metrics (x-height, character width). Use `size-adjust`, `ascent-override`, and `descent-override` in `@font-face` to fine-tune the match. This minimizes layout shift when the swap happens.

### Image Optimization

**Lazy loading:** Images below the fold shouldn't block initial render:

```html
<!-- Below-fold images -->
<img src="chart.webp" loading="lazy" alt="...">

<!-- Above-fold hero images — do NOT lazy load these -->
<img src="hero.webp" alt="...">
```

**Reserve space:** Always provide dimensions or use `aspect-ratio` to prevent layout shift when images load:

```css
.chart-container {
  aspect-ratio: 16 / 9;
  background: var(--surface-alt); /* placeholder color */
}
```

**Modern formats:** WebP and AVIF offer significantly smaller file sizes than PNG/JPEG at equivalent quality. Use `<picture>` with fallbacks for broad compatibility.

### Cumulative Layout Shift (CLS)

Layout shift happens when visible elements change position after initial render. Common causes and fixes:

- **Images without dimensions** → always set `width`/`height` or `aspect-ratio`
- **Font swap** → match fallback metrics, use `font-display: optional` for body
- **Dynamic content above the fold** → reserve space with skeleton placeholders
- **Injected banners/bars** → use `transform` to animate in rather than pushing content down

### Skeleton Screens

When content loads asynchronously, show skeleton placeholders that match the layout shape. Skeletons maintain perceived performance, prevent CLS, and give spatial context (unlike a generic spinner).

The skeleton should reflect the actual content structure: if you're loading a card with a title, two lines of text, and a metric, the skeleton shows gray blocks in those positions. Use a subtle pulse animation on the skeleton — but animate `opacity`, not `background-color`.

### Code Splitting

For applications with multiple routes or heavy features, don't load everything upfront. Split at route boundaries and for heavy components (charts, rich text editors, map widgets). The mechanism depends on your framework — lazy imports, dynamic `import()`, or framework-specific code splitting. The principle: the user shouldn't download code for pages they haven't visited.

---

## 3. Accessibility <a name="accessibility"></a>

An interface that only works for sighted mouse users is unfinished — the same way an interface without error states is unfinished. Accessibility isn't a compliance exercise bolted on at the end. It's part of the design contract: the interface works for the people who use it, however they use it.

### Color Contrast

Text must be readable. WCAG 2.1 AA requires:
- **4.5:1** contrast ratio for normal text (under ~18px)
- **3:1** for large text (18px+ bold or 24px+ regular)
- **3:1** for UI components and graphical elements (icons, borders, focus indicators)

This constrains the subtlety principle. Your muted/tertiary text levels still need to meet 4.5:1 against their background. Check contrast ratios for every text token against every surface it appears on — especially in dark mode, where it's easy to slip below threshold.

Interactive elements need sufficient contrast in all states: default, hover, focus, disabled. A disabled button that's invisible against the surface isn't "subtle" — it's inaccessible.

### Keyboard Navigation

Every interactive element must be reachable and operable via keyboard. Native HTML elements (`<button>`, `<a>`, `<input>`, `<select>`) handle this automatically. When you build custom components, you take on that responsibility.

**Custom dropdowns/selects:**
- Trigger opens with Enter or Space
- Arrow keys navigate options
- Enter selects, Escape closes
- Focus returns to trigger on close
- `role="listbox"` or `role="menu"` with `role="option"` children
- `aria-expanded` on the trigger
- `aria-activedescendant` for the highlighted option

**Custom checkboxes/toggles:**
- Space toggles the state
- `role="checkbox"` or `role="switch"` with `aria-checked`

**Modals/overlays:**
- Focus traps inside the modal (Tab cycles within, doesn't escape to background)
- Escape closes the modal
- Focus returns to the element that opened it
- `role="dialog"` with `aria-modal="true"`
- Background content gets `aria-hidden="true"` or `inert`

### Focus Management

**`focus-visible`** shows focus rings only for keyboard users, not mouse clicks. This is the right default for all interactive elements — it satisfies accessibility without adding visual noise for mouse users:

```css
:focus { outline: none; }
:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }
```

**Focus order** should follow visual reading order. If your layout reorders elements with CSS Grid or Flexbox, verify that Tab order still makes sense.

### Semantic HTML

Use the right element for the job. Semantic HTML gives screen readers structure for free:

- `<nav>` for navigation regions
- `<main>` for primary content
- `<aside>` for sidebars
- `<article>` for self-contained content
- `<section>` with `aria-labelledby` for labeled regions
- `<h1>`–`<h6>` in order, without skipping levels
- `<button>` for actions, `<a>` for navigation

A `<div>` with an `onClick` handler is not a button. It has no keyboard behavior, no screen reader role, no focus indicator. Use `<button>`.

### Live Regions

Dynamic content updates (notifications, status changes, form validation messages) need to announce themselves to screen readers:

```html
<!-- Polite: announces after current speech finishes -->
<div aria-live="polite">3 items updated</div>

<!-- Assertive: interrupts immediately (use sparingly) -->
<div aria-live="assertive">Error: payment failed</div>
```

### Motion Preferences

Some users have vestibular disorders triggered by animation. Respect their preference:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

This doesn't remove interactions — it makes them instant instead of animated. The interface still responds; it just doesn't move.

### Color Scheme Preferences

Detect the user's system preference for dark/light mode:

```css
@media (prefers-color-scheme: dark) {
  :root { /* dark mode tokens */ }
}
```

If you support manual theme switching, use a data attribute (`[data-theme="dark"]`) that overrides the media query preference.

---

## 4. Responsive Implementation <a name="responsive"></a>

Responsive design is not "make it work on mobile too." It's designing the interface to communicate clearly at every viewport width. The information hierarchy, interaction patterns, and visual density should all adapt intentionally.

### Fluid Typography

Use `clamp()` so type scales smoothly between viewport sizes without breakpoint jumps:

```css
/* Minimum 16px, scales with viewport, maximum 20px */
font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
```

Apply to headline sizes especially — a 48px headline that works on desktop is overwhelming on a 375px phone. Body text usually needs less scaling (16px is readable on most screens).

### Container Queries

Components often need to adapt based on their container size, not the viewport. A card in a sidebar has different space than the same card in a main content area:

```css
.card-container { container-type: inline-size; }

@container (min-width: 400px) {
  .card { flex-direction: row; }
}
@container (max-width: 399px) {
  .card { flex-direction: column; }
}
```

Container queries make components genuinely reusable across different layout contexts.

### Touch Targets

On touch devices, fingers are imprecise. Minimum touch target size: 44×44 CSS pixels (Apple HIG) or 48×48 (Material). This applies to buttons, links, checkboxes, dropdown triggers, close buttons, and anything else the user taps.

If the visual element is smaller (a 24px icon button), extend the touch target with padding or a pseudo-element:

```css
.icon-button {
  position: relative;
  /* Visual size */
  width: 24px; height: 24px;
}
.icon-button::before {
  content: '';
  position: absolute;
  /* Touch target size */
  inset: -12px;
}
```

### Layout Adaptation

Common patterns for how desktop layouts map to mobile:

- **Sidebar → off-canvas or bottom nav.** Don't just hide the sidebar — rethink navigation for the context. Bottom nav works for primary destinations (up to 5 items). Off-canvas hamburger works for secondary/complex navigation.
- **Multi-column → single column.** Cards and content blocks restack. Prioritize what appears first — it should be what the user came for, not the least important widget that happened to be on the left.
- **Data tables → cards or summary view.** Wide tables don't fit on narrow screens. Consider: which columns are essential? Can non-essential data move to an expandable detail view?
- **Hover interactions → long-press or tap-to-reveal.** Hover doesn't exist on touch devices. Any information or action gated behind hover needs an alternative.

### Viewport Quirks

- **`100vh` on mobile** includes the URL bar height, which changes as you scroll. Use `100dvh` (dynamic viewport height) or `100svh` (small viewport height) for full-screen layouts.
- **Safe areas on notched devices** use `env(safe-area-inset-*)` to prevent content from being obscured by the notch or home indicator.

---

## 5. Large Dataset Handling <a name="datasets"></a>

Dashboards, admin panels, and data tools — the primary use cases for this skill — routinely display large datasets. Rendering thousands of DOM nodes kills performance. The solution isn't always "paginate" — it depends on the use case.

### Virtualization

Virtual scrolling renders only the rows/items visible in the viewport (plus a small buffer). The DOM stays lightweight regardless of dataset size. The user sees a normal scrollbar and smooth scrolling.

When to virtualize: tables or lists exceeding ~100 items where the user scrolls through rather than paginating. The exact threshold depends on row complexity — a simple text row handles more DOM nodes than a row with multiple interactive elements.

The implementation depends on your framework. The principle: calculate which items are visible, render only those, and translate the rendered block to the correct scroll position.

### Debouncing and Throttling

Interactive filters, search inputs, and resize handlers can fire events dozens of times per second. Without control, each event triggers re-renders, API calls, or expensive calculations.

**Debounce** (wait for pause): For search/filter inputs. Don't fire until the user stops typing for N milliseconds (150-300ms is typical). Each keystroke resets the timer.

**Throttle** (limit frequency): For scroll and resize handlers. Fire at most once per N milliseconds. The event still fires, just at a controlled rate.

### Pagination Strategies

| Strategy | Best For | Tradeoff |
|---|---|---|
| Page numbers | Known dataset size, random access needed | User can jump to any page, but loses scroll context |
| Infinite scroll | Social feeds, discovery UX | Smooth browsing, but hard to find "where I was" |
| Virtual scroll | Large tables, audit logs, data grids | Handles any size, but adds implementation complexity |
| Load more button | Moderate datasets, user-controlled | Simple, explicit, but less fluid than infinite scroll |

### Progressive Loading

For data-heavy dashboards, don't block the entire view waiting for all data. Show the layout immediately with skeleton placeholders, then fill in sections as data arrives. Each widget can have its own loading state — the user sees progress and can start reading completed sections while others load.

---

## 6. Error & Edge States <a name="errors"></a>

Errors are a design opportunity. A well-crafted error state maintains the user's trust and gives them a path forward. A generic "Something went wrong" breaks both.

### Error Boundaries

In component-based frameworks, an unhandled error in one component can crash the entire view. Error boundaries catch these and render fallback UI at the boundary instead of losing the whole page.

Place error boundaries strategically: around each independent widget in a dashboard, around route-level content, around third-party components. The principle: a broken chart shouldn't take down the sidebar.

### Error State Design

Error states should be specific, helpful, and actionable:

- **What happened** — in plain language, not technical jargon or error codes
- **Why** — if known, a brief cause (network issue, permission, invalid data)
- **What to do** — a concrete action (retry button, link to fix the issue, "try again later")

Error messages appear where the error occurred, not in a disconnected toast or modal. If a chart fails to load, the error replaces the chart — the user sees exactly what's broken.

### Network Awareness

Interfaces exist on unreliable networks. Account for:

- **Optimistic updates** — update the UI immediately, roll back if the server rejects. Feels instant, handles the common (success) case without waiting.
- **Retry with feedback** — show a retry button with context. "Couldn't save. Retry?" is better than silently failing.
- **Offline indicators** — if the app can't function without a connection, show that state clearly rather than letting the user interact with a broken interface.

### Form Validation

- **Validate on blur** for individual fields (immediate feedback without interrupting typing)
- **Validate on submit** for cross-field rules (dependencies between fields)
- **Clear errors on re-input** — once the user starts correcting a field, remove the error. Don't make them submit again to clear it.
- **Place errors adjacent to the field**, not in a summary block at the top. The user's eye is on the field they're editing.

### Empty States

An empty state (no data yet, no search results, empty inbox) isn't blank — it's an opportunity. Show what this area will contain, how to populate it, or what to do next. An empty table with "No results found" is functional. An empty table with "No projects yet — create your first one" with a clear call to action is designed.