from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import Base, get_db
from main import app
from services.osrm import RoadGeometry


def test_cookie_auth_and_route_optimization(tmp_path: Path, monkeypatch):
    class DeterministicRoadGeometry:
        def geometry_for_path(self, path, nodes):
            points = [[nodes[name]["lat"], nodes[name]["lng"]] for name in path]
            if len(points) > 1:
                midpoint = [
                    round((points[0][0] + points[1][0]) / 2, 6),
                    round((points[0][1] + points[1][1]) / 2, 6),
                ]
                points.insert(1, midpoint)
            return RoadGeometry(points, "osrm", 8.2, 18.6)

    monkeypatch.setattr(
        "routes.route_routes._osrm_service",
        lambda: DeterministicRoadGeometry(),
    )
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False}
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            registration = client.post(
                "/api/auth/register",
                json={
                    "email": "route@example.com",
                    "username": "route_user",
                    "full_name": "Route User",
                    "password": "correct-horse-battery",
                },
            )
            assert registration.status_code == 201

            login = client.post(
                "/api/auth/login",
                data={"username": "route@example.com", "password": "correct-horse-battery"},
            )
            assert login.status_code == 200
            assert login.cookies.get("access_token")
            assert client.get("/api/auth/me").status_code == 200
            segments_response = client.get("/api/routes/segments")
            assert segments_response.status_code == 200
            segments = segments_response.json()
            assert segments
            assert len({segment["id"] for segment in segments}) == len(segments)
            assert all(segment["label"] and segment["road_type"] for segment in segments)

            response = client.post(
                "/api/routes/optimize",
                json={
                    "source": "Rock Garden",
                    "destination": "Elante Mall",
                    "vehicle_type": "car",
                    "traffic_density": "medium",
                    "weather": "sunny",
                    "road_condition": "good",
                    "optimization_priority": "balanced",
                    "time_of_day": "09:00",
                    "qaoa_layers": 1,
                    "qaoa_shots": 32,
                    "qaoa_maxiter": 8,
                    "seed": 7,
                },
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["network_version"] == "curated-chandigarh-v4+osrm-geometry"
            assert payload["dijkstra"]["feasible"] is True
            assert payload["astar"]["objective_value"] == payload["dijkstra"]["objective_value"]
            assert payload["bellman_ford"]["objective_value"] == payload["dijkstra"]["objective_value"]
            assert payload["traffic_prediction"]["provenance"] == "synthetic_scenario_model"
            assert payload["quantum"]["backend"] == "qiskit_aer_simulator"
            assert payload["dijkstra"]["geometry_source"] == "osrm"
            assert len(payload["dijkstra"]["path_coords"]) > len(payload["dijkstra"]["path"])
            assert payload["priority_routes"]["shortest"]["geometry_source"] == "osrm"
            assert payload["road_geometry"]["provider"] == "OSRM"
            assert payload["recommendation"]["explanation"]["headline"] == "Balanced objective selected this path"
            assert payload["recommendation"]["explanation"]["factors"][0]["label"] == "Priority"
            assert payload["recommendation"]["explanation"]["route_characteristics"]["segments"]
            assert payload["recommendation"]["explanation"]["alternatives"]
            assert payload["recommendation"]["path_coords"] == payload["dijkstra"]["path_coords"]
            assert payload["recommendation"]["geometry_source"] == payload["dijkstra"]["geometry_source"]
            assert payload["route_analysis"]["search_report"]["exhaustive_path_enumeration"] is False
            assert payload["route_analysis"]["search_report"]["optimal_route_guarantee"] == "exact_non_negative_shortest_path"
            assert all(edge["road_width_m"] > 0 for edge in payload["edges"])
            assert all("traffic_delay_min" in edge for edge in payload["edges"])
            assert "km" in payload["recommendation"]["reason"]

            assert client.post("/api/auth/logout").status_code == 204
            assert client.get("/api/auth/me").status_code == 401
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
