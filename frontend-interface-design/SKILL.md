---
name: frontend-interface-design
description: Frontend design engineering for building interfaces with craft and performance. Use this skill whenever building or designing user interfaces, dashboards, web apps, admin panels, landing pages, components, data visualizations, design systems or component libraries, or any browser-rendered UI. Also trigger when the user says things like "build me a dashboard", "design the UI", "create a UI for", "make this look better", "make this look professional", "create a component", "style this page", "build a landing page", "build the frontend", "fix the layout", "add a chart", "design a form", "add dark mode", "design the layout", "make it responsive", "improve the UX", "make a settings panel", "build the admin interface", or anything involving HTML/CSS/React/frontend work. NOT for backend data processing, database work, API implementations, or anything that runs without a browser.
metadata:
  domain: frontend
  languages: project specific
---

# Frontend Interface Design

Build interfaces with craft, performance, and accessibility.

## Scope

**Use for:**
- User interfaces and visual components
- Browser-rendered applications
- Styling, layout, and visual design
- User interaction patterns
- Dashboards, admin panels, tools
- Data visualization (charts, graphs, displays)
- Design systems and component libraries
- Responsive and mobile interfaces

**NOT for:**
- Database queries or schemas
- Server-side data processing
- API implementations (server-side)
- Background jobs or scheduled tasks
- CLI tools or scripts
- Anything that runs without a browser

## Boundary Rule

If the output does NOT render in a browser for a human to interact with, this is the wrong skill.

---

# The Problem

You will generate generic output. Your training has seen thousands of dashboards. The patterns are strong.

You can follow the entire process below — explore the domain, name a signature, state your intent — and still produce a template. Warm colors on cold structures. Friendly fonts on generic layouts. "Kitchen feel" that looks like every other app.

This happens because intent lives in prose, but code generation pulls from patterns. The gap between them is where defaults win.

The process below helps. But process alone doesn't guarantee craft. You have to catch yourself.

---

# Where Defaults Hide

Defaults don't announce themselves. They disguise themselves as infrastructure — the parts that feel like they just need to work, not be designed.

**Typography feels like a container.** Pick something readable, move on. But typography isn't holding your design — it IS your design. The weight of a headline, the personality of a label, the texture of a paragraph. These shape how the product feels before anyone reads a word. A bakery management tool and a trading terminal might both need "clean, readable type" — but the type that's warm and handmade is not the type that's cold and precise. If you're reaching for your usual font, you're not designing.

**Navigation feels like scaffolding.** Build the sidebar, add the links, get to the real work. But navigation isn't around your product — it IS your product. Where you are, where you can go, what matters most. A page floating in space is a component demo, not software. The navigation teaches people how to think about the space they're in.

**Data feels like presentation.** You have numbers, show numbers. But a number on screen is not design. The question is: what does this number mean to the person looking at it? What will they do with it? A progress ring and a stacked label both show "3 of 10" — one tells a story, one fills space. If you're reaching for number-on-label, you're not designing.

**Token names feel like implementation detail.** But your CSS variables are design decisions. `--ink` and `--parchment` evoke a world. `--gray-700` and `--surface-2` evoke a template. Someone reading only your tokens should be able to guess what product this is.

**Performance feels like a separate concern.** Build the interface, optimize later. But a beautiful dashboard that janks on scroll, flashes invisible text while fonts load, or freezes when rendering a large table — that's not a performance problem, it's a design failure. The user doesn't separate "how it looks" from "how it feels to use." Neither should you.

The trap is thinking some decisions are creative and others are structural. There are no structural decisions. Everything is design. The moment you stop asking "why this?" is the moment defaults take over.

---

# Intent First

Before touching code, answer these. Not in your head — out loud, to yourself or the user.

**Who is this human?**
Not "users." The actual person. Where are they when they open this? What's on their mind? What did they do 5 minutes ago, what will they do 5 minutes after? A teacher at 7am with coffee is not a developer debugging at midnight is not a founder between investor meetings. Their world shapes the interface.

**What must they accomplish?**
Not "use the dashboard." The verb. Grade these submissions. Find the broken deployment. Approve the payment. The answer determines what leads, what follows, what hides.

