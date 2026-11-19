# QuantumRoute AI UX Contract

## Product context

- Audience: capstone evaluators, transport researchers, and authenticated project users.
- Primary jobs: configure a scenario, execute routing algorithms, compare evidence, revisit history, and export a report.
- Target market: Chandigarh, India.
- Active locale: `en-IN`; display timezone `Asia/Kolkata`; Gregorian calendar.
- Accessibility target: WCAG 2.2 AA.

## Business-context sources

The user brief and backend API schemas are the current product contract. Server role and ownership checks are authoritative for permissions. No billing, regulated deletion, or legal-copy workflow exists in this release.

## Visual contract

- Project context: `DESIGN.md`.
- Runtime canonical owner: `frontend/src/index.css` variables and shared UI components.
- Themes: light, dark, and system selection.
- Drift gate: strict premium UI audit plus frontend build and lint.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Native `<select>` styled by the owning form | Typed API location and enum schemas | Compact and full-width | Keyboard + browser popup |
| Date | Native `<input type="time">` in `OptimizePage.tsx` | `OptimizeRequest.time_of_day` (`HH:MM`) | Browser-native locale presentation only | Keyboard entry + optimization request |
| Form | React Hook Form + Zod | Shared frontend schemas and Pydantic request models | Authentication and optimization | Unit + browser flow |
| Scrollbar | `src/index.css` | Design tokens | Stable-gutter panel | Computed style |
| Toast/status | Inline `role=status/alert` owner | Mutation/query state | Success, warning, and error | Accessibility test |
| CRUD | Service modules + React Query | PostgreSQL-backed API | Return and stay | End-to-end flow |

Native selects and the native time picker are an explicit ownership decision: platform popup geometry and locale behavior are accepted for reliable keyboard and mobile interaction. QuantumRoute owns their visible labels, validation, recovery messages, and layout, but does not claim to style the opened platform popup.

## Flow ledger

| Operation | Pending | Success | Failure recovery | Focus outcome |
|---|---|---|---|---|
| Optimize route | Stable progress panel; submit disabled; scenario changes debounce 650ms after the first run | Results and OSRM road geometry replace the prior run; changed paths name the triggering inputs and show measured decision factors; history invalidates | Inputs remain; OSRM failure is labelled and uses waypoint geometry; optimization can be retried | Recommendation heading |
| Sign in/register | Button spinner; duplicate submit blocked | Dashboard | Generic inline error; entered email remains | Error banner or dashboard heading |
| Export report | Row action busy | Browser download | Inline row error and retry | Trigger retained |
| Toggle user | Confirmation dialog and disabled action | Row status updates | Dialog stays open with retry | Trigger or next row |
| Search/history | 300ms debounce, stale requests ignored | URL-backed result set | Persistent retry state | Search input |

## Navigation and responsive behavior

Each route has a unique document title. Authenticated users without administrator permission see an access-denied screen. The sidebar becomes an app-owned drawer below the desktop breakpoint. Tables scroll within their panel and never impose viewport height on sibling forms.

## Async and resilience

Mutations are pessimistic and idempotent at the UI boundary. Active route requests time out with a retry path. Cached results remain visible during refresh. A 401 clears the safe local user shell and returns to sign-in with the intended path; secrets are never stored client-side.

## Validation and permissions

All product forms use `noValidate`, text errors, field association, first-error focus, and stable busy buttons. Admin controls are hidden from navigation for non-admins and guarded again by the server; direct access displays 403. The final active administrator cannot be disabled.

## Verification

- Backend: `backend/.venv/bin/pytest -q`.
- Frontend: `npm run lint`, `npm run build`.
- Premium audit: strict skill audit against repository root.
- Browser: sign-in, optimization success/failure, route toggles, empty history, export, themes, keyboard, narrow viewport, reduced motion.
