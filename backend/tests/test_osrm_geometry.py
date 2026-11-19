import httpx

from services.osrm import OSRMGeometryService


NODES = {
    "Start": {"lat": 30.7422, "lng": 76.8183},
    "Via": {"lat": 30.7526, "lng": 76.8089},
    "Finish": {"lat": 30.7056, "lng": 76.8013},
}


def test_osrm_returns_full_road_geometry_in_leaflet_coordinate_order():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/route/v1/driving/76.818300,30.742200;76.808900,30.752600;76.801300,30.705600"
        )
        assert request.url.params["geometries"] == "geojson"
        assert request.url.params["overview"] == "full"
        return httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [{
                    "distance": 8200.0,
                    "duration": 1120.0,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [76.8183, 30.7422],
                            [76.8151, 30.7449],
                            [76.8013, 30.7056],
                        ],
                    },
                }],
                "waypoints": [],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(route))
    result = OSRMGeometryService(client=client).geometry_for_path(
        ["Start", "Via", "Finish"], NODES
    )

    assert result.source == "osrm"
    assert result.coordinates == [
        [30.7422, 76.8183],
        [30.7449, 76.8151],
        [30.7056, 76.8013],
    ]
    assert result.distance_km == 8.2
    assert result.duration_min == 18.6667


def test_osrm_failure_is_explicit_and_preserves_waypoint_geometry():
    def unavailable(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"code": "ServiceUnavailable"})

    client = httpx.Client(transport=httpx.MockTransport(unavailable))
    result = OSRMGeometryService(client=client).geometry_for_path(
        ["Start", "Finish"], NODES
    )

    assert result.source == "waypoint_fallback"
    assert result.coordinates == [[30.7422, 76.8183], [30.7056, 76.8013]]
    assert result.error == "osrm_http_503"


def test_one_waypoint_path_does_not_call_osrm():
    def fail_if_called(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("OSRM must not be called for a one-node path")

    client = httpx.Client(transport=httpx.MockTransport(fail_if_called))
    result = OSRMGeometryService(client=client).geometry_for_path(["Start"], NODES)

    assert result.source == "waypoint_fallback"
    assert result.coordinates == [[30.7422, 76.8183]]
    assert result.error == "insufficient_waypoints"
