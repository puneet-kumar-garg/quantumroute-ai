import test from 'node:test';
import assert from 'node:assert/strict';
import { selectAvailableLocation } from '../src/lib/locationSelection.ts';

test('a removed location is replaced with the preferred available location', () => {
  const locations = ['Elante Mall', 'Sector 17 Plaza', 'Rock Garden'];

  assert.equal(
    selectAvailableLocation('Sukhna Lake', locations, 'Elante Mall', 'Rock Garden'),
    'Rock Garden',
  );
});

test('a valid current location remains selected', () => {
  const locations = ['Elante Mall', 'Sector 17 Plaza', 'Rock Garden'];

  assert.equal(
    selectAvailableLocation('Sector 17 Plaza', locations, 'Elante Mall', 'Rock Garden'),
    'Sector 17 Plaza',
  );
});
