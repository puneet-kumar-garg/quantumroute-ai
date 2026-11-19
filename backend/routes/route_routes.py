from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from functools import lru_cache
from datetime import datetime, timedelta, timezone

from database.db import get_db
from models.models import User, OptimizationRecord
from models.schemas import (
    RouteRequest, OptimizationResponse, DashboardStats,
    RecentOptimization, RouteNode, AlgorithmResult, QuantumResult, TrafficPrediction
)
from services.auth_service import get_current_user
from quantum.qaoa_engine import (
    build_city_graph, CHANDIGARH_EDGES,
    get_graph_nodes_edges, CHANDIGARH_NODES
)
from ml.traffic_pipeline import ScenarioTrafficService
from services.optimization import OptimizationSettings, optimize_graph
from services.routing import CostWeights
from services.osrm import OSRMGeometryService
from services.route_explanation import build_route_explanation
from utils.config import settings

router = APIRouter(prefix="/routes", tags=["routes"])
LOCATIONS = list(CHANDIGARH_NODES.keys())


WEIGHT_PRESETS = {
    "shortest": CostWeights(distance=0.8, time=0.1, fuel=0.05, congestion=0.05, risk=0),
    "fastest": CostWeights(distance=0.05, time=0.8, fuel=0.05, congestion=0.1, risk=0),
    "least_fuel": CostWeights(distance=0.1, time=0.1, fuel=0.7, congestion=0.05, risk=0.05),
    "least_traffic": CostWeights(distance=0.05, time=0.15, fuel=0.05, congestion=0.7, risk=0.05),
    "balanced": CostWeights(),
}

EMERGENCY_RESPONSE_WEIGHTS = CostWeights(
    distance=0.12,
    time=0.68,
    fuel=0.03,
    congestion=0.10,
    risk=0.07,
)


@lru_cache(maxsize=1)
def _traffic_service() -> ScenarioTrafficService:
    return ScenarioTrafficService(rows=2_000, seed=42)


@lru_cache(maxsize=1)
def _osrm_service() -> OSRMGeometryService:
    return OSRMGeometryService(
        base_url=settings.OSRM_BASE_URL,
        timeout_seconds=settings.OSRM_TIMEOUT_SECONDS,
    )


def _weights_for_request(req: RouteRequest) -> CostWeights:
    if req.weights:
        return CostWeights(**req.weights.model_dump())
    if req.vehicle_type == "emergency":
        return EMERGENCY_RESPONSE_WEIGHTS
    return WEIGHT_PRESETS.get(req.optimization_priority, WEIGHT_PRESETS["balanced"])


def _classical_payload(result, nodes: dict) -> dict:
    metrics = result.metrics
    road_geometry = _osrm_service().geometry_for_path(result.path, nodes)
    return {
        "algorithm": result.algorithm,
        "path": result.path,
        "path_coords": road_geometry.coordinates,
        "distance": metrics.distance_km if metrics else 0.0,
        "time": metrics.time_min if metrics else 0.0,
        "cost": metrics.fuel_cost_inr if metrics else 0.0,
        "fuel_l": metrics.fuel_l if metrics else 0.0,
        "congestion_exposure": metrics.congestion_exposure if metrics else 0.0,
        "risk_exposure": metrics.risk_exposure if metrics else 0.0,
        "execution_time_ms": result.execution_time_ms,
        "memory_usage_kb": result.memory_peak_kb,
        "feasible": result.feasible,
        "objective_value": result.objective_value if result.feasible else None,
        "provenance": "measured_execution",
        "geometry_source": road_geometry.source,
        "geometry_error": road_geometry.error,
    }


