"""Versioned, curated Chandigarh scenario graph used by every route solver.

The coordinates are geographic landmarks. Edge attributes are curated scenario
inputs, not a live traffic feed or a complete OpenStreetMap extract.
"""

from typing import List, Dict, Iterable, Tuple
import networkx as nx

from services.routing import CostWeights, edge_objective


# ── Real Chandigarh GPS coordinates ──────────────────────────────────────────
CHANDIGARH_NODES: Dict[str, Dict] = {
    "Elante Mall":          {"lat": 30.7056, "lng": 76.8013, "type": "commercial"},
    "Sector 17 Plaza":      {"lat": 30.7414, "lng": 76.7842, "type": "commercial"},
    "PGI Hospital":         {"lat": 30.7648, "lng": 76.7762, "type": "hospital"},
    "Chandigarh Airport":   {"lat": 30.6735, "lng": 76.7885, "type": "transport"},
    "Rock Garden":          {"lat": 30.7526, "lng": 76.8089, "type": "landmark"},
    "ISBT Sector 43":       {"lat": 30.7076, "lng": 76.7916, "type": "transport"},
    "Sector 22 Market":     {"lat": 30.7333, "lng": 76.7794, "type": "commercial"},
    "Punjab University":    {"lat": 30.7601, "lng": 76.7659, "type": "education"},
    "Sector 35 Market":     {"lat": 30.7196, "lng": 76.7839, "type": "commercial"},
    "Mohali IT Park":       {"lat": 30.7046, "lng": 76.7179, "type": "commercial"},
    "Panchkula Sector 5":   {"lat": 30.6955, "lng": 76.8535, "type": "residential"},
    "Chandigarh Railway":   {"lat": 30.6980, "lng": 76.8220, "type": "transport"},
    "Sector 8 Market":      {"lat": 30.7490, "lng": 76.7960, "type": "commercial"},
    "Leisure Valley":       {"lat": 30.7310, "lng": 76.8050, "type": "landmark"},
    "Kharar":               {"lat": 30.7468, "lng": 76.6452, "type": "residential"},
    "Chandigarh University":{"lat": 30.7735, "lng": 76.5773, "type": "education"},
}

