export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'admin' | 'user';
  created_at: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RouteOptimizationRequest {
  source: string;
  destination: string;
  vehicle_type: 'car' | 'bike' | 'truck' | 'emergency';
  traffic_density: 'low' | 'medium' | 'high';
  weather: 'sunny' | 'rain' | 'fog';
  road_condition: 'good' | 'moderate' | 'poor';
  optimization_priority: 'fastest' | 'shortest' | 'least_fuel' | 'least_traffic' | 'balanced';
  time_of_day?: string;
  qaoa_layers?: number;
  qaoa_shots?: number;
  qaoa_maxiter?: number;
  seed?: number;
  weights?: { distance: number; time: number; fuel: number; congestion: number; risk: number };
  traffic_overlay?: boolean;
  animate_vehicle?: boolean;
  previous_path?: string[];
  previous_scenario?: Partial<Record<'vehicle_type' | 'traffic_density' | 'weather' | 'road_condition' | 'optimization_priority' | 'time_of_day', string>>;
  closed_segments?: string[];
  construction_segments?: string[];
}

export interface RouteNode {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface RouteEdge {
  from: string;
  to: string;
  distance: number;
  time: number;
  traffic_factor: number;
  geometry?: [number, number][];
  fuel_l?: number;
  congestion?: number;
  risk?: number;
  segment_id?: string;
  segment_label?: string;
  road_type?: string;
  road_width_m?: number;
  lanes?: number;
  speed_limit_kmh?: number;
  accessible?: boolean;
  construction?: boolean;
  free_flow_time_min?: number;
  traffic_delay_min?: number;
  weather_delay_min?: number;
  surface_delay_min?: number;
  intersection_delay_min?: number;
  construction_delay_min?: number;
}

export interface RoadSegmentCatalog {
  id: string;
  label: string;
  road_type: string;
  distance_km: number;
  lanes: number;
  speed_limit_kmh: number;
}

export interface RouteSegmentEvidence {
  segment: string;
  segment_id: string;
  road_type: string;
  distance_km: number;
  expected_time_min: number;
  road_width_m: number;
  lanes: number;
  speed_limit_kmh: number;
  accessible: boolean;
  construction: boolean;
  free_flow_time_min: number;
  traffic_delay_min: number;
  weather_delay_min: number;
  surface_delay_min: number;
  intersection_delay_min: number;
  construction_delay_min: number;
}

export interface RouteAlternativeAnalysis {
  rank: number;
  selected: boolean;
  path: string[];
  distance_km: number;
  time_min: number;
  fuel_l: number;
  fuel_cost_inr: number;
  congestion_exposure: number;
  risk_exposure: number;
  objective_value: number;
  objective_delta: number;
  why_not_selected: string[];
}

export interface RouteDecisionExplanation {
  headline: string;
  summary: string;
  dominant_objective: string;
  factors: Array<{ label: string; value: string; effect: string }>;
  path: string[];
  route_characteristics: {
    minimum_width_m: number;
    maximum_width_m: number;
    speed_limits_kmh: number[];
    road_types: string[];
    all_segments_accessible: boolean;
    construction_segments: string[];
    segments: RouteSegmentEvidence[];
  };
  impact_breakdown: Record<'free_flow_time_min' | 'traffic_delay_min' | 'weather_delay_min' | 'surface_delay_min' | 'intersection_delay_min' | 'construction_delay_min', number>;
  alternatives: RouteAlternativeAnalysis[];
  search_scope: {
    optimal_route_guarantee?: string;
    alternative_search?: string;
    exhaustive_path_enumeration?: boolean;
    alternatives_evaluated?: number;
    alternative_limit?: number;
    reachable_nodes?: number;
    graph_nodes?: number;
    graph_edges?: number;
    note?: string;
  };
  constraints: {
    excluded_segments: Array<Record<string, unknown>>;
    closed_segments: string[];
  };
  previous_route_comparison: {
    status: 'not_available' | 'unchanged' | 'changed';
    previous_path: string[];
    valid_under_current_conditions?: boolean;
    affected_segments?: Array<Record<string, unknown>>;
    previous_metrics?: { distance_km: number; time_min: number; fuel_cost_inr: number; objective_value: number };
    reasons: string[];
  };
}

export interface AlgorithmResult {
  algorithm: string;
  path: string[];
  path_coords: [number, number][];
  distance: number;
  time: number;
  cost: number;
  fuel_l: number;
  congestion_exposure: number;
  risk_exposure: number;
  execution_time_ms: number;
  memory_usage_kb: number;
  feasible: boolean;
  objective_value: number | null;
  provenance: string;
  geometry_source: 'osrm' | 'waypoint_fallback';
  geometry_error: string | null;
}

export interface QuantumResult {
  path: string[];
  path_coords: [number, number][];
  distance: number;
  time: number;
  cost: number;
  fuel_l: number;
  congestion_exposure: number;
  risk_exposure: number;
  execution_time_ms: number;
  quantum_cost: number;
  circuit_depth: number;
  num_qubits: number;
  qaoa_layers: number;
  status: 'completed' | 'not_required' | 'unavailable' | 'failed';
  backend: string | null;
  feasible: boolean;
  feasible_probability: number | null;
  counts: Record<string, number>;
  fallback_used: boolean;
  error: string | null;
  optimizer_evaluations: number | null;
  geometry_source: 'osrm' | 'waypoint_fallback';
  geometry_error: string | null;
}

export interface PriorityRoute {
  path: string[];
  path_coords: [number, number][];
  distance: number;
  time: number;
  cost: number;
  geometry_source: 'osrm' | 'waypoint_fallback';
  geometry_error: string | null;
}

export interface ConditionZone {
  lat: number;
  lng: number;
  radius: number;
  color: string;
  label: string;
  type: 'traffic' | 'weather' | 'road';
}

export interface OptimizationResult {
  id: number;
  request: RouteOptimizationRequest;
  quantum: QuantumResult;
  dijkstra: AlgorithmResult;
  astar: AlgorithmResult;
  bellman_ford: AlgorithmResult;
  priority_routes: {
    fastest: PriorityRoute;
    shortest: PriorityRoute;
    least_fuel: PriorityRoute;
    least_traffic: PriorityRoute;
    balanced: PriorityRoute;
  };
  traffic_prediction: TrafficPrediction;
  nodes: RouteNode[];
  edges: RouteEdge[];
  condition_zones: ConditionZone[];
  recommendation: {
    path: string[];
    path_coords: [number, number][];
    geometry_source: 'osrm' | 'waypoint_fallback';
    geometry_error: string | null;
    distance: number;
    time: number;
    cost: number;
    fuel_l: number;
    objective_value: number;
    reason: string;
    weights: Record<string, number>;
    explanation: RouteDecisionExplanation;
  };
  route_analysis: {
    search_report: RouteDecisionExplanation['search_scope'];
    alternatives: RouteAlternativeAnalysis[];
    constraints: RouteDecisionExplanation['constraints'];
  };
  road_geometry: {
    provider: 'OSRM';
    profile: string;
    source: string;
    status: 'complete' | 'partial_fallback';
    fallback_count: number;
    route_count: number;
    note: string;
  };
  network_version: string;
  created_at: string;
}

export interface TrafficPrediction {
  predicted_traffic: number;
  congestion_level: 'low' | 'moderate' | 'high' | 'severe';
  confidence_score: number | null;
  peak_hours: string[];
  estimated_delay_min?: number;
  expected_travel_time_min?: number;
  model_name?: string;
  provenance: string;
  dataset_fingerprint?: string;
}

export interface TrafficModelMetric {
  name: string;
  mae: number;
  rmse: number;
  r2: number;
}

export interface TrafficModelReport {
  status: string;
  provenance: string;
  dataset_fingerprint: string;
  training_rows: number;
  test_rows: number;
  selected_model: string;
  metrics: TrafficModelMetric[];
  limitation: string;
}

export interface DashboardStats {
  total_routes: number;
  avg_traffic: number;
  success_rate: number;
  quantum_accuracy: number;
  avg_time_saved: number;
  fuel_saved: number;
  carbon_reduction: number;
  avg_execution_time: number;
}

export interface SimulationData {
  scenario_id: string;
  scenario_label: string;
  provenance: 'deterministic_synthetic_scenario';
  generated_at: string;
  active_vehicles: number;
  accidents: SimulationEvent[];
  road_closures: SimulationEvent[];
  traffic_hotspots: TrafficHotspot[];
  weather_alerts: WeatherAlert[];
}

export interface SimulationEvent {
  id: string;
  lat: number;
  lng: number;
  type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

export interface TrafficHotspot {
  lat: number;
  lng: number;
  intensity: number;
  label: string;
}

export interface WeatherAlert {
  type: string;
  severity: string;
  message: string;
}

export interface RecentOptimization {
  id: number;
  source: string;
  destination: string;
  algorithm: string;
  distance: number;
  time: number;
  objective_value: number;
  created_at: string;
}
