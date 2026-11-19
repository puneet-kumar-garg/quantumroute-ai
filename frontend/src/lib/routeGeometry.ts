export type MapCoordinate = [number, number];

export function selectRoadGeometry(
  roadCoordinates: MapCoordinate[],
  curatedFallback: MapCoordinate[],
): MapCoordinate[] {
  return roadCoordinates.length > 1 ? roadCoordinates : curatedFallback;
}
