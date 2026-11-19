---
version: "1.0"
name: "QuantumRoute AI"
description: "An urban mobility control room for reproducible hybrid route experiments."
colors:
  canvas: "#07111F"
  surface: "#0C1A2B"
  panel: "#122238"
  primary: "#2F7CF6"
  quantum: "#9B7BFF"
  cyan: "#37C9D8"
  warning: "#F5B642"
  danger: "#F06464"
  success: "#3BC98A"
  text: "#EAF2FF"
  muted: "#91A4BE"
typography:
  display:
    fontFamily: "Space Grotesk, Inter, system-ui, sans-serif"
  sans:
    fontFamily: "Inter, system-ui, sans-serif"
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
rounded:
  DEFAULT: "0.75rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
spacing:
  section-gap: "1.5rem"
  page-max: "100rem"
components:
  button: {}
  card: {}
  input: {}
  table: {}
  map: {}
---

# QuantumRoute AI Design System

## Overview

### Creative North Star

The interface takes its visual logic from a city traffic operations room: quiet dark instrumentation, luminous route traces, cartographic layers, and dense but legible measurements. The map is the signature surface. Quantum results use violet; verified recommendations use transit blue; operational states keep stable semantic colors.

### Product context and register

- **Audience and primary job:** engineering evaluators, students, and transport researchers configuring and inspecting route experiments.
- **Target market:** Chandigarh capstone and invention demonstrations, established by the project brief and curated city network.
- **Locale:** English UI, Indian number/currency conventions, Asia/Kolkata display time.
- **Usage scene:** laptop-first analysis, with responsive read-only comparison on mobile.
- **Register:** authenticated technical product.
- **Memorable signature:** the map and its route-selection rail read as one analytical instrument.
- **Restraint:** forms, history, authentication, and reports use familiar controls without decorative effects.
- **Anti-references:** generic gradient-heavy AI dashboards, fictional KPI grids, glass effects that reduce map legibility, and decorative quantum imagery.
- **Token ownership:** runtime CSS variables in `frontend/src/index.css` are canonical; this document mirrors their accepted semantic values.

## Colors

The navy scale separates canvas, navigation, and panels without relying on heavy shadow. Blue marks the verified recommendation, violet marks QAOA evidence, cyan marks traffic modeling, amber marks scenario assumptions, red marks failures, and green marks completed measured runs. Light mode remaps semantic tokens while preserving their meaning.

## Typography

Space Grotesk is reserved for product identity and page titles. Inter carries controls and prose. IBM Plex Mono or a metric-compatible system monospace carries timings, coordinates, energies, and identifiers. UI copy uses sentence case; data units stay adjacent to values.

## Layout

The route workspace uses a 360px parameter rail and a flexible map/results canvas above 1280px, then a single document flow. Page content is capped at 100rem. Tables own horizontal overflow; pages retain natural vertical scrolling. Async regions reserve their final minimum height.

## Elevation & Depth

Hierarchy uses tonal surfaces and 1px borders. Shadows are limited to floating menus and map controls. The map remains visually behind controls; blur is never placed over dense route data.

## Shapes

Controls use 8px radii and analytical panels use 12–16px radii. Status pills are the only fully rounded controls. Route strokes are rounded for map readability.

## Components

### Foundational visual states

All interactive controls include hover, visible focus, pressed, disabled, busy, and error states. Loading uses a stable app-owned spinner. Empty and failure panels keep the same footprint as populated data.

### Buttons and actions

Buttons combine emphasis (solid, outline, ghost) and intent (brand, neutral, success, warning, danger). Busy buttons retain their dimensions. Icon-only actions require names and tooltips.

### Navigation and data display

Navigation groups Route workspace, Experiments, and Account/System. Tables remain semantic and horizontally scroll on narrow screens. Charts always have a tabular or textual equivalent.

### Forms and overlays

The existing shared Input and Select owners are extended. Native selects are an explicit choice for predictable macOS accessibility. Product forms own validation and use `noValidate`. Destructive actions require an app dialog.

### Iconography

Lucide supplies 16–20px outline icons. Icons support labels rather than replacing unfamiliar actions.

### Motion

Motion communicates page arrival, route selection, and job progress at 150–300ms. Reduced-motion mode removes transforms and stagger delays.

### Content and data visualization

Copy distinguishes measured executions, scenario estimates, synthetic-model outputs, fallbacks, and unavailable results. Charts never compare unlike units on one axis and never invent empty-state values.

## Do's and Don'ts

- **Do:** keep the verified recommendation visually distinct from experimental QAOA selection.
- **Do:** show provenance and units beside performance evidence.
- **Do:** label OSRM road-following geometry and expose its fallback state.
- **Don't:** use random fallback metrics or imply live traffic.
- **Don't:** use gradients as structural decoration or hide actions behind hover.
