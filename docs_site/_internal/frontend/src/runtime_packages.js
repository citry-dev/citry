const PYPI_FILES_HOST = "files.pythonhosted.org";
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

function resolveDirectUrl(packageInfo, baseUrl) {
  if (typeof packageInfo.url !== "string" || packageInfo.url.length === 0) {
    throw new Error(`${packageLabel(packageInfo)} has no runtime URL.`);
  }
  return new URL(packageInfo.url, baseUrl).href;
}

async function resolvePypiUrl(packageInfo, fetchImpl) {
  const { filename, sha256 } = packageInfo;
  if (typeof filename !== "string" || filename.length === 0 || filename.includes("/")) {
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
  { baseUrl = import.meta.url, fetchImpl = fetch } = {},
) {
  requirePackageIdentity(packageInfo);
  if (packageInfo.source === "url") return resolveDirectUrl(packageInfo, baseUrl);
  if (packageInfo.source === "pypi") return resolvePypiUrl(packageInfo, fetchImpl);
  throw new Error(`${packageLabel(packageInfo)} has an unsupported runtime source.`);
}

export async function resolvePackageUrls(packages, options = {}) {
  if (!Array.isArray(packages)) throw new Error("The playground runtime package list is invalid.");
  return Promise.all(packages.map((packageInfo) => resolvePackageUrl(packageInfo, options)));
}
