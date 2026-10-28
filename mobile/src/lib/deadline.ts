export class DeadlineError extends Error {
  constructor() { super('Request deadline exceeded'); this.name = 'DeadlineError'; }
}

export class CancellationError extends Error {
  constructor() { super('Request cancelled'); this.name = 'CancellationError'; }
}

// Race the entire operation (including body consumption). Abort is best effort:
// native transports may continue processing after the caller has settled.
export async function withDeadline<T>(
  operation: (signal: AbortSignal) => Promise<T>,
  milliseconds: number,
  ownerSignal?: AbortSignal | null,
): Promise<T> {
  const expiresAt = Date.now() + milliseconds;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let cancel = () => {};
  const interrupted = new Promise<never>((_resolve, reject) => {
    cancel = () => { reject(new CancellationError()); controller.abort(); };
    ownerSignal?.addEventListener('abort', cancel, { once: true });
    timer = setTimeout(() => { reject(new DeadlineError()); controller.abort(); }, milliseconds);
  });
  try {
    if (ownerSignal?.aborted) throw new CancellationError();
    const work = operation(controller.signal).then(value => {
      // Native backgrounding can delay JS timers. A network completion queued
      // ahead of the resumed timer must still respect the wall-clock deadline.
      if (Date.now() >= expiresAt) { controller.abort(); throw new DeadlineError(); }
      return value;
    }, error => {
      if (Date.now() >= expiresAt) { controller.abort(); throw new DeadlineError(); }
      throw error;
    });
    return await Promise.race([work, interrupted]);
  } finally {
    clearTimeout(timer);
    ownerSignal?.removeEventListener('abort', cancel);
  }
}
