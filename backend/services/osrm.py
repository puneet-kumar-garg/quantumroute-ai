"""OSRM road-geometry adapter.

The optimization graph remains the authoritative source for route selection and
scenario costs. OSRM is used only to snap the selected landmark sequence to
real OpenStreetMap roads for display.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Mapping, Sequence

import httpx


@dataclass(frozen=True)
class RoadGeometry:
    coordinates: list[list[float]]
    source: str
    distance_km: float | None = None
    duration_min: float | None = None
    error: str | None = None


class OSRMGeometryService:
    def __init__(
        self,
        *,
        base_url: str = "https://router.project-osrm.org",
        timeout_seconds: float = 6.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"User-Agent": "QuantumRouteAI/1.0 (capstone road geometry)"},
        )
        self._cache: dict[tuple[tuple[float, float], ...], RoadGeometry] = {}
        self._cache_lock = Lock()

    @staticmethod
    def _waypoints(
        path: Sequence[str], nodes: Mapping[str, Mapping[str, float]]
    ) -> list[list[float]]:
        return [
            [float(nodes[name]["lat"]), float(nodes[name]["lng"])]
            for name in path
            if name in nodes
        ]

    def geometry_for_path(
        self,
        path: Sequence[str],
        nodes: Mapping[str, Mapping[str, float]],
    ) -> RoadGeometry:
        waypoints = self._waypoints(path, nodes)
        if len(waypoints) < 2:
            return RoadGeometry(
                coordinates=waypoints,
                source="waypoint_fallback",
                error="insufficient_waypoints",
            )

        cache_key = tuple((lat, lng) for lat, lng in waypoints)
        with self._cache_lock:
            cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        coordinate_string = ";".join(
            f"{lng:.6f},{lat:.6f}" for lat, lng in waypoints
        )
        url = f"{self.base_url}/route/v1/driving/{coordinate_string}"
        try:
            response = self.client.get(
                url,
                params={
                    "geometries": "geojson",
                    "overview": "full",
                    "steps": "false",
                    "alternatives": "false",
                },
            )
        except httpx.HTTPError as exc:
            return RoadGeometry(
                coordinates=waypoints,
                source="waypoint_fallback",
                error=f"osrm_{exc.__class__.__name__.lower()}",
            )

        if response.status_code != 200:
            return RoadGeometry(
                coordinates=waypoints,
                source="waypoint_fallback",
                error=f"osrm_http_{response.status_code}",
            )

        try:
            payload = response.json()
            route = payload["routes"][0]
            coordinates = [
                [round(float(lat), 6), round(float(lng), 6)]
                for lng, lat in route["geometry"]["coordinates"]
            ]
            if payload.get("code") != "Ok" or len(coordinates) < 2:
                raise ValueError("OSRM returned no usable route")
            result = RoadGeometry(
                coordinates=coordinates,
                source="osrm",
                distance_km=round(float(route["distance"]) / 1000.0, 4),
                duration_min=round(float(route["duration"]) / 60.0, 4),
            )
        except (KeyError, IndexError, TypeError, ValueError):
            return RoadGeometry(
                coordinates=waypoints,
                source="waypoint_fallback",
                error="osrm_invalid_response",
            )

        with self._cache_lock:
            self._cache[cache_key] = result
        return result
