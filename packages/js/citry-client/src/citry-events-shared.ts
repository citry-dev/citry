/** Renderer-independent helpers shared by Citry Events browser hosts. */

/** Whether a value is a button or input that belongs to this form, so it may have submitted it. */
const isFormSubmitter = (value: unknown, form: HTMLFormElement): value is HTMLButtonElement | HTMLInputElement =>
  ((typeof HTMLButtonElement === "function" && value instanceof HTMLButtonElement) ||
    (typeof HTMLInputElement === "function" && value instanceof HTMLInputElement)) &&
  value.form === form;

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
  submitter?: unknown,
): Record<string, string | string[]> => {
  const entries = new Map<string, string[]>();
  // A post without JavaScript also sends the name and value of the button
  // that submitted the form. FormData adds it only when it is given that
  // button, and throws for any element that is not one of the form's own
  // submit buttons, so anything else is left out.
  const button = isFormSubmitter(submitter, form) ? submitter : undefined;
  let data: FormData;
  try {
    data = new FormData(form, button);
  } catch {
    data = new FormData(form);
  }
  data.forEach((value, name) => {
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
