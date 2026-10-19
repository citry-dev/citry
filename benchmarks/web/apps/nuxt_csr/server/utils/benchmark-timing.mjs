export function appendServerTiming(existing, entries) {
  const previous = existing == null ? [] : Array.isArray(existing) ? existing : [existing];
  return [...previous, ...entries].filter(Boolean).map(String).join(", ");
}
