from services.route_explanation import build_route_explanation
from quantum.qaoa_engine import build_city_graph
from routes.route_routes import WEIGHT_PRESETS
from services.optimization import OptimizationSettings, optimize_graph


def test_explanation_uses_active_scenario_and_measured_route_metrics():
    explanation = build_route_explanation(
        request={
            "vehicle_type": "truck",
            "traffic_density": "high",
            "weather": "rain",
            "road_condition": "moderate",
            "optimization_priority": "shortest",
            "time_of_day": "09:00",
        },
        path=["Rock Garden", "Panchkula Sector 5", "Elante Mall"],
        metrics={
            "distance": 17.71,
            "time": 113.8,
            "cost": 469.38,
            "congestion_exposure": 2.0,
            "risk_exposure": 1.05,
            "objective_value": 1.3101,
        },
        weights={"distance": 0.8, "time": 0.1, "fuel": 0.05, "congestion": 0.05, "risk": 0.0},
    )

    assert explanation["headline"] == "Shortest-route objective selected this path"
    assert "17.7 km" in explanation["summary"]
    assert "113.8 min" in explanation["summary"]
    factors = {factor["label"]: factor for factor in explanation["factors"]}
    assert factors["Vehicle"]["value"] == "Truck"
    assert "local roads" in factors["Vehicle"]["effect"]
    assert factors["Traffic"]["value"] == "High"
    assert factors["Weather"]["value"] == "Rain"
    assert factors["Road condition"]["value"] == "Moderate"
    assert factors["Priority"]["value"] == "Shortest route"


def test_custom_weights_explanation_names_the_dominant_objective():
    explanation = build_route_explanation(
        request={
            "vehicle_type": "car",
            "traffic_density": "medium",
            "weather": "sunny",
            "road_condition": "good",
            "optimization_priority": "balanced",
            "time_of_day": "14:00",
            "weights": {"distance": 5, "time": 10, "fuel": 10, "congestion": 70, "risk": 5},
        },
        path=["A", "B"],
        metrics={
            "distance": 8.0,
            "time": 22.0,
            "cost": 90.0,
            "congestion_exposure": 0.2,
            "risk_exposure": 0.1,
            "objective_value": 0.42,
        },
        weights={"distance": 0.05, "time": 0.1, "fuel": 0.1, "congestion": 0.7, "risk": 0.05},
    )

    assert explanation["headline"] == "Custom objective selected this path"
    assert explanation["dominant_objective"] == "Congestion"
    assert "70%" in explanation["factors"][0]["effect"]


def test_decision_explanation_is_derived_from_segments_and_alternatives():
    graph, _ = build_city_graph(
        vehicle="emergency",
        traffic_density="medium",
        weather="rain",
        road_condition="moderate",
        hour=9,
    )
    outcome = optimize_graph(
        graph,
        "PGI Hospital",
        "Elante Mall",
        WEIGHT_PRESETS["fastest"],
        OptimizationSettings(candidate_limit=5, layers=1, shots=32, maxiter=1),
    )
    selected = outcome.classical["dijkstra"].metrics

    explanation = build_route_explanation(
        request={
            "vehicle_type": "emergency",
            "traffic_density": "medium",
            "weather": "rain",
            "road_condition": "moderate",
            "optimization_priority": "fastest",
            "time_of_day": "09:00",
        },
        path=outcome.recommended_path,
        metrics={
            "distance": selected.distance_km,
            "time": selected.time_min,
            "cost": selected.fuel_cost_inr,
            "congestion_exposure": selected.congestion_exposure,
            "risk_exposure": selected.risk_exposure,
            "objective_value": selected.objective_value,
        },
        weights=WEIGHT_PRESETS["fastest"].__dict__,
        graph=graph,
        alternatives=outcome.alternatives,
        search_report=outcome.search_report,
        previous_path=["PGI Hospital", "Mohali IT Park", "Elante Mall"],
    )

    characteristics = explanation["route_characteristics"]
    assert characteristics["minimum_width_m"] > 0
    assert characteristics["speed_limits_kmh"]
    assert characteristics["segments"][0]["segment"]
    assert explanation["impact_breakdown"]["traffic_delay_min"] > 0
    assert explanation["impact_breakdown"]["weather_delay_min"] > 0
    assert explanation["alternatives"][0]["selected"] is True
    assert explanation["alternatives"][1]["why_not_selected"]
    assert explanation["search_scope"]["exhaustive_path_enumeration"] is False
    comparison = explanation["previous_route_comparison"]
    assert comparison["status"] == "changed"
    assert comparison["previous_path"] == ["PGI Hospital", "Mohali IT Park", "Elante Mall"]
    assert comparison["reasons"]


def test_unchanged_route_explains_the_actual_condition_change():
    graph, _ = build_city_graph(
        vehicle="car", traffic_density="high", weather="rain", road_condition="good", hour=9
    )
    outcome = optimize_graph(
        graph,
        "PGI Hospital",
        "Elante Mall",
        WEIGHT_PRESETS["fastest"],
        OptimizationSettings(candidate_limit=4, layers=1, shots=32, maxiter=4),
    )
    selected = outcome.classical["dijkstra"].metrics
    explanation = build_route_explanation(
        request={
            "vehicle_type": "car",
            "traffic_density": "high",
            "weather": "rain",
            "road_condition": "good",
            "optimization_priority": "fastest",
            "time_of_day": "09:00",
        },
        previous_scenario={
            "vehicle_type": "car",
            "traffic_density": "low",
            "weather": "sunny",
            "road_condition": "good",
            "optimization_priority": "fastest",
            "time_of_day": "09:00",
        },
        path=outcome.recommended_path,
        previous_path=outcome.recommended_path,
        metrics={
            "distance": selected.distance_km,
            "time": selected.time_min,
            "cost": selected.fuel_cost_inr,
            "objective_value": selected.objective_value,
        },
        weights=WEIGHT_PRESETS["fastest"].__dict__,
        graph=graph,
        alternatives=outcome.alternatives,
        search_report=outcome.search_report,
    )

    reasons = " ".join(explanation["previous_route_comparison"]["reasons"])
    assert "Traffic density changed from Low to High" in reasons
    assert "Weather changed from Sunny to Rain" in reasons
    assert "still has the lowest" in reasons
