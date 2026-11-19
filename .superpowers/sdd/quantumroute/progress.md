# SDD ledger — plan: approved QuantumRoute AI blueprint in chat

Ruling: the archive has no writable Git metadata or plan file, so execution uses this workspace and ledger without commits or generated task briefs.

Task 1: complete — source extracted without archived dependencies; frontend baseline build passed; baseline lint reported 22 warnings.
Task 2: complete — shared routing objective, classical solvers, QUBO, Aer QAOA, and synthetic traffic pipeline; 14 backend tests pass.
Task 3: complete — cookie authentication, PostgreSQL persistence/migrations, analytics, admin controls, exports, responsive frontend, and truthful evidence surfaces are integrated.

Final verification (2026-11-18):

- Backend: `14 passed`; Python compile check passed.
- Database: Alembic reported `No new upgrade operations detected` against PostgreSQL.
- Frontend: lint passed with zero findings; TypeScript/Vite production build passed.
- Design: strict premium UI audit passed with zero findings.
- Browser: authentication, admin authorization/health, Aer optimization, ML evidence, simulation, responsive navigation, settings, route history, and PDF/CSV/XLSX report exports verified.
- Hygiene: temporary E2E user, sessions, and four owned route records were removed; three pre-existing users remain.

Scenario and road-geometry enhancement (2026-11-18):

- Added cached OSRM full-GeoJSON geometry for every classical, QAOA, and priority route, with explicit waypoint fallback provenance.
- Scenario controls now debounce and automatically recompute after the first run; QAOA-only controls remain explicit.
- Verified Car/Truck/Emergency cost changes and Shortest/Least Traffic path changes in the browser.
- Fixed QUBO penalty validation so raw route costs above 2.0 are normalized before the one-hot penalty check.
- Evidence: `21 passed` backend, `2 passed` frontend, clean lint/build, clean strict UI audit, no Alembic drift, and 441 OSRM road points for a four-landmark result.
- Hygiene: the OSRM E2E user, one session, and six owned route records were removed; four unrelated users remain.

Runtime correction and route reasoning (2026-11-18):

- Identified that standard ports `5173/8000` were serving an older `Capstone Codex copy` workspace whose map preferred straight edge geometry.
- Replaced those processes with the current workspace on the standard ports; the live renderer now prefers OSRM full-road coordinates.
- Added scenario-specific recommendation factors and an explicit route-change notice naming changed controls and the new path.
- Browser evidence: Car to Truck changed the six-stop route to `Sukhna Lake → Panchkula Sector 5 → Elante Mall`, with a complete measured explanation and no console warnings/errors.
- Temporary reasoning E2E user, session, and two owned records were removed.
