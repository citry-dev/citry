export function formatRuntimeLabel(runtime, source) {
  const versions = String(runtime)
    .split(", ")
    .filter((part) => part.startsWith("Citry "))
    .join(" · ");
  const sourceLabel = source === "workspace" || source === "published" ? source : "unknown source";
  return `${versions || "Citry runtime"} · ${sourceLabel}`;
}
