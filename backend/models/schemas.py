from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-z0-9_]+$")
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ObjectiveWeights(BaseModel):
    distance: float = Field(ge=0, le=1000)
    time: float = Field(ge=0, le=1000)
    fuel: float = Field(ge=0, le=1000)
    congestion: float = Field(ge=0, le=1000)
    risk: float = Field(ge=0, le=1000)


class RouteRequest(BaseModel):
    source: str
    destination: str
    vehicle_type: Literal["car", "bike", "truck", "emergency"]
    traffic_density: Literal["low", "medium", "high"]
    weather: Literal["sunny", "rain", "fog"]
    road_condition: Literal["good", "moderate", "poor"]
    optimization_priority: Literal["fastest", "shortest", "least_fuel", "least_traffic", "balanced"]
    time_of_day: Optional[str] = Field(default="09:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    qaoa_layers: Optional[int] = Field(default=2, ge=1, le=5)
    qaoa_shots: Optional[int] = Field(default=1024, ge=32, le=8192)
    qaoa_maxiter: Optional[int] = Field(default=80, ge=1, le=500)
    seed: Optional[int] = Field(default=42, ge=0, le=2_147_483_647)
    weights: Optional[ObjectiveWeights] = None
    traffic_overlay: Optional[bool] = False
    animate_vehicle: Optional[bool] = True
    previous_path: Optional[List[str]] = Field(default=None, max_length=32)
    previous_scenario: Optional[dict[str, str]] = None
    closed_segments: List[str] = Field(default_factory=list, max_length=64)
    construction_segments: List[str] = Field(default_factory=list, max_length=64)


class RouteNode(BaseModel):
    id: str
    name: str
    lat: float
    lng: float


class AlgorithmResult(BaseModel):
    algorithm: str
    path: List[str]
    path_coords: List[List[float]]
    distance: float
    time: float
    cost: float
    fuel_l: float
    congestion_exposure: float
    risk_exposure: float
    execution_time_ms: float
    memory_usage_kb: float
    feasible: bool = True
    objective_value: Optional[float] = None
    provenance: str = "measured_execution"
    geometry_source: str = "waypoint_fallback"
    geometry_error: Optional[str] = None


class QuantumResult(BaseModel):
    path: List[str]
    path_coords: List[List[float]]
    distance: float
    time: float
    cost: float
    fuel_l: float
    congestion_exposure: float
    risk_exposure: float
    execution_time_ms: float
    quantum_cost: float
    circuit_depth: int
    num_qubits: int
    qaoa_layers: int
    status: str = "completed"
    backend: Optional[str] = None
    feasible: bool = True
    feasible_probability: Optional[float] = None
    counts: dict[str, int] = Field(default_factory=dict)
    fallback_used: bool = False
    error: Optional[str] = None
    optimizer_evaluations: Optional[int] = None
    geometry_source: str = "waypoint_fallback"
    geometry_error: Optional[str] = None


class TrafficPrediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    predicted_traffic: float
    congestion_level: str
    confidence_score: Optional[float] = None
    peak_hours: List[str]
    estimated_delay_min: Optional[float] = 0.0
    expected_travel_time_min: Optional[float] = None
    model_name: Optional[str] = None
    provenance: str = "synthetic_scenario_model"
    dataset_fingerprint: Optional[str] = None


class OptimizationResponse(BaseModel):
    id: int
    request: RouteRequest
    quantum: QuantumResult
    dijkstra: AlgorithmResult
    astar: AlgorithmResult
    bellman_ford: AlgorithmResult
    priority_routes: dict  # {shortest, least_fuel, balanced} each with path + path_coords
    traffic_prediction: TrafficPrediction
    nodes: List[RouteNode]
    edges: List[Any]
    condition_zones: List[Any] = Field(default_factory=list)
    recommendation: dict[str, Any] = Field(default_factory=dict)
    route_analysis: dict[str, Any] = Field(default_factory=dict)
    road_geometry: dict[str, Any] = Field(default_factory=dict)
    network_version: str = "curated-chandigarh-v2"
    created_at: datetime


class DashboardStats(BaseModel):
    total_routes: int
    avg_traffic: float
    success_rate: float
    quantum_accuracy: float
    avg_time_saved: float
    fuel_saved: float
    carbon_reduction: float
    avg_execution_time: float


class RecentOptimization(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    destination: str
    algorithm: str
    distance: float
    time: float
    objective_value: float
    created_at: datetime