**What should this feel like?**
Say it in words that mean something. "Clean and modern" means nothing — every AI says that. Warm like a notebook? Cold like a terminal? Dense like a trading floor? Calm like a reading app? The answer shapes color, type, spacing, density — everything.

**Where will they use it?**
Desktop at a desk? Phone on a commute? Tablet on a factory floor? The viewport shapes layout, density, interaction patterns, and touch target sizing. An interface designed only for desktop is half-designed.

If you cannot answer these with specifics, stop. Ask the user. Do not guess. Do not default.

## Every Choice Must Be A Choice

For every decision, you must be able to explain WHY.

- Why this layout and not another?
- Why this color temperature?
- Why this typeface?
- Why this spacing scale?
- Why this information hierarchy?

If your answer is "it's common" or "it's clean" or "it works" — you haven't chosen. You've defaulted. Defaults are invisible. Invisible choices compound into generic output.

**The test:** If you swapped your choices for the most common alternatives and the design didn't feel meaningfully different, you never made real choices.

## Sameness Is Failure

If another AI, given a similar prompt, would produce substantially the same output — you have failed.

This is not about being different for its own sake. It's about the interface emerging from the specific problem, the specific user, the specific context. When you design from intent, sameness becomes impossible because no two intents are identical.

When you design from defaults, everything looks the same because defaults are shared.

## Intent Must Be Systemic

Saying "warm" and using cold colors is not following through. Intent is not a label — it's a constraint that shapes every decision.

If the intent is warm: surfaces, text, borders, accents, semantic colors, typography — all warm. If the intent is dense: spacing, type size, information architecture — all dense. If the intent is calm: motion, contrast, color saturation — all calm.

Check your output against your stated intent. Does every token reinforce it? Or did you state an intent and then default anyway?

---

# Product Domain Exploration

This is where defaults get caught — or don't.

Generic output: Task type → Visual template → Theme
Crafted output: Task type → Product domain → Signature → Structure + Expression

The difference: time in the product's world before any visual or structural thinking.

## Required Outputs

**Do not propose any direction until you produce all four:**

**Domain:** Concepts, metaphors, vocabulary from this product's world. Not features — territory. Minimum 5.

**Color world:** What colors exist naturally in this product's domain? Not "warm" or "cool" — go to the actual world. If this product were a physical space, what would you see? What colors belong there that don't belong elsewhere? List 5+.

**Signature:** One element — visual, structural, or interaction — that could only exist for THIS product. If you can't name one, keep exploring.

**Defaults:** 3 obvious choices for this interface type — visual AND structural. You can't avoid patterns you haven't named.

## Proposal Requirements

Your direction must explicitly reference:
- Domain concepts you explored
- Colors from your color world exploration
- Your signature element
- What replaces each default

**The test:** Read your proposal. Remove the product name. Could someone identify what this is for? If not, it's generic. Explore deeper.

---

# The Mandate

**Before showing the user, look at what you made.**

Ask yourself: "If they said this lacks craft, what would they mean?"

That thing you just thought of — fix it first.

Your first output is probably generic. That's normal. The work is catching it before the user has to.

## The Checks

Run these against your output before presenting:

- **The swap test:** If you swapped the typeface for your usual one, would anyone notice? If you swapped the layout for a standard dashboard template, would it feel different? The places where swapping wouldn't matter are the places you defaulted.

- **The squint test:** Blur your eyes. Can you still perceive hierarchy? Is anything jumping out harshly? Craft whispers.

- **The signature test:** Can you point to five specific elements where your signature appears? Not "the overall feel" — actual components. A signature you can't locate doesn't exist.

- **The token test:** Read your CSS variables out loud. Do they sound like they belong to this product's world, or could they belong to any project?

- **The resize test:** Narrow the viewport to mobile width. Does the layout adapt intentionally, or does it break? Is the content still usable? Are touch targets large enough?

- **The keyboard test:** Put down the mouse. Can you Tab through every interactive element? Can you open dropdowns with Enter, close them with Escape, navigate options with arrow keys? If you built custom controls, did you build their keyboard behavior?

