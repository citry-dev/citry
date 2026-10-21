/** Renderer-independent helpers shared by Citry Events browser hosts. */

/**
 * Read a form's named controls as call args.
 *
 * Every value stays the text the form holds, as a form posted without
 * JavaScript would send it. The caller marks the call with
 * `argsSource: "form"`, and the server converts the text to the handler's
 * number and boolean fields by the same rules for both paths.
 */
export const collectFormArgs = (
  form: HTMLFormElement,
  reservedFields: ReadonlySet<string>,
): Record<string, string | string[]> => {
  const entries = new Map<string, string[]>();
  new FormData(form).forEach((value, name) => {
    // A file cannot ride in a JSON call, so file inputs are left out.
    if (reservedFields.has(name) || typeof value !== "string") return;
    const bucket = entries.get(name) ?? [];
    bucket.push(value);
    entries.set(name, bucket);
  });
  const output: Record<string, string | string[]> = {};
  // One value is sent as itself and a repeated name as the list of its
  // values, the same shape the server's no-JavaScript form reader builds.
  entries.forEach((values, name) => {
    output[name] = values.length === 1 ? values[0] : values.slice();
  });
  return output;
};
