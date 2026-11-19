from quantum.qaoa_engine import build_city_graph
from routes.route_routes import get_locations


def test_removed_sukhna_location_is_not_routable():
    locations = get_locations()
    graph, _ = build_city_graph()

    assert "Sukhna Lake" not in locations
    assert "Sukhna Lake" not in graph
    assert all("Sukhna Lake" not in edge for edge in graph.edges)