# ── Road network with realistic attributes ────────────────────────────────────
# (from, to, dist_km, base_time_min, road_type, lanes, speed_limit_kmh)
# Distances are curated demonstration inputs and are not asserted as live measurements.
CHANDIGARH_EDGES: List[Tuple] = [
    # FORMAT: (from, to, dist_km, base_time_min, road_type, lanes, speed_limit_kmh)
    #
    # DESIGN: Three parallel networks exist:
    #   HIGHWAY network  - fast base time, destroyed by fog/poor-road/emergency-preferred
    #   ARTERIAL network - medium, destroyed by rain/high-traffic
    #   LOCAL network    - slow base time, resilient to all conditions, bike-preferred
    # Every long route has competing paths through different network types.

    # ── Rock Garden ──
    ("Rock Garden",    "Sector 8 Market",        1.8,  6,  "local",    2, 30),
    ("Rock Garden",    "Panchkula Sector 5",     7.0,  9,  "highway",  6, 80),
    ("Rock Garden",    "Leisure Valley",         2.5,  8,  "arterial", 4, 50),

    # ── Sector 8 Market ──
    ("Sector 8 Market", "Sector 17 Plaza",       2.4,  8,  "arterial", 4, 50),
    ("Sector 8 Market", "Leisure Valley",        2.8,  9,  "local",    2, 30),
    ("Sector 8 Market", "PGI Hospital",          3.0, 10,  "arterial", 4, 50),
    ("Sector 8 Market", "Punjab University",     3.5, 11,  "arterial", 4, 50),
    ("Sector 8 Market", "ISBT Sector 43",        6.5,  8,  "highway",  6, 80),

    # ── Sector 17 Plaza ──
    ("Sector 17 Plaza", "Sector 22 Market",      1.6,  5,  "arterial", 6, 60),
    ("Sector 17 Plaza", "Leisure Valley",        2.0,  7,  "local",    2, 30),
    ("Sector 17 Plaza", "Sector 35 Market",      2.3,  7,  "arterial", 6, 60),
    ("Sector 17 Plaza", "PGI Hospital",          4.5, 14,  "local",    2, 30),
    ("Sector 17 Plaza", "ISBT Sector 43",        6.0,  7,  "highway",  6, 80),

    # ── Leisure Valley ──
    ("Leisure Valley",  "Sector 22 Market",      3.0,  9,  "local",    2, 30),
    ("Leisure Valley",  "Sector 35 Market",      2.0,  6,  "local",    2, 40),
    ("Leisure Valley",  "Elante Mall",           3.0,  9,  "arterial", 4, 50),

    # ── Sector 22 Market ──
    ("Sector 22 Market", "Punjab University",    3.2, 10,  "arterial", 4, 50),
    ("Sector 22 Market", "Sector 35 Market",     1.6,  5,  "local",    2, 30),
    ("Sector 22 Market", "ISBT Sector 43",       3.5, 11,  "arterial", 4, 50),
    ("Sector 22 Market", "Elante Mall",          4.2, 13,  "arterial", 4, 50),
    ("Sector 22 Market", "Chandigarh Railway",   5.0,  6,  "highway",  6, 80),

    # ── Punjab University ──
    ("Punjab University", "PGI Hospital",        1.6,  5,  "local",    2, 30),
    ("Punjab University", "Mohali IT Park",      7.5,  9,  "highway",  6, 80),
    ("Punjab University", "Elante Mall",         9.5, 11,  "highway",  6, 80),
    ("Punjab University", "Sector 35 Market",    4.0, 12,  "arterial", 4, 50),

    # ── PGI Hospital ──
    ("PGI Hospital",    "Mohali IT Park",        10.0, 12,  "highway",  6, 80),
    ("PGI Hospital",    "Chandigarh Airport",    14.0, 16,  "highway",  6, 80),
    ("PGI Hospital",    "Sector 22 Market",       4.0, 13,  "arterial", 4, 50),

    # ── Sector 35 Market ──
    ("Sector 35 Market", "ISBT Sector 43",       3.0,  9,  "arterial", 4, 50),
    ("Sector 35 Market", "Elante Mall",          2.3,  7,  "arterial", 4, 50),
    ("Sector 35 Market", "Chandigarh Railway",   4.5, 14,  "arterial", 4, 50),
    ("Sector 35 Market", "Mohali IT Park",       8.0, 10,  "highway",  6, 80),
    ("Sector 35 Market", "Chandigarh Airport",   7.5,  9,  "highway",  6, 80),
    ("Sector 35 Market", "Leisure Valley",       2.0,  6,  "local",    2, 40),

    # ── ISBT Sector 43 ──
    ("ISBT Sector 43",  "Elante Mall",           1.5,  5,  "arterial", 4, 50),
    ("ISBT Sector 43",  "Chandigarh Railway",    2.4,  8,  "arterial", 4, 50),
    ("ISBT Sector 43",  "Mohali IT Park",        6.0,  8,  "highway",  6, 80),
    ("ISBT Sector 43",  "Chandigarh Airport",    5.5,  7,  "highway",  6, 80),
    ("ISBT Sector 43",  "Panchkula Sector 5",    9.5, 11,  "highway",  6, 80),
    ("ISBT Sector 43",  "Sector 22 Market",      3.5, 11,  "local",    2, 30),

    # ── Elante Mall ──
    ("Elante Mall",     "Chandigarh Railway",    2.6,  8,  "arterial", 4, 50),
    ("Elante Mall",     "Mohali IT Park",        4.5,  6,  "highway",  6, 80),
    ("Elante Mall",     "Panchkula Sector 5",    9.5, 12,  "highway",  6, 80),
    ("Elante Mall",     "Sector 35 Market",      2.3,  7,  "local",    2, 30),

    # ── Chandigarh Railway ──
    ("Chandigarh Railway", "Chandigarh Airport", 4.5,  6,  "highway",  6, 80),
    ("Chandigarh Railway", "Panchkula Sector 5", 8.0, 10,  "highway",  6, 80),
    ("Chandigarh Railway", "Mohali IT Park",     8.0, 10,  "highway",  6, 80),
    ("Chandigarh Railway", "ISBT Sector 43",     2.4,  8,  "local",    2, 30),

    # ── Chandigarh Airport ──
    ("Chandigarh Airport", "Mohali IT Park",     4.0,  5,  "highway",  6, 80),
    ("Chandigarh Airport", "Kharar",            10.0, 12,  "highway",  6, 80),
    ("Chandigarh Airport", "Panchkula Sector 5",12.0, 14,  "highway",  6, 80),
    ("Chandigarh Airport", "ISBT Sector 43",     5.5,  7,  "arterial", 4, 50),

    # ── Panchkula Sector 5 ──
    ("Panchkula Sector 5", "Mohali IT Park",    22.0, 26,  "highway",  6, 80),
    ("Panchkula Sector 5", "Elante Mall",        9.5, 12,  "arterial", 4, 50),

    # ── Mohali IT Park ──
    ("Mohali IT Park",  "Kharar",               8.5, 10,  "highway",  6, 80),
    ("Mohali IT Park",  "Chandigarh University",14.0, 17,  "highway",  4, 60),
    ("Mohali IT Park",  "ISBT Sector 43",        6.0,  8,  "arterial", 4, 50),

    # ── Kharar ──
    ("Kharar",          "Chandigarh University", 7.2,  9,  "highway",  4, 60),
    ("Kharar",          "Mohali IT Park",        8.5, 10,  "arterial", 4, 50),
]

