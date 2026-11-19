import assert from 'node:assert/strict';
import test from 'node:test';

import { buildRouteRequest } from '../src/lib/routeRequest.ts';

const form = {
  source: 'PGI Hospital',
  destination: 'Elante Mall',
  vehicle_type: 'emergency' as const,
  traffic_density: 'high' as const,
  weather: 'rain' as const,
  road_condition: 'moderate' as const,
  optimization_priority: 'shortest' as const,
  time_of_day: '09:00',
  qaoa_layers: 2,
  qaoa_shots: 1024,
  traffic_overlay: true,
  animate_vehicle: true,
  disruption_type: 'closure' as const,
  disruption_segment: 'PGI Hospital|Panjab University',
};

test('builds an auditable closure request and retains the previous route', () => {
  const previousPath = ['PGI Hospital', 'Panjab University', 'Elante Mall'];
  const request = buildRouteRequest(form, undefined, previousPath, {
    ...form,
    vehicle_type: 'car',
    traffic_density: 'low',
    weather: 'sunny',
    closed_segments: [],
    construction_segments: [],
  });

  assert.deepEqual(request.closed_segments, ['PGI Hospital|Panjab University']);
  assert.deepEqual(request.construction_segments, []);
  assert.deepEqual(request.previous_path, previousPath);
  assert.equal(request.previous_scenario?.vehicle_type, 'car');
  assert.equal(request.previous_scenario?.weather, 'sunny');
  assert.equal('disruption_type' in request, false);
  assert.equal('disruption_segment' in request, false);
});

test('maps construction separately and sends custom objective weights', () => {
  const request = buildRouteRequest(
    { ...form, disruption_type: 'construction' },
    { distance: 30, time: 40, fuel: 10, congestion: 10, risk: 10 },
  );

  assert.deepEqual(request.closed_segments, []);
  assert.deepEqual(request.construction_segments, ['PGI Hospital|Panjab University']);
  assert.equal(request.weights?.time, 40);
});
