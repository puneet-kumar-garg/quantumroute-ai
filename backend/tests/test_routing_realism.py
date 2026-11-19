import pytest

from quantum.qaoa_engine import build_city_graph
from routes.route_routes import WEIGHT_PRESETS
from services.routing import CostWeights, solve_all_classical


SOURCE = "PGI Hospital"
DESTINATION = "Elante Mall"


def _fastest(vehicle: str):
    graph, _ = build_city_graph(
        vehicle=vehicle,
        traffic_density="medium",
        weather="sunny",
        road_condition="good",
        hour=9,
    )
    result = solve_all_classical(
        graph, SOURCE, DESTINATION, WEIGHT_PRESETS["fastest"]
    )["dijkstra"]
    return graph, result


def test_emergency_route_avoids_unjustified_geographic_detour():
    _, car = _fastest("car")
    _, emergency = _fastest("emergency")

    assert emergency.metrics.time_min < car.metrics.time_min
    assert emergency.metrics.distance_km <= car.metrics.distance_km * 1.15


def test_emergency_speed_advantage_is_bounded_on_the_same_highway_segment():
    car_graph, _ = _fastest("car")
    emergency_graph, _ = _fastest("emergency")

    car_time = car_graph["PGI Hospital"]["Mohali IT Park"]["time_min"]
    emergency_time = emergency_graph["PGI Hospital"]["Mohali IT Park"]["time_min"]

    assert emergency_time < car_time
    assert emergency_time >= car_time * 0.45


def test_route_edges_expose_measured_delay_and_accessibility_components():
    graph, result = _fastest("emergency")

    for start, end in zip(result.path, result.path[1:]):
        edge = graph[start][end]
        assert edge["road_width_m"] > 0
        assert edge["accessible"] is True
        assert edge["free_flow_time_min"] > 0
        assert edge["traffic_delay_min"] >= 0
        assert edge["weather_delay_min"] >= 0
        assert edge["surface_delay_min"] >= 0
        assert edge["intersection_delay_min"] >= 0
        assert edge["time_min"] == pytest.approx(
            edge["free_flow_time_min"]
            + edge["traffic_delay_min"]
            + edge["weather_delay_min"]
            + edge["surface_delay_min"]
            + edge["intersection_delay_min"],
            abs=0.06,
        )


def test_closed_segment_is_removed_and_construction_delay_is_measured():
    segment = "PGI Hospital|Punjab University"
    closed_graph, _ = build_city_graph(closed_segments=[segment])
    construction_graph, _ = build_city_graph(construction_segments=[segment])
    baseline_graph, _ = build_city_graph()

    assert not closed_graph.has_edge("PGI Hospital", "Punjab University")
    assert not closed_graph.has_edge("Punjab University", "PGI Hospital")
    assert construction_graph["PGI Hospital"]["Punjab University"]["construction"] is True
    assert construction_graph["PGI Hospital"]["Punjab University"]["time_min"] > baseline_graph["PGI Hospital"]["Punjab University"]["time_min"]


def test_parallel_road_choice_uses_the_active_objective_not_a_fixed_fastest_edge():
    fastest_graph, _ = build_city_graph(
        traffic_density="high",
        weather="fog",
        road_condition="poor",
        objective_weights=CostWeights(distance=0, time=1, fuel=0, congestion=0, risk=0),
    )
    fuel_graph, _ = build_city_graph(
        traffic_density="high",
        weather="fog",
        road_condition="poor",
        objective_weights=CostWeights(distance=0, time=0, fuel=1, congestion=0, risk=0),
    )

    fastest = fastest_graph["Sector 22 Market"]["ISBT Sector 43"]
    fuel_saving = fuel_graph["Sector 22 Market"]["ISBT Sector 43"]
    assert fastest["road_type"] == "local"
    assert fuel_saving["road_type"] == "arterial"
    assert fastest["time_min"] < fuel_saving["time_min"]
    assert fuel_saving["fuel_l"] < fastest["fuel_l"]