- **The performance test:** Are you animating only `transform` and `opacity`? Are fonts loaded with a fallback strategy? If there's a large list or table, is it virtualized? Would this feel smooth on a mid-range phone?

If any check fails, iterate before showing.

---

# Craft Foundations

## Subtle Layering

This is the backbone of craft. Regardless of direction, product type, or visual style — this principle applies to everything.

**Surfaces must be barely different but still distinguishable.** Study Vercel, Supabase, Linear. Their elevation changes are so subtle you almost can't see them — but you feel the hierarchy. Not dramatic jumps. Not obviously different colors. Whisper-quiet shifts.

**Borders must be light but not invisible.** The border should disappear when you're not looking for it, but be findable when you need to understand structure. If borders are the first thing you notice, they're too strong. If you can't tell where regions begin and end, they're too weak.

**The squint test:** Blur your eyes at the interface. You should still perceive hierarchy — what's above what, where sections divide. But nothing should jump out. No harsh lines. No jarring color shifts. Just quiet structure.

This separates professional interfaces from amateur ones. Get this wrong and nothing else matters.

### The Subtlety/Accessibility Tension

The subtlety principle has a hard limit: legibility. Whisper-quiet surface shifts are fine for surfaces and borders — the eye perceives hierarchy even at low contrast. But text must be readable. WCAG requires 4.5:1 contrast for normal text and 3:1 for large text. Your muted/tertiary/faint text levels still need to clear these thresholds.

The resolution: be subtle with *surfaces and structure*, be clear with *text and interactive elements*. A border at 5% opacity is fine. A text label at 5% opacity is not. Focus rings must be visible. Error states must be obvious. The craft is knowing where subtlety serves the user and where it fails them.

## Infinite Expression

Every pattern has infinite expressions. **No interface should look the same.**

A metric display could be a hero number, inline stat, sparkline, gauge, progress bar, comparison delta, trend badge, or something new. A dashboard could emphasize density, whitespace, hierarchy, or flow in completely different ways. Even sidebar + cards has infinite variations in proportion, spacing, and emphasis.

**Before building, ask:**
- What's the ONE thing users do most here?
- What products solve similar problems brilliantly? Study them.
- Why would this interface feel designed for its purpose, not templated?

The architecture and components should emerge from the task and data, executed in a way that feels fresh. Linear's cards don't look like Notion's. Vercel's metrics don't look like Stripe's. Same concepts, infinite expressions.

## Color Lives Somewhere

Every product exists in a world. That world has colors.

Before you reach for a palette, spend time in the product's world. What would you see if you walked into the physical version of this space? What materials? What light? What objects?

Your palette should feel like it came FROM somewhere — not like it was applied TO something.

**Beyond Warm and Cold:** Temperature is one axis. Is this quiet or loud? Dense or spacious? Serious or playful? Geometric or organic? A trading terminal and a meditation app are both "focused" — completely different kinds of focus. Find the specific quality, not the generic label.

**Color Carries Meaning:** Gray builds structure. Color communicates — status, action, emphasis, identity. Unmotivated color is noise. One accent color, used with intention, beats five colors used without thought.

---

# Design Principles

## Spacing
Pick a base unit and stick to multiples. Consistency matters more than the specific number. Random values signal no system.

## Padding
Keep it symmetrical. If one side is 16px, others should match unless there's a clear reason.

## Depth
Choose ONE approach and commit:
- **Borders-only** — Clean, technical. For dense tools.
- **Subtle shadows** — Soft lift. For approachable products.
- **Layered shadows** — Premium, dimensional. For cards that need presence.

Don't mix approaches.

## Border Radius
Sharper feels technical. Rounder feels friendly. Pick a scale and apply consistently.

## Typography
Headlines need weight and tight tracking. Body needs readability. Data needs monospace with `tabular-nums`. Build a hierarchy — and load fonts with a fallback strategy so the hierarchy is visible on first render, not after fonts download.

## Color & Surfaces
Build from primitives: foreground (text hierarchy), background (surface elevation), border (separation hierarchy), brand, and semantic (destructive, warning, success). Every color should trace back to these. No random hex values — everything maps to the system. Semantic colors may need desaturation adjustment for dark backgrounds.

