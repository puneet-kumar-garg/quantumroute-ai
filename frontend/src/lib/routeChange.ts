import type { RouteOptimizationRequest } from '../types/index.ts';

export interface RouteChangeExplanation {
  title: 'Route changed';
  changedInputs: string[];
  previousPath: string;
  newPath: string;
}

const labels: Partial<Record<keyof RouteOptimizationRequest, string>> = {
  source: 'Source',
  destination: 'Destination',
  vehicle_type: 'Vehicle',
  traffic_density: 'Traffic',
  weather: 'Weather',
  road_condition: 'Road condition',
  optimization_priority: 'Priority',
  time_of_day: 'Departure',
};

const formatValue = (value: unknown) => String(value ?? '')
  .replace(/_/g, ' ')
  .replace(/\b\w/g, character => character.toUpperCase());

const priorityValues: Record<string, string> = {
  fastest: 'Fastest route',
  shortest: 'Shortest route',
  least_fuel: 'Least fuel',
  least_traffic: 'Least traffic',
  balanced: 'Balanced',
};

const formatFieldValue = (key: keyof RouteOptimizationRequest, value: unknown) => (
  key === 'optimization_priority'
    ? priorityValues[String(value)] ?? formatValue(value)
    : formatValue(value)
);

export function describeRouteChange(
  previousRequest: RouteOptimizationRequest,
  nextRequest: RouteOptimizationRequest,
  previousPath: string[],
  nextPath: string[],
): RouteChangeExplanation | null {
  if (previousPath.join('\u0000') === nextPath.join('\u0000')) return null;

  const changedInputs = (Object.keys(labels) as Array<keyof RouteOptimizationRequest>)
    .filter(key => previousRequest[key] !== nextRequest[key])
    .map(key => `${labels[key]}: ${formatFieldValue(key, previousRequest[key])} → ${formatFieldValue(key, nextRequest[key])}`);

  const segmentChanges = (
    field: 'closed_segments' | 'construction_segments',
    label: string,
  ) => {
    const previous = new Set(previousRequest[field] ?? []);
    const next = new Set(nextRequest[field] ?? []);
    for (const segment of next) {
      if (!previous.has(segment)) changedInputs.push(`${label} added: ${segment.replace('|', ' → ')}`);
    }
    for (const segment of previous) {
      if (!next.has(segment)) changedInputs.push(`${label} removed: ${segment.replace('|', ' → ')}`);
    }
  };
  segmentChanges('closed_segments', 'Closure');
  segmentChanges('construction_segments', 'Construction');

  return {
    title: 'Route changed',
    changedInputs,
    previousPath: previousPath.join(' → '),
    newPath: nextPath.join(' → '),
  };
}
