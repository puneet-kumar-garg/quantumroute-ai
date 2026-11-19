# QuantumRoute AI — Routing Engine Implementation Status

Last verified: 18 November 2026

## Implemented

### Route search and objective model

- Dijkstra, A*, and Bellman–Ford now consume the same directed graph and the same normalized, non-negative weighted objective.
- The recommended route is the exact minimum over the complete reachable graph. Dijkstra provides the production recommendation; A* (with an admissible zero heuristic) and Bellman–Ford independently verify its objective.
- Loopless K-shortest paths provide up to eight ranked, feasible alternatives for comparison and QAOA. This is deliberately described as bounded alternative enumeration, not exhaustive enumeration of every simple path.
- Parallel roads between the same landmarks are reduced only after the active objective is known. The minimum-objective parallel edge is retained, which preserves the global optimum for an additive objective.
- Invalid, disconnected, and inaccessible routes are handled as infeasible rather than fabricated.

### Vehicle and condition model

- Removed the previous extreme multiplicative vehicle penalties that could make an ambulance five times faster on a highway and six times slower on a local road.
- Travel time is now the sum of inspectable components: free-flow movement, traffic, weather, surface condition, intersections/signals, and construction.
- Cars, bikes, trucks, and emergency vehicles have separate movement, congestion, intersection, fuel, and minimum-width profiles.
- Emergency vehicles use a safe response-time objective with bounded traffic/signal privileges. A road is never selected merely because it is a highway.
- Road closures remove the selected segment before every solver runs. Construction adds explicit time and risk to the affected segment.
- Custom weights and the five normal priorities are supported. For an emergency vehicle, the default priority is intentionally overridden by the safe response-time policy; explicit custom weights remain authoritative.

### Explanations and integration

- Every route response includes segment-level road class, width, lanes, speed limit, accessibility, construction state, and each time-delay component.
- The response includes ranked alternatives, objective deltas, reasons alternatives lost, graph/search scope, active constraints, and a comparison with the previous recommended path.
- The frontend sends the previous path on every scenario recomputation and shows whether the route changed or remained optimal.
- A dedicated **Route Decision Explanation** section displays route metrics, decision factors, road characteristics, additive time impact, segment evidence, alternatives, previous-route comparison, and search coverage.
- The map's green recommended line and vehicle animation now use the backend recommendation geometry, not a UI-only priority route.
- OSRM geometry follows OpenStreetMap roads for the complete selected landmark sequence. Straight waypoint geometry is used only as a clearly labelled fallback if OSRM is unavailable.
- Practical segment controls are available for closures and construction; they use the backend segment catalogue and trigger automatic recomputation.

### Quantum route selection

- QAOA uses one binary variable per feasible K-shortest candidate route.
- The QUBO minimizes normalized route cost with a mathematically explicit one-hot penalty, `A(Σxᵢ − 1)²`, where the penalty exceeds every normalized candidate cost.
- Qiskit Aer, a parameterized QAOA ansatz, COBYLA, measured samples, feasibility decoding, circuit depth, and feasible probability are reported.
- The exact classical recommendation remains authoritative. The application does not claim quantum advantage and clearly identifies Aer as simulation.

## Named validation: PGI Hospital → Elante Mall

Scenario: medium traffic, sunny weather, good roads, 09:00; eight loopless alternatives requested.

| Vehicle | Recommended landmark path | Distance | Expected time | Fuel | Objective |
|---|---|---:|---:|---:|---:|
| Car (fastest) | PGI Hospital → Punjab University → Elante Mall | 11.05 km | 21.26 min | 0.83890 L | 0.681531 |
| Emergency | PGI Hospital → Punjab University → Elante Mall | 11.05 km | 14.70 min | 1.28249 L | 0.454047 |

The emergency vehicle no longer takes the old PGI → Mohali IT Park → Elante detour. That 14.37 km alternative is slower for the ambulance (16.68 min) and has a higher objective (0.525696). Dijkstra, A*, and Bellman–Ford returned exactly the same optimum for both vehicle profiles.

## Verification

- Backend: `35 passed`.
- Frontend unit tests: `9 passed`.
- The backend matrix covers 240 ordered source/destination cases per vehicle profile (960 route cases across four vehicles), 216 vehicle/traffic/weather/road/hour combinations, and an all-pairs emergency-detour invariant.
- API integration covers cookie authentication, the segment catalogue, real route response data, Qiskit Aer provenance, geometry contracts, alternatives, explanation evidence, and route history persistence.
- Frontend production build and TypeScript compilation pass.

## Data and infrastructure limitations

These limitations are shown honestly because they affect what the demonstration can claim:

- The optimization topology is a curated 16-landmark Chandigarh scenario graph. It is not a complete lane-level OpenStreetMap import. OSRM supplies road-following display geometry, but does not currently supply the optimization edge attributes.
- Traffic, weather, construction, width, and surface inputs are deterministic scenario data, not live municipal feeds. The traffic ML pipeline is trained and evaluated on clearly labelled synthetic scenario data.
- The curated graph has directed edges but does not include an authoritative turn-restriction or one-way-road dataset. Those claims require an OSM/PostGIS import or a licensed road-network feed.
- Public OSRM availability and routing policy are external dependencies. When it fails, the UI explicitly reports partial fallback instead of pretending the straight geometry is road-following.
- K-shortest enumeration is bounded to eight candidates because each candidate becomes one QAOA qubit. Exact classical optimization still searches the complete reachable graph; the system never claims that every simple path was enumerated.
- QAOA runs on Qiskit Aer simulation. No quantum-hardware execution or quantum speedup is claimed.

For production-grade street-level routing, the next data milestone is an OSM/PostGIS graph containing individual directed road segments, access tags, turn restrictions, bridge/height/weight limits, and versioned live traffic observations. The current interfaces and explanation schema are designed so that graph provider can replace the curated topology without changing the UI contract.
