const PYPI_FILES_HOST = "files.pythonhosted.org";
// Published direct URLs are accepted only from this pinned Pyodide CDN origin.
const APPROVED_DIRECT_URL_HOST = "cdn.jsdelivr.net";
const PYODIDE_VERSION_PATTERN = /^\d+\.\d+\.\d+$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

function packageLabel(packageInfo) {
  const name = typeof packageInfo?.name === "string" ? packageInfo.name : "unknown package";
  const version = typeof packageInfo?.version === "string" ? packageInfo.version : "unknown version";
  return `${name} ${version}`;
}

function requirePackageIdentity(packageInfo) {
  if (
    packageInfo === null
    || typeof packageInfo !== "object"
    || Array.isArray(packageInfo)
    || typeof packageInfo.name !== "string"
    || packageInfo.name.length === 0
    || typeof packageInfo.version !== "string"
    || packageInfo.version.length === 0
  ) {
    throw new Error("The playground runtime contains a package without a name and version.");
  }
}

function pyodidePackageBase(pyodide) {
  if (
    pyodide === null
    || typeof pyodide !== "object"
    || typeof pyodide.version !== "string"
    || !PYODIDE_VERSION_PATTERN.test(pyodide.version)
  ) {
    throw new Error("The playground runtime has an invalid Pyodide version.");
  }
  return `/pyodide/v${pyodide.version}/full/`;
}

export function validatePyodideManifest(pyodide) {
  const path = pyodidePackageBase(pyodide);
  const baseUrl = `https://${APPROVED_DIRECT_URL_HOST}${path}`;
  if (
    typeof pyodide.python !== "string"
    || !PYODIDE_VERSION_PATTERN.test(pyodide.python)
    || pyodide.index_url !== baseUrl
    || pyodide.module_url !== `${baseUrl}pyodide.mjs`
  ) {
    throw new Error("The playground runtime has invalid Pyodide CDN URLs.");
  }
}

function resolveDirectUrl(packageInfo, baseUrl, pyodide) {
  const value = packageInfo.url;
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`${packageLabel(packageInfo)} has no runtime URL.`);
  }
  if (
    value.startsWith("//")
    || value.includes("\\")
    || value.includes("?")
    || value.includes("#")
    || value.includes("@")
  ) {
    throw new Error(`${packageLabel(packageInfo)} has an unsafe runtime URL.`);
  }
  const isLocal = value.startsWith("./local/") && !value.includes("..") && !value.startsWith("//");
  const isAbsolute = /^[a-z][a-z\d+.-]*:/i.test(value) || value.startsWith("//");
  const resolved = new URL(value, baseUrl);
  if (isLocal) return resolved.href;
  const expectedPath = pyodidePackageBase(pyodide);
  const pathRemainder = resolved.pathname.startsWith(expectedPath)
    ? resolved.pathname.slice(expectedPath.length)
    : "";
  if (
    !isAbsolute
    || resolved.protocol !== "https:"
    || resolved.hostname !== APPROVED_DIRECT_URL_HOST
    || resolved.username
    || resolved.password
    || resolved.port
    || !pathRemainder
    || pathRemainder.includes("/")
  ) {
    throw new Error(`${packageLabel(packageInfo)} has an unapproved Pyodide runtime URL.`);
  }
  return resolved.href;
}

async function resolvePypiUrl(packageInfo, fetchImpl) {
  const { filename, sha256 } = packageInfo;
  if (
    typeof filename !== "string"
    || filename.length === 0
    || filename.includes("/")
    || filename.includes("\\")
  ) {
    throw new Error(`${packageLabel(packageInfo)} has an invalid wheel filename.`);
  }
  if (typeof sha256 !== "string" || !SHA256_PATTERN.test(sha256)) {
    throw new Error(`${packageLabel(packageInfo)} has an invalid SHA-256 digest.`);
  }

  // PyPI assigns the storage URL, so resolve it at load time while pinning the
  // filename and digest that qualification knew before publication.
  const name = encodeURIComponent(packageInfo.name);
  const version = encodeURIComponent(packageInfo.version);
  const response = await fetchImpl(`https://pypi.org/pypi/${name}/${version}/json`, {
    cache: "no-cache",
  });
  if (!response.ok) {
    throw new Error(`PyPI metadata for ${packageLabel(packageInfo)} returned HTTP ${response.status}.`);
  }
  const payload = await response.json();
  const matches = Array.isArray(payload.urls)
    ? payload.urls.filter((item) => item?.filename === filename)
    : [];
  if (matches.length !== 1) {
    throw new Error(`PyPI does not contain exactly one ${filename} artifact.`);
  }
  const artifact = matches[0];
  const artifactUrl = new URL(artifact.url);
  if (
    artifactUrl.protocol !== "https:"
    || artifactUrl.hostname !== PYPI_FILES_HOST
    || artifact.digests?.sha256 !== sha256
  ) {
    throw new Error(`PyPI's ${filename} artifact does not match the qualified SHA-256 digest.`);
  }
  return artifactUrl.href;
}

export async function resolvePackageUrl(
  packageInfo,
  { baseUrl = import.meta.url, fetchImpl = fetch, pyodide } = {},
) {
  requirePackageIdentity(packageInfo);
  if (packageInfo.source === "url") return resolveDirectUrl(packageInfo, baseUrl, pyodide);
  if (packageInfo.source === "pypi") return resolvePypiUrl(packageInfo, fetchImpl);
  throw new Error(`${packageLabel(packageInfo)} has an unsupported runtime source.`);
}

export async function resolvePackageUrls(packages, options = {}) {
  if (!Array.isArray(packages)) throw new Error("The playground runtime package list is invalid.");
  return Promise.all(packages.map((packageInfo) => resolvePackageUrl(packageInfo, options)));
}