# Travel time is assembled from additive, inspectable components.  This avoids
# the old multiplicative penalties where an emergency vehicle became 5x faster
# on a highway and 6x slower on a local road, which created geographic detours.
TRAFFIC_DELAY_RATE = {
    "low": {"highway": 0.05, "arterial": 0.08, "local": 0.05},
    "medium": {"highway": 0.18, "arterial": 0.28, "local": 0.16},
    "high": {"highway": 0.48, "arterial": 0.65, "local": 0.36},
}

PEAK_DELAY_RATE = {
    7: {"highway": 0.10, "arterial": 0.15, "local": 0.08},
    8: {"highway": 0.18, "arterial": 0.28, "local": 0.14},
    9: {"highway": 0.18, "arterial": 0.28, "local": 0.14},
    10: {"highway": 0.10, "arterial": 0.16, "local": 0.08},
    17: {"highway": 0.14, "arterial": 0.22, "local": 0.11},
    18: {"highway": 0.24, "arterial": 0.34, "local": 0.18},
    19: {"highway": 0.20, "arterial": 0.30, "local": 0.16},
    20: {"highway": 0.10, "arterial": 0.16, "local": 0.08},
}

WEATHER_DELAY_RATE = {
    "sunny": {"highway": 0.0, "arterial": 0.0, "local": 0.0},
    "rain": {"highway": 0.15, "arterial": 0.18, "local": 0.12},
    "fog": {"highway": 0.30, "arterial": 0.20, "local": 0.14},
}

SURFACE_DELAY_RATE = {
    "good": {"highway": 0.0, "arterial": 0.0, "local": 0.0},
    "moderate": {"highway": 0.08, "arterial": 0.12, "local": 0.16},
    "poor": {"highway": 0.24, "arterial": 0.34, "local": 0.46},
}

VEHICLE_TIME_PROFILE = {
    "car": {"moving": 1.0, "traffic": 1.0, "intersection": 1.0, "minimum_width": 2.8},
    "bike": {"moving": 1.10, "traffic": 0.72, "intersection": 0.80, "minimum_width": 1.5},
    "truck": {"moving": 1.16, "traffic": 1.12, "intersection": 1.18, "minimum_width": 5.2},
    # Sirens and signal priority reduce congestion/intersection delay, not the
    # physical length of a road or the safe traversal time by an extreme factor.
    "emergency": {"moving": 0.88, "traffic": 0.45, "intersection": 0.50, "minimum_width": 3.0},
}

LANE_WIDTH_M = {"highway": 3.5, "arterial": 3.25, "local": 2.8}

FUEL_RATE = {
    "car": {"highway": 0.060, "arterial": 0.085, "local": 0.100},
    "bike": {"highway": 0.025, "arterial": 0.030, "local": 0.035},
    "truck": {"highway": 0.220, "arterial": 0.280, "local": 0.320},
    "emergency": {"highway": 0.100, "arterial": 0.130, "local": 0.150},
}

FUEL_PRICE_PER_LITRE = 96.0  # INR, Chandigarh petrol price