def _build_condition_zones(traffic: str, weather: str, road_cond: str) -> list:
    """
    Return deterministic scenario overlays anchored to Chandigarh landmarks.
    These are visual scenario inputs, not observations from a live feed.
    """
    zones = []

    # ── Traffic Density zones ──
    if traffic == "high":
        zones += [
            {"lat": 30.7414, "lng": 76.7842, "radius": 600, "color": "#ef4444", "label": "High Traffic", "type": "traffic"},   # Sector 17 Plaza
            {"lat": 30.7333, "lng": 76.7794, "radius": 500, "color": "#ef4444", "label": "High Traffic", "type": "traffic"},   # Sector 22 Market
            {"lat": 30.7196, "lng": 76.7839, "radius": 500, "color": "#ef4444", "label": "High Traffic", "type": "traffic"},   # Sector 35 Market
            {"lat": 30.7076, "lng": 76.7916, "radius": 450, "color": "#ef4444", "label": "High Traffic", "type": "traffic"},   # ISBT Sector 43
            {"lat": 30.7056, "lng": 76.8013, "radius": 400, "color": "#f97316", "label": "Moderate Traffic", "type": "traffic"}, # Elante Mall
        ]
    elif traffic == "medium":
        zones += [
            {"lat": 30.7414, "lng": 76.7842, "radius": 400, "color": "#f59e0b", "label": "Medium Traffic", "type": "traffic"},
            {"lat": 30.7076, "lng": 76.7916, "radius": 350, "color": "#f59e0b", "label": "Medium Traffic", "type": "traffic"},
        ]

    # ── Weather zones ──
    if weather == "rain":
        zones += [
            {"lat": 30.7526, "lng": 76.8089, "radius": 700, "color": "#3b82f6", "label": "Heavy Rain", "type": "weather"},      # Rock Garden area
            {"lat": 30.6955, "lng": 76.8535, "radius": 900, "color": "#60a5fa", "label": "Rain", "type": "weather"},            # Panchkula
            {"lat": 30.6980, "lng": 76.8220, "radius": 600, "color": "#60a5fa", "label": "Rain", "type": "weather"},            # Railway area
            {"lat": 30.7310, "lng": 76.8050, "radius": 500, "color": "#3b82f6", "label": "Heavy Rain", "type": "weather"},      # Leisure Valley
        ]
    elif weather == "fog":
        zones += [
            {"lat": 30.6735, "lng": 76.7885, "radius": 1200, "color": "#94a3b8", "label": "Dense Fog", "type": "weather"},     # Airport (worst fog)
            {"lat": 30.7468, "lng": 76.6452, "radius": 1000, "color": "#94a3b8", "label": "Dense Fog", "type": "weather"},     # Kharar highway
            {"lat": 30.7735, "lng": 76.5773, "radius": 900,  "color": "#cbd5e1", "label": "Fog", "type": "weather"},           # Chandigarh University
            {"lat": 30.7046, "lng": 76.7179, "radius": 800,  "color": "#94a3b8", "label": "Dense Fog", "type": "weather"},     # Mohali IT Park
        ]

    # ── Road Condition zones ──
    if road_cond == "poor":
        zones += [
            {"lat": 30.7601, "lng": 76.7659, "radius": 600, "color": "#dc2626", "label": "Poor Road", "type": "road"},         # Punjab University
            {"lat": 30.7648, "lng": 76.7762, "radius": 500, "color": "#dc2626", "label": "Poor Road", "type": "road"},         # PGI Hospital
            {"lat": 30.7046, "lng": 76.7179, "radius": 700, "color": "#dc2626", "label": "Poor Road", "type": "road"},         # Mohali IT Park
            {"lat": 30.7468, "lng": 76.6452, "radius": 800, "color": "#b91c1c", "label": "Very Poor Road", "type": "road"},    # Kharar
        ]
    elif road_cond == "moderate":
        zones += [
            {"lat": 30.7601, "lng": 76.7659, "radius": 400, "color": "#f59e0b", "label": "Moderate Road", "type": "road"},
            {"lat": 30.7046, "lng": 76.7179, "radius": 500, "color": "#f59e0b", "label": "Moderate Road", "type": "road"},
            {"lat": 30.7468, "lng": 76.6452, "radius": 600, "color": "#f59e0b", "label": "Moderate Road", "type": "road"},
        ]

    return zones


@router.get("/locations")
def get_locations():
    return LOCATIONS


