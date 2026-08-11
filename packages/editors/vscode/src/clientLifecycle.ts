/** Serialize restart requests so one workspace never owns concurrent clients. */
export class RestartCoordinator {
	private requested = false;
	private running: Promise<void> | undefined;

	constructor(private readonly restart: () => Promise<void>) {}

	request(): Promise<void> {
		this.requested = true;
		if (this.running === undefined) {
			this.running = this.run();
		}
		return this.running;
	}

	settled(): Promise<void> {
		return this.running ?? Promise.resolve();
	}

	private async run(): Promise<void> {
		try {
			// A request arriving during shutdown gets one fresh client after the
			// current restart, without ever overlapping its start/stop work.
			while (this.requested) {
				this.requested = false;
				await this.restart();
			}
		} finally {
			this.running = undefined;
		}
	}
}

export interface PendingFileChange<T> {
	uri: string;
	type: T;
}

/** Collect save bursts into one watched-files notification per workspace. */
export class WatchedFileChangeBatcher<T> {
	private readonly pending = new Map<string, T>();
	private timer: ReturnType<typeof setTimeout> | undefined;

	constructor(
		private readonly send: (changes: PendingFileChange<T>[]) => void,
		private readonly delayMs = 100,
	) {}

	push(uri: string, type: T): void {
		this.pending.set(uri, type);
		if (this.timer === undefined) {
			this.timer = setTimeout(() => this.flush(), this.delayMs);
		}
	}

	flush(): void {
		if (this.timer !== undefined) {
			clearTimeout(this.timer);
			this.timer = undefined;
		}
		if (this.pending.size === 0) {
			return;
		}
		const changes = [...this.pending].map(([uri, type]) => ({ uri, type }));
		this.pending.clear();
		this.send(changes);
	}

	dispose(): void {
		if (this.timer !== undefined) {
			clearTimeout(this.timer);
			this.timer = undefined;
		}
		this.pending.clear();
	}
}

interface ServerProcess {
	exitCode: number | null;
	signalCode: NodeJS.Signals | null;
	kill(signal?: NodeJS.Signals | number): boolean;
}

interface StoppableLanguageClient {
	needsStop(): boolean;
	stop(timeout?: number): Promise<void>;
	serverProcess?: ServerProcess;
}

/** Bound graceful shutdown and terminate a server that misses the deadline. */
export async function stopLanguageClient(client: StoppableLanguageClient, timeoutMs = 2_000): Promise<void> {
	if (!client.needsStop()) {
		return;
	}
	// Citry-lsp owns its analyzer descendants and gets the complete graceful
	// window first. Retain the exposed parent handle because the language client
	// clears it before reporting a transport timeout.
	const process = client.serverProcess;
	try {
		await client.stop(timeoutMs);
	} catch {
		if (process === undefined || process.exitCode !== null || process.signalCode !== null) {
			return;
		}
		process.kill("SIGTERM");
		const escalation = setTimeout(() => {
			if (process.exitCode === null && process.signalCode === null) {
				process.kill("SIGKILL");
			}
		}, 250);
		escalation.unref();
	}
}
