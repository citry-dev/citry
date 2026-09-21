/** Renderer-independent helpers shared by Citry Events browser hosts. */

export const collectFormArgs = (
  form: HTMLFormElement,
  reservedFields: ReadonlySet<string>,
): Record<string, unknown> => {
  const entries = new Map<string, string[]>();
  new FormData(form).forEach((value, name) => {
    if (reservedFields.has(name) || typeof value !== "string") return;
    const bucket = entries.get(name) ?? [];
    bucket.push(value);
    entries.set(name, bucket);
  });
  const output: Record<string, unknown> = {};
  entries.forEach((values, name) => {
    const control = form.elements.namedItem(name);
    const input = control instanceof HTMLInputElement ? control : null;
    const numeric = input && (input.type === "number" || input.type === "range") ? input.valueAsNumber : Number.NaN;
    output[name] = values.length === 1 ? (Number.isFinite(numeric) ? numeric : values[0]) : values.slice();
  });
  return output;
};