def segment_id(start: str, end: str) -> str:
    """Return a stable undirected identifier for a curated road segment."""
    return "|".join(sorted((start, end)))


def _edge_components(
    *,
    distance_km: float,
    base_time_min: float,
    road_type: str,
    speed_limit_kmh: float,
    vehicle: str,
    weather: str,
    road_condition: str,
    hour: int,
    traffic_density: str,
    construction: bool,
) -> dict[str, float]:
    profile = VEHICLE_TIME_PROFILE[vehicle]
    legal_minimum = distance_km / max(1.0, speed_limit_kmh) * 60.0
    reference_moving = max(legal_minimum, base_time_min * 0.72)
    free_flow = reference_moving * profile["moving"]
    intersection_reference = max(0.0, base_time_min - reference_moving)
    intersection = intersection_reference * profile["intersection"]

    traffic_rate = TRAFFIC_DELAY_RATE[traffic_density][road_type]
    traffic_rate += PEAK_DELAY_RATE.get(hour, {}).get(road_type, 0.0)
    traffic = base_time_min * traffic_rate * profile["traffic"]
    weather_delay = base_time_min * WEATHER_DELAY_RATE[weather][road_type]
    surface_delay = base_time_min * SURFACE_DELAY_RATE[road_condition][road_type]
    construction_delay = base_time_min * 0.40 if construction else 0.0
    return {
        "free_flow_time_min": round(free_flow, 3),
        "traffic_delay_min": round(traffic, 3),
        "weather_delay_min": round(weather_delay, 3),
        "surface_delay_min": round(surface_delay, 3),
        "intersection_delay_min": round(intersection, 3),
        "construction_delay_min": round(construction_delay, 3),
    }


def _edge_fuel_l(
    distance_km: float,
    road_type: str,
    vehicle: str,
    components: dict[str, float],
    road_condition: str,
) -> float:
    moving = max(components["free_flow_time_min"], 0.1)
    delay = sum(value for key, value in components.items() if key != "free_flow_time_min")
    delay_factor = 1.0 + min(0.45, (delay / moving) * 0.18)
    surface_factor = {"good": 1.0, "moderate": 1.08, "poor": 1.20}[road_condition]
    return round(distance_km * FUEL_RATE[vehicle][road_type] * delay_factor * surface_factor, 5)


