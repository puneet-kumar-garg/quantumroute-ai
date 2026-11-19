import assert from 'node:assert/strict';
import test from 'node:test';

import { describeRouteChange } from '../src/lib/routeChange.ts';


const baseRequest = {
  source: 'Rock Garden', destination: 'Elante Mall', vehicle_type: 'car' as const,
  traffic_density: 'high' as const, weather: 'rain' as const,
  road_condition: 'moderate' as const, optimization_priority: 'shortest' as const,
  time_of_day: '09:00',
};


test('a changed path names the controls that caused recomputation', () => {
  const change = describeRouteChange(
    baseRequest,
    { ...baseRequest, vehicle_type: 'truck', optimization_priority: 'least_traffic' },
    ['Rock Garden', 'Sector 8 Market', 'Elante Mall'],
    ['Rock Garden', 'Panchkula Sector 5', 'Elante Mall'],
  );

  assert.equal(change?.title, 'Route changed');
  assert.deepEqual(change?.changedInputs, [
    'Vehicle: Car → Truck',
    'Priority: Shortest route → Least traffic',
  ]);
  assert.equal(change?.newPath, 'Rock Garden → Panchkula Sector 5 → Elante Mall');
});


test('unchanged path does not claim a reroute', () => {
  const change = describeRouteChange(
    baseRequest,
    { ...baseRequest, weather: 'sunny' },
    ['Rock Garden', 'Sector 8 Market', 'Elante Mall'],
    ['Rock Garden', 'Sector 8 Market', 'Elante Mall'],
  );

  assert.equal(change, null);
});

test('a closure-driven reroute identifies the affected segment', () => {
  const change = describeRouteChange(
    { ...baseRequest, closed_segments: [] },
    { ...baseRequest, closed_segments: ['PGI Hospital|Punjab University'] },
    ['PGI Hospital', 'Punjab University', 'Elante Mall'],
    ['PGI Hospital', 'Sector 17 Plaza', 'Elante Mall'],
  );

  assert.deepEqual(change?.changedInputs, ['Closure added: PGI Hospital → Punjab University']);
});
