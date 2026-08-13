// CodeMirror and the analysis Worker share this narrow authored-region proof.
// It recognizes the direct triple-quoted asset form used by Citry components.
export function citryAssetAt(node, read) {
  if (node.name !== "String") return null;
  const prefix = read(Math.max(0, node.from - 220), node.from);
  const line = prefix.slice(prefix.lastIndexOf("\n") + 1);
  const assignment = line.match(/\b(template|js|css|messages)(?:\s*:\s*[^=\n]+)?\s*=\s*$/);
  if (!assignment) return null;

  const quoted = read(node.from, node.to);
  const literal = quoted.match(/^([rubfRUBF]*)("""|''')/);
  if (!literal) return null;
  const literalPrefix = literal[1];
  const delimiter = literal[2];
  if (!delimiter || !quoted.endsWith(delimiter) || node.to - node.from < 6) return null;
  const bodyStart = literalPrefix.length + delimiter.length;
  const body = quoted.slice(bodyStart, -delimiter.length);
  return {
    kind: assignment[1],
    from: node.from + bodyStart,
    to: node.to - delimiter.length,
    // Phase 1 has no Python escape-to-source map. Raw literals and ordinary
    // bodies without escapes preserve exact parser and editor coordinates.
    sourceExact: !/[bf]/i.test(literalPrefix) && (/r/i.test(literalPrefix) || !body.includes("\\")),
  };
}