def build_city_graph(
    vehicle: str = "car",
    traffic_density: str = "medium",
    weather: str = "sunny",
    road_condition: str = "good",
    hour: int = 9,
    closed_segments: Iterable[str] | None = None,
    construction_segments: Iterable[str] | None = None,
    objective_weights: CostWeights | None = None,
) -> Tuple[nx.DiGraph, Dict[str, Dict]]:
    """
    Two-pass build: collect all parallel road options per landmark pair, then
    retain the edge with the lowest active additive objective. This reduction is
    optimality-preserving: replacing a parallel edge with a higher-cost edge
    cannot improve any path under the same non-negative objective.
    """
    closed = set(closed_segments or ())
    construction = set(construction_segments or ())
    candidates: Dict[tuple, list] = {}
    excluded: list[dict] = []
    for u, v, dist, base_t, road_type, lanes, speed_lim in CHANDIGARH_EDGES:
        identifier = segment_id(u, v)
        if identifier in closed:
            excluded.append({"segment_id": identifier, "from": u, "to": v, "reason": "road_closure"})
            continue
        for (nu, nv, nd, nt) in [(u, v, dist, base_t), (v, u, dist * 0.97, base_t * 0.97)]:
            width = round(lanes * LANE_WIDTH_M[road_type], 1)
            minimum_width = VEHICLE_TIME_PROFILE[vehicle]["minimum_width"]
            if width < minimum_width:
                excluded.append({
                    "segment_id": identifier,
                    "from": nu,
                    "to": nv,
                    "reason": "insufficient_width",
                    "road_width_m": width,
                    "minimum_width_m": minimum_width,
                })
                continue
            components = _edge_components(
                distance_km=nd,
                base_time_min=nt,
                road_type=road_type,
                speed_limit_kmh=speed_lim,
                vehicle=vehicle,
                weather=weather,
                road_condition=road_condition,
                hour=hour,
                traffic_density=traffic_density,
                construction=identifier in construction,
            )
            t = round(sum(components.values()), 2)
            fuel_l = _edge_fuel_l(nd, road_type, vehicle, components, road_condition)
            fuel_cost = round(fuel_l * FUEL_PRICE_PER_LITRE, 2)
            delay = t - components["free_flow_time_min"]
            risk = (
                {"good": 0.04, "moderate": 0.18, "poor": 0.42}[road_condition]
                + {"sunny": 0.0, "rain": 0.08, "fog": 0.14}[weather]
                + (0.12 if identifier in construction else 0.0)
                + (0.08 if width <= minimum_width + 0.5 else 0.0)
            )
            candidates.setdefault((nu, nv), []).append({
                "segment_id": identifier,
                "segment_label": f"{nu} → {nv}",
                "distance": round(nd, 2), "time": t, "fuel_cost": fuel_cost,
                "distance_km": round(nd, 2), "time_min": round(t, 2),
                "fuel_l": fuel_l,
                "congestion": round(components["traffic_delay_min"] / max(nt, 0.1), 4),
                "risk": round(min(1.0, risk), 4),
                "road_type": road_type, "lanes": lanes, "speed_limit": speed_lim,
                "road_width_m": width,
                "accessible": True,
                "construction": identifier in construction,
                "closed": False,
                "base_time": round(nt, 2),
                "total_delay_min": round(delay, 3),
                **components,
                "geometry": [
                    [CHANDIGARH_NODES[nu]["lat"], CHANDIGARH_NODES[nu]["lng"]],
                    [CHANDIGARH_NODES[nv]["lat"], CHANDIGARH_NODES[nv]["lng"]],
                ],
            })

    G = nx.DiGraph()
    G.graph.update({
        "vehicle": vehicle,
        "traffic_density": traffic_density,
        "weather": weather,
        "road_condition": road_condition,
        "hour": hour,
        "excluded_segments": excluded,
        "closed_segments": sorted(closed),
        "construction_segments": sorted(construction),
    })
    for name, attrs in CHANDIGARH_NODES.items():
        G.add_node(name, **attrs)

    active_weights = objective_weights or CostWeights(time=1.0, distance=0, fuel=0, congestion=0, risk=0)
    for (u, v), edges in candidates.items():
        best = min(edges, key=lambda edge: (edge_objective(edge, active_weights), edge["time"], edge["road_type"]))
        G.add_edge(u, v, **best)

    return G, CHANDIGARH_NODES


def get_path_coords(path: List[str], nodes: Dict) -> List[List[float]]:
    return [[nodes[n]["lat"], nodes[n]["lng"]] for n in path if n in nodes]


def get_graph_nodes_edges(G: nx.DiGraph, nodes: Dict):
    node_list = [
        {"id": n, "name": n, "lat": nodes[n]["lat"], "lng": nodes[n]["lng"]}
        for n in G.nodes if n in nodes
    ]
    edge_list = [
        {
            "from": u, "to": v,
            "distance": d.get("distance", 0),
            "time": d.get("time", 0),
            "fuel_cost": d.get("fuel_cost", 0),
            "road_type": d.get("road_type", "arterial"),
            "segment_id": d.get("segment_id", segment_id(u, v)),
            "segment_label": d.get("segment_label", f"{u} → {v}"),
            "lanes": d.get("lanes", 0),
            "road_width_m": d.get("road_width_m", 0),
            "speed_limit_kmh": d.get("speed_limit", 0),
            "accessible": d.get("accessible", True),
            "construction": d.get("construction", False),
            "free_flow_time_min": d.get("free_flow_time_min", 0),
            "traffic_delay_min": d.get("traffic_delay_min", 0),
            "weather_delay_min": d.get("weather_delay_min", 0),
            "surface_delay_min": d.get("surface_delay_min", 0),
            "intersection_delay_min": d.get("intersection_delay_min", 0),
            "construction_delay_min": d.get("construction_delay_min", 0),
            "traffic_factor": round(d.get("time", 1) / max(d.get("base_time", 1), 0.1), 2),
            "geometry": d.get("geometry", []),
            "fuel_l": d.get("fuel_l", 0),
            "congestion": d.get("congestion", 0),
            "risk": d.get("risk", 0),
        }
        for u, v, d in G.edges(data=True)
    ]
    return node_list, edge_list
