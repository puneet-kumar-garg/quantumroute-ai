from itertools import product

import networkx as nx
import pytest

from quantum.qaoa_engine import CHANDIGARH_NODES, build_city_graph
from routes.route_routes import EMERGENCY_RESPONSE_WEIGHTS, WEIGHT_PRESETS
from services.routing import edge_objective, evaluate_path, solve_all_classical


def test_all_source_destination_and_vehicle_combinations_are_connected_and_consistent():
    locations = list(CHANDIGARH_NODES)
    for vehicle in ("car", "bike", "truck", "emergency"):
        graph, _ = build_city_graph(
            vehicle=vehicle,
            traffic_density="medium",
            weather="sunny",
            road_condition="good",
            hour=9,
        )
        weights = EMERGENCY_RESPONSE_WEIGHTS if vehicle == "emergency" else WEIGHT_PRESETS["balanced"]
        for source, destination in product(locations, repeat=2):
            if source == destination:
                continue
            results = solve_all_classical(graph, source, destination, weights)
            assert all(result.feasible for result in results.values()), (
                vehicle,
                source,
                destination,
            )
            paths = [result.path for result in results.values()]
            assert all(path[0] == source and path[-1] == destination for path in paths)
            assert all(len(path) == len(set(path)) for path in paths)
            objectives = [result.objective_value for result in results.values()]
            assert max(objectives) - min(objectives) < 1e-9


def test_environment_matrix_recalculates_every_edge_from_measured_components():
    for vehicle, traffic, weather, road, hour in product(
        ("car", "bike", "truck", "emergency"),
        ("low", "medium", "high"),
        ("sunny", "rain", "fog"),
        ("good", "moderate", "poor"),
        (9, 14),
    ):
        graph, _ = build_city_graph(
            vehicle=vehicle,
            traffic_density=traffic,
            weather=weather,
            road_condition=road,
            hour=hour,
        )
        weights = EMERGENCY_RESPONSE_WEIGHTS if vehicle == "emergency" else WEIGHT_PRESETS["balanced"]
        result = solve_all_classical(
            graph, "PGI Hospital", "Elante Mall", weights
        )["dijkstra"]
        assert result.feasible, (vehicle, traffic, weather, road, hour)
        for start, end in zip(result.path, result.path[1:]):
            edge = graph[start][end]
            component_total = sum(
                edge[key]
                for key in (
                    "free_flow_time_min",
                    "traffic_delay_min",
                    "weather_delay_min",
                    "surface_delay_min",
                    "intersection_delay_min",
                    "construction_delay_min",
                )
            )
            assert edge["time_min"] == pytest.approx(component_total, abs=0.06)
            assert edge_objective(edge, weights) >= 0


def test_emergency_routes_do_not_take_unjustified_all_pairs_detours():
    locations = list(CHANDIGARH_NODES)
    car_graph, _ = build_city_graph(
        vehicle="car", traffic_density="medium", weather="sunny", road_condition="good", hour=9
    )
    emergency_graph, _ = build_city_graph(
        vehicle="emergency", traffic_density="medium", weather="sunny", road_condition="good", hour=9
    )
    car_weight = lambda _u, _v, edge: edge_objective(edge, WEIGHT_PRESETS["fastest"])
    emergency_weight = lambda _u, _v, edge: edge_objective(edge, EMERGENCY_RESPONSE_WEIGHTS)

    for source, destination in product(locations, repeat=2):
        if source == destination:
            continue
        car_path = nx.dijkstra_path(car_graph, source, destination, weight=car_weight)
        emergency_path = nx.dijkstra_path(
            emergency_graph, source, destination, weight=emergency_weight
        )
        car = evaluate_path(car_graph, car_path, WEIGHT_PRESETS["fastest"])
        emergency = evaluate_path(
            emergency_graph, emergency_path, EMERGENCY_RESPONSE_WEIGHTS
        )
        unjustified_detour = (
            emergency.distance_km > car.distance_km * 1.35
            and emergency.time_min >= car.time_min * 0.85
        )
        assert not unjustified_detour, (
            source,
            destination,
            car_path,
            emergency_path,
        )
