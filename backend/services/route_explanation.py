"""Build transparent, scenario-specific route recommendation explanations."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import networkx as nx

from services.routing import CostWeights, evaluate_path


OBJECTIVE_LABELS = {
    "distance": "Distance",
    "time": "Travel time",
    "fuel": "Fuel",
    "congestion": "Congestion",
    "risk": "Road risk",
}

PRIORITY_LABELS = {
    "shortest": "Shortest route",
    "fastest": "Fastest route",
    "least_fuel": "Least fuel",
    "least_traffic": "Least traffic",
    "balanced": "Balanced",
}

PRIORITY_HEADLINES = {
    "shortest": "Shortest-route objective selected this path",
    "fastest": "Fastest-route objective selected this path",
    "least_fuel": "Fuel-saving objective selected this path",
    "least_traffic": "Low-congestion objective selected this path",
    "balanced": "Balanced objective selected this path",
}

VEHICLE_EFFECTS = {
    "car": "Uses neutral road-type penalties with standard car speed and fuel rates.",
    "bike": "Favors local roads, discourages highways, and applies bike speed and fuel rates.",
    "truck": "Favors highways while strongly penalizing narrow local roads and applying truck fuel rates.",
    "emergency": "Minimizes safe response time with bounded traffic and signal privileges on physically accessible roads.",
}

TRAFFIC_EFFECTS = {
    "low": "Reduces congestion multipliers, especially on highways and arterial roads.",
    "medium": "Uses the scenario graph's baseline congestion multipliers.",
    "high": "Raises arterial and highway travel-time, fuel, and congestion costs.",
}

WEATHER_EFFECTS = {
    "sunny": "Adds no weather penalty to the road network.",
    "rain": "Penalizes rain-sensitive arterial roads and increases travel-time exposure.",
    "fog": "Penalizes high-speed highways because of reduced visibility.",
}

ROAD_EFFECTS = {
    "good": "Uses the lowest surface-risk and travel-time multipliers.",
    "moderate": "Raises surface risk and travel time, with a larger effect on highways.",
    "poor": "Applies the strongest surface-risk, time, and fuel penalties.",
}


def _title(value: str) -> str:
    return value.replace("_", " ").title()


def _segment_evidence(graph: nx.DiGraph, path: Sequence[str]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    segments: list[dict[str, Any]] = []
    totals = {
        "free_flow_time_min": 0.0,
        "traffic_delay_min": 0.0,
        "weather_delay_min": 0.0,
        "surface_delay_min": 0.0,
        "intersection_delay_min": 0.0,
        "construction_delay_min": 0.0,
    }
    for start, end in zip(path, path[1:]):
        edge = graph[start][end]
        for key in totals:
            totals[key] += float(edge.get(key, 0.0))
        segments.append({
            "segment": edge.get("segment_label", f"{start} → {end}"),
            "segment_id": edge.get("segment_id", f"{start}|{end}"),
            "road_type": edge.get("road_type", "unknown"),
            "distance_km": float(edge.get("distance_km", 0.0)),
            "expected_time_min": float(edge.get("time_min", 0.0)),
            "road_width_m": float(edge.get("road_width_m", 0.0)),
            "lanes": int(edge.get("lanes", 0)),
            "speed_limit_kmh": float(edge.get("speed_limit", 0.0)),
            "accessible": bool(edge.get("accessible", True)),
            "construction": bool(edge.get("construction", False)),
            "free_flow_time_min": float(edge.get("free_flow_time_min", 0.0)),
            "traffic_delay_min": float(edge.get("traffic_delay_min", 0.0)),
            "weather_delay_min": float(edge.get("weather_delay_min", 0.0)),
            "surface_delay_min": float(edge.get("surface_delay_min", 0.0)),
            "intersection_delay_min": float(edge.get("intersection_delay_min", 0.0)),
            "construction_delay_min": float(edge.get("construction_delay_min", 0.0)),
        })
    return segments, {key: round(value, 2) for key, value in totals.items()}


def _alternative_payload(alternatives: Sequence[Any]) -> list[dict[str, Any]]:
    if not alternatives:
        return []
    selected = alternatives[0].metrics
    payload: list[dict[str, Any]] = []
    for alternative in alternatives:
        metrics = alternative.metrics
        why: list[str] = []
        if alternative.rank == 1:
            why.append("Lowest verified weighted objective under the active conditions.")
        else:
            if metrics.objective_value > selected.objective_value + 1e-9:
                why.append(
                    f"Weighted objective is {metrics.objective_value - selected.objective_value:.4f} higher."
                )
            if metrics.time_min > selected.time_min + 0.05:
                why.append(f"Expected travel time is {metrics.time_min - selected.time_min:.1f} min slower.")
            if metrics.distance_km > selected.distance_km + 0.05:
                why.append(f"Distance is {metrics.distance_km - selected.distance_km:.1f} km longer.")
            if metrics.risk_exposure > selected.risk_exposure + 0.01:
                why.append("Road/weather risk exposure is higher.")
            if not why:
                why.append("It loses the deterministic objective tie-break against the recommended route.")
        payload.append({
            "rank": alternative.rank,
            "selected": alternative.rank == 1,
            "path": list(alternative.path),
            "distance_km": metrics.distance_km,
            "time_min": metrics.time_min,
            "fuel_l": metrics.fuel_l,
            "fuel_cost_inr": metrics.fuel_cost_inr,
            "congestion_exposure": metrics.congestion_exposure,
            "risk_exposure": metrics.risk_exposure,
            "objective_value": metrics.objective_value,
            "objective_delta": alternative.objective_delta,
            "why_not_selected": why,
        })
    return payload


def _previous_route_comparison(
    graph: nx.DiGraph,
    selected_path: Sequence[str],
    previous_path: Sequence[str] | None,
    weights: Mapping[str, float],
    selected_metrics: Mapping[str, float],
    request: Mapping[str, Any],
    previous_scenario: Mapping[str, Any] | None,
    impact: Mapping[str, float],
) -> dict[str, Any]:
    if not previous_path:
        return {"status": "not_available", "previous_path": [], "reasons": []}
    if list(previous_path) == list(selected_path):
        reasons: list[str] = []
        labels = {
            "vehicle_type": "Vehicle",
            "traffic_density": "Traffic density",
            "weather": "Weather",
            "road_condition": "Road condition",
            "optimization_priority": "Optimization priority",
            "time_of_day": "Departure time",
        }
        for key, label in labels.items():
            before = (previous_scenario or {}).get(key)
            after = request.get(key)
            if before is not None and before != after:
                reasons.append(f"{label} changed from {_title(str(before))} to {_title(str(after))}.")
        if request.get("traffic_density") != (previous_scenario or {}).get("traffic_density"):
            reasons.append(f"The current route carries {impact.get('traffic_delay_min', 0.0):.1f} min of measured traffic delay.")
        if request.get("weather") != (previous_scenario or {}).get("weather"):
            reasons.append(f"The current route carries {impact.get('weather_delay_min', 0.0):.1f} min of measured weather delay.")
        reasons.append(
            "After recalculating every reachable edge, this path still has the lowest measured objective among the feasible alternatives."
        )
        return {
            "status": "unchanged",
            "previous_path": list(previous_path),
            "reasons": reasons,
        }
    try:
        previous = evaluate_path(graph, list(previous_path), CostWeights(**weights))
    except (KeyError, nx.NetworkXError):
        excluded = graph.graph.get("excluded_segments", [])
        previous_pairs = {
            (start, end)
            for start, end in zip(previous_path, previous_path[1:])
        }
        affected = [
            item for item in excluded
            if (item.get("from"), item.get("to")) in previous_pairs
        ]
        return {
            "status": "changed",
            "previous_path": list(previous_path),
            "valid_under_current_conditions": False,
            "affected_segments": affected,
            "reasons": [
                "The previous route is no longer physically feasible under the active closure or accessibility constraints."
            ],
        }

    selected_time = float(selected_metrics.get("time", 0.0))
    selected_distance = float(selected_metrics.get("distance", 0.0))
    selected_objective = float(selected_metrics.get("objective_value", 0.0))
    reasons: list[str] = []
    if previous.time_min > selected_time + 0.05:
        reasons.append(f"The new route saves {previous.time_min - selected_time:.1f} min under the current conditions.")
    elif selected_time > previous.time_min + 0.05:
        reasons.append(
            f"The new route takes {selected_time - previous.time_min:.1f} min longer but wins on the active weighted objective."
        )
    if previous.distance_km > selected_distance + 0.05:
        reasons.append(f"The previous route is {previous.distance_km - selected_distance:.1f} km longer.")
    elif selected_distance > previous.distance_km + 0.05:
        reasons.append(f"The new route is {selected_distance - previous.distance_km:.1f} km longer.")
    if previous.objective_value > selected_objective + 1e-9:
        reasons.append(f"Its current weighted objective is {previous.objective_value - selected_objective:.4f} higher.")

    previous_segments, _ = _segment_evidence(graph, previous_path)
    if previous_segments:
        worst = max(
            previous_segments,
            key=lambda segment: (
                segment["traffic_delay_min"]
                + segment["weather_delay_min"]
                + segment["surface_delay_min"]
                + segment["construction_delay_min"]
            ),
        )
        delay_parts = {
            "traffic": worst["traffic_delay_min"],
            "weather": worst["weather_delay_min"],
            "road surface": worst["surface_delay_min"],
            "construction": worst["construction_delay_min"],
        }
        cause, value = max(delay_parts.items(), key=lambda item: item[1])
        if value > 0:
            reasons.append(
                f"On {worst['segment']}, {cause} adds {value:.1f} min—the largest avoidable delay on the previous path."
            )
    return {
        "status": "changed",
        "previous_path": list(previous_path),
        "valid_under_current_conditions": True,
        "previous_metrics": {
            "distance_km": previous.distance_km,
            "time_min": previous.time_min,
            "fuel_cost_inr": previous.fuel_cost_inr,
            "objective_value": previous.objective_value,
        },
        "reasons": reasons or ["The new route has a lower measured weighted objective."],
    }


def build_route_explanation(
    *,
    request: Mapping[str, Any],
    path: Sequence[str],
    metrics: Mapping[str, float],
    weights: Mapping[str, float],
    graph: nx.DiGraph | None = None,
    alternatives: Sequence[Any] = (),
    search_report: Mapping[str, Any] | None = None,
    previous_path: Sequence[str] | None = None,
    previous_scenario: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    priority = str(request.get("optimization_priority", "balanced"))
    custom = bool(request.get("weights"))
    dominant_key, dominant_weight = max(weights.items(), key=lambda item: item[1])
    dominant_label = OBJECTIVE_LABELS.get(dominant_key, _title(dominant_key))
    priority_label = "Custom weights" if custom else PRIORITY_LABELS.get(priority, _title(priority))
    headline = "Custom objective selected this path" if custom else PRIORITY_HEADLINES.get(
        priority, "Weighted objective selected this path"
    )

    distance = float(metrics.get("distance", 0.0))
    duration = float(metrics.get("time", 0.0))
    objective = float(metrics.get("objective_value", 0.0))
    summary = (
        f"The verified route through {' → '.join(path)} has the lowest active weighted "
        f"objective ({objective:.4f}). It covers {distance:.1f} km in {duration:.1f} min "
        f"under the selected scenario."
    )

    vehicle = str(request.get("vehicle_type", "car"))
    if vehicle == "emergency" and not custom:
        priority_label = "Emergency response time"
        headline = "Emergency response-time policy selected this path"
    traffic = str(request.get("traffic_density", "medium"))
    weather = str(request.get("weather", "sunny"))
    road = str(request.get("road_condition", "good"))
    time_of_day = str(request.get("time_of_day", "09:00"))
    try:
        hour = int(time_of_day.split(":", 1)[0])
    except (TypeError, ValueError):
        hour = 9
    peak = 7 <= hour <= 10 or 17 <= hour <= 20

    segments: list[dict[str, Any]] = []
    impact = {
        "free_flow_time_min": 0.0,
        "traffic_delay_min": 0.0,
        "weather_delay_min": 0.0,
        "surface_delay_min": 0.0,
        "intersection_delay_min": 0.0,
        "construction_delay_min": 0.0,
    }
    if graph is not None and len(path) > 1:
        segments, impact = _segment_evidence(graph, path)

    widths = [segment["road_width_m"] for segment in segments if segment["road_width_m"] > 0]
    speeds = sorted({segment["speed_limit_kmh"] for segment in segments if segment["speed_limit_kmh"] > 0})
    road_types = sorted({segment["road_type"] for segment in segments})
    construction = [segment["segment"] for segment in segments if segment["construction"]]
    dynamic_vehicle_effect = VEHICLE_EFFECTS[vehicle]
    if segments:
        privilege = ""
        if vehicle == "emergency":
            privilege = (
                f" Signal/traffic privileges are reflected in the measured {impact['traffic_delay_min']:.1f} min "
                "traffic delay and reduced intersection delay; no road is preferred solely because it is a highway."
            )
        dynamic_vehicle_effect = (
            f"All {len(segments)} selected segments satisfy the {vehicle} accessibility profile; "
            f"minimum route width is {min(widths):.1f} m.{privilege}"
        )

    factors = [
        {
            "label": "Priority",
            "value": priority_label,
            "effect": (
                f"{dominant_label} carries {dominant_weight * 100:.0f}% of the normalized objective."
            ),
        },
        {"label": "Vehicle", "value": _title(vehicle), "effect": dynamic_vehicle_effect},
        {
            "label": "Traffic",
            "value": _title(traffic),
            "effect": f"Traffic adds {impact['traffic_delay_min']:.1f} min across the selected segments." if segments else TRAFFIC_EFFECTS[traffic],
        },
        {
            "label": "Weather",
            "value": _title(weather),
            "effect": f"Weather adds {impact['weather_delay_min']:.1f} min using each segment's road class." if segments else WEATHER_EFFECTS[weather],
        },
        {
            "label": "Road condition",
            "value": _title(road),
            "effect": f"Surface quality adds {impact['surface_delay_min']:.1f} min; construction adds {impact['construction_delay_min']:.1f} min." if segments else ROAD_EFFECTS[road],
        },
        {
            "label": "Departure",
            "value": time_of_day,
            "effect": (
                "Peak-hour multipliers are active for this departure time."
                if peak
                else "Peak-hour multipliers are not active for this departure time."
            ),
        },
    ]
    route_characteristics = {
        "minimum_width_m": round(min(widths), 1) if widths else 0.0,
        "maximum_width_m": round(max(widths), 1) if widths else 0.0,
        "speed_limits_kmh": speeds,
        "road_types": road_types,
        "all_segments_accessible": all(segment["accessible"] for segment in segments),
        "construction_segments": construction,
        "segments": segments,
    }
    return {
        "headline": headline,
        "summary": summary,
        "dominant_objective": dominant_label,
        "factors": factors,
        "path": list(path),
        "route_characteristics": route_characteristics,
        "impact_breakdown": impact,
        "alternatives": _alternative_payload(alternatives),
        "search_scope": dict(search_report or {}),
        "constraints": {
            "excluded_segments": list(graph.graph.get("excluded_segments", [])) if graph is not None else [],
            "closed_segments": list(graph.graph.get("closed_segments", [])) if graph is not None else [],
        },
        "previous_route_comparison": (
            _previous_route_comparison(
                graph, path, previous_path, weights, metrics,
                request, previous_scenario, impact,
            )
            if graph is not None
            else {"status": "not_available", "previous_path": [], "reasons": []}
        ),
    }
