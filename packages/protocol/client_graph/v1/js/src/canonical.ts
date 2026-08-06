import { isPlainObject, ProtocolValueError, validateStrictJson } from "./issue";

export const PROTOCOL = "citry-client-graph/1" as const;
export const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER;

const canonicalValue = (value: unknown): string => {
	if (value === null || typeof value === "string" || typeof value === "boolean")
		return JSON.stringify(value);
	if (typeof value === "number") {
		if (!Number.isSafeInteger(value) || value < 0)
			throw new TypeError(
				"client-graph numbers must be non-negative safe integers",
			);
		return String(value);
	}
	if (Array.isArray(value)) return `[${value.map(canonicalValue).join(",")}]`;
	if (isPlainObject(value)) {
		return `{${Object.keys(value)
			.sort()
			.map((key) => `${JSON.stringify(key)}:${canonicalValue(value[key])}`)
			.join(",")}}`;
	}
	throw new TypeError("unsupported client-graph JSON value");
};

/** Return the exact client-graph canonical JSON for one in-memory value. */
export const canonicalJson = (value: unknown): string => {
	const issue = validateStrictJson(value);
	if (issue) throw new ProtocolValueError(issue);
	return canonicalValue(value);
};

// Synchronous SHA-256 keeps graph validation available on ordinary HTTP
// origins where SubtleCrypto may be unavailable.
export const sha256 = (value: string): string => {
	const bytes = new TextEncoder().encode(value);
	const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
	const padded = new Uint8Array(paddedLength);
	padded.set(bytes);
	padded[bytes.length] = 0x80;
	const view = new DataView(padded.buffer);
	view.setUint32(
		paddedLength - 8,
		Math.floor(bytes.length / 0x20000000),
		false,
	);
	view.setUint32(paddedLength - 4, (bytes.length << 3) >>> 0, false);
	const constants = new Uint32Array([
		0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
		0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
		0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
		0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
		0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
		0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
		0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
		0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
		0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
		0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
		0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
	]);
	const hash = new Uint32Array([
		0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c,
		0x1f83d9ab, 0x5be0cd19,
	]);
	const words = new Uint32Array(64);
	const rotate = (word: number, count: number): number =>
		(word >>> count) | (word << (32 - count));
	for (let offset = 0; offset < paddedLength; offset += 64) {
		for (let index = 0; index < 16; index += 1)
			words[index] = view.getUint32(offset + index * 4, false);
		for (let expanded = 16; expanded < 64; expanded += 1) {
			const before15 = words[expanded - 15] as number;
			const before2 = words[expanded - 2] as number;
			const sigma0 =
				rotate(before15, 7) ^ rotate(before15, 18) ^ (before15 >>> 3);
			const sigma1 =
				rotate(before2, 17) ^ rotate(before2, 19) ^ (before2 >>> 10);
			words[expanded] =
				((words[expanded - 16] as number) +
					sigma0 +
					(words[expanded - 7] as number) +
					sigma1) >>>
				0;
		}
		let a = hash[0] as number;
		let b = hash[1] as number;
		let c = hash[2] as number;
		let d = hash[3] as number;
		let e = hash[4] as number;
		let f = hash[5] as number;
		let g = hash[6] as number;
		let h = hash[7] as number;
		for (let round = 0; round < 64; round += 1) {
			const sum1 = rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25);
			const choice = (e & f) ^ (~e & g);
			const temporary1 =
				(h +
					sum1 +
					choice +
					(constants[round] as number) +
					(words[round] as number)) >>>
				0;
			const sum0 = rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22);
			const majority = (a & b) ^ (a & c) ^ (b & c);
			const temporary2 = (sum0 + majority) >>> 0;
			h = g;
			g = f;
			f = e;
			e = (d + temporary1) >>> 0;
			d = c;
			c = b;
			b = a;
			a = (temporary1 + temporary2) >>> 0;
		}
		hash[0] = ((hash[0] as number) + a) >>> 0;
		hash[1] = ((hash[1] as number) + b) >>> 0;
		hash[2] = ((hash[2] as number) + c) >>> 0;
		hash[3] = ((hash[3] as number) + d) >>> 0;
		hash[4] = ((hash[4] as number) + e) >>> 0;
		hash[5] = ((hash[5] as number) + f) >>> 0;
		hash[6] = ((hash[6] as number) + g) >>> 0;
		hash[7] = ((hash[7] as number) + h) >>> 0;
	}
	return Array.from(hash)
		.map((word) => word.toString(16).padStart(8, "0"))
		.join("");
};

/** Hash one already validated unsigned manifest. */
export const revisionFor = (
	unsignedManifest: Record<string, unknown>,
): string => sha256(canonicalValue(unsignedManifest));

/** Recalculate a manifest revision without mutating the input. */
export const revisionForManifest = (
	manifest: Record<string, unknown>,
): string => {
	const unsigned: Record<string, unknown> = {};
	for (const key of Object.keys(manifest)) {
		if (key !== "revision") unsigned[key] = manifest[key];
	}
	return revisionFor(unsigned);
};
