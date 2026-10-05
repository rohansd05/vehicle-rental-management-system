// Minimal fetch client for the VRMS API.
// Requests are same-origin: Vite proxies /api in development, Caddy in
// production (D1). Business rules are enforced by the server; anything the
// client checks is for usability only (CO-3).

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

// TODO(Phase 1, SE-9): replace with the real SimpleJWT access token, refresh
// on expiry, and re-authenticate before payments and refunds.
export function getAccessToken(): string | null {
  return null
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(path, { ...init, headers })
  const isJson = response.headers.get('Content-Type')?.includes('application/json')
  const body: unknown = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    throw new ApiError(response.status, body)
  }
  return body as T
}
