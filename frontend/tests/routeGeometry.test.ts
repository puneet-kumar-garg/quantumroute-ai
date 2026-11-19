import assert from 'node:assert/strict';
import test from 'node:test';

import { selectRoadGeometry } from '../src/lib/routeGeometry.ts';


test('OSRM road coordinates take precedence over straight graph edges', () => {
  const osrmRoad = [
    [30.7422, 76.8183],
    [30.7431, 76.8168],
    [30.7440, 76.8152],
  ] as [number, number][];
  const straightEdge = [
    [30.7422, 76.8183],
    [30.7440, 76.8152],
  ] as [number, number][];

  assert.deepEqual(selectRoadGeometry(osrmRoad, straightEdge), osrmRoad);
});


test('curated edge coordinates remain a visible fallback when OSRM is unavailable', () => {
  const straightEdge = [
    [30.7422, 76.8183],
    [30.7440, 76.8152],
  ] as [number, number][];

  assert.deepEqual(selectRoadGeometry([], straightEdge), straightEdge);
});