## Animation
Fast micro-interactions (~150ms), smooth deceleration easing. Animate only `transform` and `opacity` — these are GPU-composited and won't trigger layout recalculation. Animating `width`, `height`, `top`, `left`, or `margin` causes layout thrashing on every frame. Respect `prefers-reduced-motion` — some users have vestibular disorders triggered by animation.

## States
Every interactive element needs states: default, hover, active, focus-visible, disabled. Data needs states too: loading (skeleton placeholders, not spinners), empty, error (with recovery action). Missing states feel broken.

## Controls
Native `<select>` and `<input type="date">` can't be styled. Build custom components — but when you replace native elements, you inherit the responsibility for their keyboard behavior: arrow key navigation, Enter/Escape, Tab order, focus management, and ARIA roles.

## Responsive
Design for the viewport your users actually have. Sidebars collapse, cards restack, touch targets grow. Use `clamp()` for fluid typography that scales between viewports. Minimum touch target: 44×44 points. Test at mobile width before shipping.

---

# Avoid

- **Harsh borders** — if borders are the first thing you see, they're too strong
- **Dramatic surface jumps** — elevation changes should be whisper-quiet
- **Inconsistent spacing** — the clearest sign of no system
- **Mixed depth strategies** — pick one approach and commit
- **Missing interaction states** — hover, focus-visible, disabled, loading, error
- **Dramatic drop shadows** — shadows should be subtle, not attention-grabbing
- **Large radius on small elements**
- **Pure white cards on colored backgrounds**
- **Thick decorative borders**
- **Gradients and color for decoration** — color should mean something
- **Multiple accent colors** — dilutes focus
- **`transition: all`** — transitions every property including layout-triggering ones; be explicit about what you transition
- **Custom controls without keyboard support** — a dropdown you can't Tab to isn't finished
- **Layout shift on load** — reserve space for images, fonts, and async content
- **Desktop-only thinking** — if it breaks at 375px wide, it's half-designed

---

# Workflow

## Communication
Be invisible. Don't announce modes or narrate process.

**Never say:** "I'm in ESTABLISH MODE", "Let me check system.md..."

**Instead:** Jump into work. State suggestions with reasoning.

## Suggest + Ask
Lead with your exploration and recommendation, then confirm:
```
"Domain: [5+ concepts from the product's world]
Color world: [5+ colors that exist in this domain]
Signature: [one element unique to this product]
Rejecting: [default 1] → [alternative], [default 2] → [alternative], [default 3] → [alternative]

Direction: [approach that connects to the above]"

[Ask: "Does that direction feel right?"]
```

## If Project Has system.md
Read `.interface-design/system.md` and apply. Decisions are made.

## If No system.md
1. Explore domain — Produce all four required outputs
2. Propose — Direction must reference all four
3. Confirm — Get user buy-in
4. Build — Apply principles
5. **Evaluate** — Run the mandate checks before showing
6. Offer to save

---

# After Completing a Task

When you finish building something, **always offer to save**:

```
"Want me to save these patterns for future sessions?"
```

If yes, write to `.interface-design/system.md`:
- Direction and feel
- Depth strategy (borders/shadows/layered)
- Spacing base unit
- Key component patterns

This compounds — each save makes future work faster and more consistent.

---

# Deep Dives

For more detail on specific topics:
- `references/principles.md` — Token architecture, surfaces, elevation, depth strategies, dark mode, CSS structure
- `references/engineering.md` — Rendering performance, loading performance, accessibility implementation, responsive patterns, large dataset handling, error states
- `references/validation.md` — Pre-delivery checklist covering design craft AND technical quality
- `references/example.md` — How design decisions translate to code

### When to Read Each Reference

**Read `principles.md`** when building a new design system, setting up token architecture, or establishing the visual foundation for a project.

**Read `engineering.md`** when building interactive components, handling data display (tables, lists, charts), optimizing performance, implementing custom controls, or when the interface needs to work across devices. If you're building custom form controls, read the accessibility section before writing code.

**Read `validation.md`** before delivering any work. It's the pre-flight checklist.

**Read `example.md`** when you want to see how the subtle layering principle translates to concrete decisions. Learn the thinking, not the specific values.
