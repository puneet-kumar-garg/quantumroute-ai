from quantum.qaoa_engine import build_city_graph
from models.schemas import RouteRequest
from routes.route_routes import WEIGHT_PRESETS, _weights_for_request
from services.routing import solve_all_classical


SOURCE = "Sector 17 Plaza"
DESTINATION = "Chandigarh Airport"


def solve(vehicle, traffic, weather, road, priority="shortest"):
    graph, _ = build_city_graph(
        vehicle=vehicle,
        traffic_density=traffic,
        weather=weather,
        road_condition=road,
        hour=9,
    )
    return solve_all_classical(
        graph, SOURCE, DESTINATION, WEIGHT_PRESETS[priority]
    )["dijkstra"]


def test_vehicle_type_changes_the_feasible_network_preference():
    car = solve("car", "medium", "sunny", "good")
    bike = solve("bike", "medium", "sunny", "good")
    truck = solve("truck", "medium", "sunny", "good")
    emergency = solve("emergency", "medium", "sunny", "good")

    assert len({result.metrics.time_min for result in (car, bike, truck, emergency)}) == 4
    assert emergency.metrics.time_min < truck.metrics.time_min
    assert emergency.metrics.time_min < car.metrics.time_min
    assert truck.metrics.fuel_l > car.metrics.fuel_l > bike.metrics.fuel_l


def test_traffic_weather_and_road_controls_recalculate_route_costs():
    low_clear = solve("car", "low", "sunny", "good")
    high_clear = solve("car", "high", "sunny", "good")
    rainy = solve("car", "medium", "rain", "good")
    moderate_road = solve("car", "medium", "sunny", "moderate")

    assert high_clear.metrics.time_min > low_clear.metrics.time_min
    assert rainy.metrics.time_min > low_clear.metrics.time_min
    assert moderate_road.metrics.risk_exposure > low_clear.metrics.risk_exposure


def test_optimization_priority_can_select_a_different_route():
    shortest = solve("car", "medium", "sunny", "good", "shortest")
    least_traffic = solve("car", "medium", "sunny", "good", "least_traffic")

    assert shortest.path != least_traffic.path
    assert shortest.metrics.distance_km < least_traffic.metrics.distance_km
    assert least_traffic.metrics.congestion_exposure < shortest.metrics.congestion_exposure


def test_emergency_vehicle_uses_response_time_policy_without_custom_weights():
    request = RouteRequest(
        source="PGI Hospital",
        destination="Elante Mall",
        vehicle_type="emergency",
        traffic_density="medium",
        weather="sunny",
        road_condition="good",
        optimization_priority="shortest",
        time_of_day="09:00",
    )

    weights = _weights_for_request(request)

    assert weights.time >= 0.65
    assert weights.risk >= 0.05
    assert weights.distance < weights.time
