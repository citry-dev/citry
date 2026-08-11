import assert from "node:assert/strict";
import test from "node:test";

import { RestartCoordinator, stopLanguageClient, WatchedFileChangeBatcher } from "../out/tests/clientLifecycle.mjs";

function deferred() {
	let resolve;
	const promise = new Promise((done) => {
		resolve = done;
	});
	return { promise, resolve };
}

test("serializes restart requests that arrive during an active restart", async () => {
	const releases = [deferred(), deferred()];
	let active = 0;
	let maximumActive = 0;
	let runs = 0;
	const coordinator = new RestartCoordinator(async () => {
		const release = releases[runs];
		runs += 1;
		active += 1;
		maximumActive = Math.max(maximumActive, active);
		await release.promise;
		active -= 1;
	});

	const first = coordinator.request();
	await Promise.resolve();
	const second = coordinator.request();
	releases[0].resolve();
	await Promise.resolve();
	await Promise.resolve();
	releases[1].resolve();
	await Promise.all([first, second, coordinator.settled()]);

	assert.equal(runs, 2);
	assert.equal(maximumActive, 1);
});

test("coalesces Python watcher bursts by URI", () => {
	const deliveries = [];
	const batcher = new WatchedFileChangeBatcher((changes) => deliveries.push(changes), 60_000);

	batcher.push("file:///component.py", "changed");
	batcher.push("file:///component.py", "created");
	batcher.push("file:///other.py", "deleted");
	batcher.flush();

	assert.deepEqual(deliveries, [
		[
			{ uri: "file:///component.py", type: "created" },
			{ uri: "file:///other.py", type: "deleted" },
		],
	]);
	batcher.dispose();
});

test("terminates a language server that misses the graceful stop deadline", async () => {
	const signals = [];
	let stopTimeout;
	const process = {
		exitCode: null,
		signalCode: null,
		kill(signal) {
			signals.push(signal);
			this.signalCode = signal;
			return true;
		},
	};
	const client = {
		needsStop: () => true,
		stop: async (timeout) => {
			stopTimeout = timeout;
			throw new Error("timeout");
		},
		serverProcess: process,
	};

	await stopLanguageClient(client);
	assert.equal(stopTimeout, 2_000);
	assert.deepEqual(signals, ["SIGTERM"]);
});
