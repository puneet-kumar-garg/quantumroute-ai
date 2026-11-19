export function selectAvailableLocation(
  current: string,
  locations: string[],
  excluded: string,
  preferred: string,
): string {
  if (current !== excluded && locations.includes(current)) return current;
  if (preferred !== excluded && locations.includes(preferred)) return preferred;
  return locations.find((location) => location !== excluded) ?? '';
}
