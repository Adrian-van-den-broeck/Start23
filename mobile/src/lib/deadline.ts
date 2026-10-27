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
    return await Promise.race([operation(controller.signal), interrupted]);
  } finally {
    clearTimeout(timer);
    ownerSignal?.removeEventListener('abort', cancel);
  }
}
