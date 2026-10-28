// Ephemeral transport resources only. No account data or responses are cached.
const active = new Map<string, Set<AbortController>>();

export function registerApiRequest(token: string, controller: AbortController): () => void {
  const requests = active.get(token) ?? new Set<AbortController>();
  requests.add(controller);
  active.set(token, requests);
  return () => {
    requests.delete(controller);
    if (requests.size === 0) active.delete(token);
  };
}

export function cancelApiRequests(token: string): void {
  for (const controller of active.get(token) ?? []) controller.abort();
}