@router.get("/segments")
def get_road_segments():
    segments: dict[str, dict] = {}
    for start, end, distance, _base_time, road_type, lanes, speed_limit in CHANDIGARH_EDGES:
        identifier = "|".join(sorted((start, end)))
        existing = segments.get(identifier)
        if existing and existing["road_type"] == road_type:
            continue
        segments[identifier] = {
            "id": identifier,
            "label": f"{start} ↔ {end}",
            "road_type": road_type,
            "distance_km": distance,
            "lanes": lanes,
            "speed_limit_kmh": speed_limit,
        }
    return sorted(segments.values(), key=lambda segment: segment["label"])


@router.post("/optimize", response_model=OptimizationResponse)
def optimize_route(
    req: RouteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.source == req.destination:
        raise HTTPException(400, "Source and destination must be different")
    if req.source not in CHANDIGARH_NODES:
        raise HTTPException(400, f"Unknown source: {req.source}")
    if req.destination not in CHANDIGARH_NODES:
        raise HTTPException(400, f"Unknown destination: {req.destination}")
    valid_segments = {
        "|".join(sorted((start, end)))
        for start, end, *_rest in CHANDIGARH_EDGES
    }
    unknown_disruptions = (
        set(req.closed_segments) | set(req.construction_segments)
    ) - valid_segments
    if unknown_disruptions:
        raise HTTPException(400, f"Unknown road segment: {sorted(unknown_disruptions)[0]}")

    # Parse time of day
    hour = 9
    if req.time_of_day:
        try:
            hour = int(req.time_of_day.split(":")[0])
        except Exception:
            hour = 9

    qaoa_p = max(1, min(5, req.qaoa_layers or 2))
    qaoa_shots = max(32, min(8192, req.qaoa_shots or 1024))
    qaoa_maxiter = max(1, min(500, req.qaoa_maxiter or 80))

    weights = _weights_for_request(req)

    # Build graph with all parameters baked in per edge. Parallel road options
    # are reduced only after the active objective is known.
    G, nodes = build_city_graph(
        vehicle=req.vehicle_type,
        traffic_density=req.traffic_density,
        weather=req.weather,
        road_condition=req.road_condition,
        hour=hour,
        closed_segments=req.closed_segments,
        construction_segments=req.construction_segments,
        objective_weights=weights,
    )
    outcome = optimize_graph(
        G,
        req.source,
        req.destination,
        weights,
        OptimizationSettings(
            candidate_limit=8,
            layers=qaoa_p,
            shots=qaoa_shots,
            maxiter=qaoa_maxiter,
            seed=req.seed or 42,
        ),
    )
    dijkstra = _classical_payload(outcome.classical["dijkstra"], nodes)
    astar = _classical_payload(outcome.classical["astar"], nodes)
    bellman = _classical_payload(outcome.classical["bellman_ford"], nodes)

    selected_index = outcome.quantum.selected_index
    quantum_path = (
        outcome.candidates[selected_index]
        if selected_index is not None and selected_index < len(outcome.candidates)
        else outcome.recommended_path
    )
    quantum_metrics = (
        outcome.classical["dijkstra"].metrics
        if quantum_path == outcome.recommended_path
        else None
    )
    if quantum_metrics is None and quantum_path:
        from services.routing import evaluate_path
        quantum_metrics = evaluate_path(G, quantum_path, weights)
    quantum_geometry = _osrm_service().geometry_for_path(quantum_path, nodes)
    quantum = {
        "path": quantum_path,
        "path_coords": quantum_geometry.coordinates,
        "distance": quantum_metrics.distance_km if quantum_metrics else 0.0,
        "time": quantum_metrics.time_min if quantum_metrics else 0.0,
        "cost": quantum_metrics.fuel_cost_inr if quantum_metrics else 0.0,
        "fuel_l": quantum_metrics.fuel_l if quantum_metrics else 0.0,
        "congestion_exposure": quantum_metrics.congestion_exposure if quantum_metrics else 0.0,
        "risk_exposure": quantum_metrics.risk_exposure if quantum_metrics else 0.0,
        "execution_time_ms": outcome.quantum.execution_time_ms,
        "quantum_cost": outcome.quantum.objective_value or 0.0,
        "circuit_depth": outcome.quantum.circuit_depth or 0,
        "num_qubits": outcome.quantum.num_qubits,
        "qaoa_layers": outcome.quantum.layers,
        "status": outcome.quantum.status.value,
        "backend": outcome.quantum.backend,
        "feasible": selected_index is not None,
        "feasible_probability": outcome.quantum.feasible_probability,
        "counts": outcome.quantum.counts,
        "fallback_used": selected_index is None,
        "error": outcome.quantum.error,
        "optimizer_evaluations": outcome.quantum.optimizer_evaluations,
        "geometry_source": quantum_geometry.source,
        "geometry_error": quantum_geometry.error,
    }

    # Alternatives are objective presets, each solved with the same verified Dijkstra implementation.
    priority_routes = {}
    for priority in ("fastest", "shortest", "least_fuel", "least_traffic", "balanced"):
        priority_weights = (
            EMERGENCY_RESPONSE_WEIGHTS
            if req.vehicle_type == "emergency"
            else WEIGHT_PRESETS[priority]
        )
        priority_graph, _ = build_city_graph(
            vehicle=req.vehicle_type,
            traffic_density=req.traffic_density,
            weather=req.weather,
            road_condition=req.road_condition,
            hour=hour,
            closed_segments=req.closed_segments,
            construction_segments=req.construction_segments,
            objective_weights=priority_weights,
        )
        alternative = optimize_graph(
            priority_graph, req.source, req.destination, priority_weights,
            OptimizationSettings(candidate_limit=1, layers=1, shots=32, maxiter=1, seed=req.seed or 42),
        ).classical["dijkstra"]
        payload = _classical_payload(alternative, nodes)
        priority_routes[priority] = {
            "path": payload["path"], "path_coords": payload["path_coords"],
            "distance": payload["distance"], "time": payload["time"], "cost": payload["cost"],
            "geometry_source": payload["geometry_source"],
            "geometry_error": payload["geometry_error"],
        }

    # ML traffic prediction using actual parameters
    base_time = dijkstra["time"] if dijkstra["feasible"] else 0
    predicted = _traffic_service().predict(
        hour=hour,
        day_of_week=datetime.now(timezone.utc).weekday(),
        weather="clear" if req.weather == "sunny" else req.weather,
        vehicle_density={"low": 0.25, "medium": 0.60, "high": 0.90}[req.traffic_density],
        road_category="arterial",
        surface=req.road_condition,
        base_travel_time_min=base_time,
    )
    traffic_pred = {
        "predicted_traffic": predicted.congestion_percent,
        "congestion_level": predicted.congestion_level,
        "confidence_score": None,
        "peak_hours": ["08:00–10:00", "17:00–20:00"],
        "estimated_delay_min": predicted.estimated_delay_min,
        "expected_travel_time_min": predicted.expected_travel_time_min,
        "model_name": predicted.model_name,
        "provenance": predicted.provenance,
        "dataset_fingerprint": predicted.dataset_fingerprint,
    }

    node_list, edge_list = get_graph_nodes_edges(G, nodes)

    # Scenario zones are parameter-driven and explicitly non-live.
    condition_zones = _build_condition_zones(req.traffic_density, req.weather, req.road_condition)

    geometry_sources = [
        dijkstra["geometry_source"], astar["geometry_source"],
        bellman["geometry_source"], quantum["geometry_source"],
        *(route["geometry_source"] for route in priority_routes.values()),
    ]
    fallback_count = sum(source != "osrm" for source in geometry_sources)
    road_geometry = {
        "provider": "OSRM",
        "profile": "driving",
        "source": "OpenStreetMap road network",
        "status": "complete" if fallback_count == 0 else "partial_fallback",
        "fallback_count": fallback_count,
        "route_count": len(geometry_sources),
        "note": "OSRM snaps the optimized landmark sequence to roads; scenario costs and route selection come from the curated Chandigarh graph.",
    }
    explanation = build_route_explanation(
        request=req.model_dump(),
        path=outcome.recommended_path,
        metrics={
            "distance": dijkstra["distance"],
            "time": dijkstra["time"],
            "cost": dijkstra["cost"],
            "congestion_exposure": dijkstra["congestion_exposure"],
            "risk_exposure": dijkstra["risk_exposure"],
            "objective_value": outcome.recommended_objective,
        },
        weights=weights.__dict__,
        graph=G,
        alternatives=outcome.alternatives,
        search_report=outcome.search_report,
        previous_path=req.previous_path,
        previous_scenario=req.previous_scenario,
    )

    record = OptimizationRecord(
        user_id=current_user.id,
        source=req.source, destination=req.destination,
        vehicle_type=req.vehicle_type, traffic_density=req.traffic_density,
        weather=req.weather, road_condition=req.road_condition,
        optimization_priority=req.optimization_priority,
        quantum_result=quantum, dijkstra_result=dijkstra,
        astar_result=astar, bellman_ford_result=bellman,
        traffic_prediction=traffic_pred,
        nodes=node_list, edges=edge_list,
        objective_value=outcome.recommended_objective,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return OptimizationResponse(
        id=record.id, request=req,
        quantum=QuantumResult(**quantum),
        dijkstra=AlgorithmResult(**dijkstra),
        astar=AlgorithmResult(**astar),
        bellman_ford=AlgorithmResult(**bellman),
        priority_routes=priority_routes,
        traffic_prediction=TrafficPrediction(**traffic_pred),
        nodes=[RouteNode(**n) for n in node_list],
        edges=edge_list,
        condition_zones=condition_zones,
        recommendation={
            "path": outcome.recommended_path,
            "path_coords": dijkstra["path_coords"],
            "geometry_source": dijkstra["geometry_source"],
            "geometry_error": dijkstra["geometry_error"],
            "distance": dijkstra["distance"],
            "time": dijkstra["time"],
            "cost": dijkstra["cost"],
            "fuel_l": dijkstra["fuel_l"],
            "objective_value": outcome.recommended_objective,
            "reason": explanation["summary"],
            "weights": weights.__dict__,
            "explanation": explanation,
        },
        route_analysis={
            "search_report": outcome.search_report,
            "alternatives": explanation["alternatives"],
            "constraints": explanation["constraints"],
        },
        road_geometry=road_geometry,
        network_version="curated-chandigarh-v4+osrm-geometry",
        created_at=record.created_at,
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(OptimizationRecord).filter(
        OptimizationRecord.user_id == current_user.id).all()
    total = len(records)
    quantum_results = [record.quantum_result or {} for record in records]
    traffic_results = [record.traffic_prediction or {} for record in records]
    feasible = [result for result in quantum_results if result.get("feasible", bool(result.get("path")))]
    agreement = []
    time_savings = []
    fuel_savings = []
    execution_times = []
    for record, quantum in zip(records, quantum_results):
        classical = [record.dijkstra_result or {}, record.astar_result or {}, record.bellman_ford_result or {}]
        recommended_path = (record.dijkstra_result or {}).get("path", [])
        if quantum.get("status") == "completed":
            agreement.append(quantum.get("path") == recommended_path)
        times = [item.get("time") for item in classical if item.get("time") is not None]
        costs = [item.get("cost") for item in classical if item.get("cost") is not None]
        if times and quantum.get("time") is not None:
            time_savings.append(max(0.0, max(times) - quantum["time"]))
        if costs and quantum.get("cost") is not None:
            fuel_savings.append(max(0.0, max(costs) - quantum["cost"]))
        if quantum.get("execution_time_ms") is not None:
            execution_times.append(quantum["execution_time_ms"])
    avg_traffic = (
        sum(float(item.get("predicted_traffic", 0)) for item in traffic_results) / total
        if total else 0.0
    )
    return DashboardStats(
        total_routes=total,
        avg_traffic=round(avg_traffic, 1),
        success_rate=round(len(feasible) / total * 100, 1) if total else 0.0,
        quantum_accuracy=round(sum(agreement) / len(agreement) * 100, 1) if agreement else 0.0,
        avg_time_saved=round(sum(time_savings) / len(time_savings), 1) if time_savings else 0.0,
        fuel_saved=round(sum(fuel_savings), 2),
        carbon_reduction=round(sum(fuel_savings) / 96.0 * 2.31, 2),
        avg_execution_time=round(sum(execution_times) / len(execution_times), 1) if execution_times else 0.0,
    )


@router.get("/history", response_model=List[RecentOptimization])
def get_history(limit: int = 10, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    records = (
        db.query(OptimizationRecord)
        .filter(OptimizationRecord.user_id == current_user.id)
        .order_by(OptimizationRecord.created_at.desc())
        .limit(limit).all()
    )
    return [
        RecentOptimization(
            id=r.id, source=r.source, destination=r.destination,
            algorithm="Hybrid",
            distance=r.quantum_result.get("distance", 0) if r.quantum_result else 0,
            time=r.quantum_result.get("time", 0) if r.quantum_result else 0,
            objective_value=r.objective_value or float((r.quantum_result or {}).get("quantum_cost", 0) or 0),
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/analytics")
def get_analytics(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    records = db.query(OptimizationRecord).filter(
        OptimizationRecord.user_id == current_user.id,
        OptimizationRecord.created_at >= since,
    ).order_by(OptimizationRecord.created_at.asc()).all()
    by_date: dict[str, list[OptimizationRecord]] = {}
    traffic_hours: dict[int, list[float]] = {}
    for record in records:
        key = record.created_at.date().isoformat()
        by_date.setdefault(key, []).append(record)
        hour = record.created_at.hour
        traffic_hours.setdefault(hour, []).append(float((record.traffic_prediction or {}).get("predicted_traffic", 0)))
    daily_stats = []
    for date, day_records in by_date.items():
        def average(field: str, key: str) -> float:
            values = [float((getattr(record, field) or {}).get(key, 0)) for record in day_records]
            return round(sum(values) / len(values), 3) if values else 0.0
        daily_stats.append({
            "date": date,
            "quantum": average("quantum_result", "execution_time_ms"),
            "dijkstra": average("dijkstra_result", "execution_time_ms"),
            "astar": average("astar_result", "execution_time_ms"),
            "bellman_ford": average("bellman_ford_result", "execution_time_ms"),
            "routes": len(day_records),
        })
    algorithms = [
        ("quantum", "quantum_result"), ("dijkstra", "dijkstra_result"),
        ("astar", "astar_result"), ("bellman_ford", "bellman_ford_result"),
    ]
    algorithm_comparison = []
    for name, field in algorithms:
        payloads = [getattr(record, field) or {} for record in records]
        algorithm_comparison.append({
            "algorithm": name,
            "runs": len(payloads),
            "avg_execution_ms": round(sum(float(item.get("execution_time_ms", 0)) for item in payloads) / len(payloads), 3) if payloads else 0,
            "avg_objective": round(sum(float(item.get("objective_value", item.get("quantum_cost", 0)) or 0) for item in payloads) / len(payloads), 6) if payloads else 0,
        })
    traffic_by_hour = [
        {"hour": f"{hour:02d}:00", "traffic": round(sum(values) / len(values), 1)}
        for hour, values in sorted(traffic_hours.items())
    ]
    return {"daily_stats": daily_stats, "algorithm_comparison": algorithm_comparison,
            "traffic_by_hour": traffic_by_hour, "provenance": "stored_executions"}


@router.get("/traffic/model")
def get_traffic_model(current_user: User = Depends(get_current_user)):
    service = _traffic_service()
    return {
        "status": "available_synthetic_scenario_only",
        "provenance": "synthetic_scenario",
        "dataset_fingerprint": service.report.dataset_fingerprint,
        "training_rows": service.report.training_rows,
        "test_rows": service.report.test_rows,
        "selected_model": service.model_name,
        "metrics": [metric.__dict__ for metric in service.report.metrics],
        "limitation": "Metrics describe the generated scenario dataset and are not evidence of real Chandigarh traffic accuracy.",
    }


@router.get("/{record_id}/export")
def export_report(record_id: int, format: str = "pdf",
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    from fastapi.responses import StreamingResponse
    import io

    record = db.query(OptimizationRecord).filter(
        OptimizationRecord.id == record_id,
        OptimizationRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, "Report not found")

    if format == "csv":
        import csv
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Field", "Value"])
        for k, v in [("Source", record.source), ("Destination", record.destination),
                     ("Vehicle", record.vehicle_type), ("Traffic", record.traffic_density),
                     ("Weather", record.weather), ("Road Condition", record.road_condition),
                     ("Priority", record.optimization_priority),
                     ("Objective Value", record.objective_value)]:
            w.writerow([k, v])
        if record.quantum_result:
            qr = record.quantum_result
            w.writerow(["QAOA Distance (km)", qr.get("distance")])
            w.writerow(["QAOA Time (min)", qr.get("time")])
            w.writerow(["QAOA Fuel Cost (INR)", qr.get("cost")])
            w.writerow(["QAOA Path", " → ".join(qr.get("path", []))])
            w.writerow(["Qubits", qr.get("num_qubits")])
            w.writerow(["Circuit Depth", qr.get("circuit_depth")])
        buf.seek(0)
        return StreamingResponse(io.BytesIO(buf.getvalue().encode()), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename=report-{record_id}.csv"})

    elif format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Route Report"
        headers = ["Algorithm", "Path", "Distance (km)", "Time (min)", "Fuel Cost (INR)", "Objective"]
        ws.append(headers)
        for algo, key in [("QAOA", "quantum_result"), ("Dijkstra", "dijkstra_result"),
                          ("A*", "astar_result"), ("Bellman-Ford", "bellman_ford_result")]:
            r = getattr(record, key) or {}
            ws.append([algo, " → ".join(r.get("path", [])),
                       r.get("distance", ""), r.get("time", ""),
                       r.get("cost", ""), r.get("objective_value", r.get("quantum_cost", ""))])
        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        return StreamingResponse(buf,
                                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": f"attachment; filename=report-{record_id}.xlsx"})

    else:  # pdf
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as rl_canvas
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, 750, "QuantumRoute AI — Optimization Report")
            c.setFont("Helvetica", 11)
            y = 720
            for label, val in [
                ("Route", f"{record.source}  →  {record.destination}"),
                ("Vehicle", record.vehicle_type.title()),
                ("Traffic Density", record.traffic_density.title()),
                ("Weather", record.weather.title()),
                ("Road Condition", record.road_condition.title()),
                ("Priority", record.optimization_priority.replace("_", " ").title()),
                ("Recommended Objective", f"{record.objective_value or 0:.6f}"),
            ]:
                c.drawString(72, y, f"{label}:  {val}"); y -= 18
            y -= 10
            c.setFont("Helvetica-Bold", 13)
            c.drawString(72, y, "Algorithm Comparison"); y -= 20
            c.setFont("Helvetica", 10)
            for algo, key in [("QAOA", "quantum_result"), ("Dijkstra", "dijkstra_result"),
                               ("A*", "astar_result"), ("Bellman-Ford", "bellman_ford_result")]:
                r = getattr(record, key) or {}
                path_str = " → ".join(r.get("path", []))[:70]
                c.drawString(72, y, f"{algo}: {r.get('distance','?')} km | "
                                    f"{r.get('time','?')} min | ₹{r.get('cost','?')} | {path_str}")
                y -= 16
            c.save(); buf.seek(0)
        except ImportError:
            buf = io.BytesIO(b"Install reportlab: pip install reportlab")
        return StreamingResponse(buf, media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename=report-{record_id}.pdf"})
