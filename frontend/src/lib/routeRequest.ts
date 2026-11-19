import type { RouteOptimizationRequest } from '@/types';

export type DisruptionType = 'none' | 'closure' | 'construction';

export type RouteFormValues = Omit<
  RouteOptimizationRequest,
  'weights' | 'previous_path' | 'previous_scenario' | 'closed_segments' | 'construction_segments'
> & {
  disruption_type: DisruptionType;
  disruption_segment: string;
};

export function buildRouteRequest(
  values: RouteFormValues,
  weights?: RouteOptimizationRequest['weights'],
  previousPath?: string[],
  previousRequest?: RouteOptimizationRequest,
): RouteOptimizationRequest {
  const { disruption_type, disruption_segment, ...request } = values;
  const activeSegment = disruption_type === 'none' ? '' : disruption_segment;

  return {
    ...request,
    weights,
    previous_path: previousPath?.length ? [...previousPath] : undefined,
    previous_scenario: previousRequest ? {
      vehicle_type: previousRequest.vehicle_type,
      traffic_density: previousRequest.traffic_density,
      weather: previousRequest.weather,
      road_condition: previousRequest.road_condition,
      optimization_priority: previousRequest.optimization_priority,
      time_of_day: previousRequest.time_of_day ?? '09:00',
    } : undefined,
    closed_segments: disruption_type === 'closure' && activeSegment ? [activeSegment] : [],
    construction_segments: disruption_type === 'construction' && activeSegment ? [activeSegment] : [],
  };
}
