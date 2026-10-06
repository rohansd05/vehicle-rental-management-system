import { ApiError, apiFetch } from './client'

// GET /api/v1/health/ — public. The only source of the agency name and
// currency in the frontend (D7); never hardcode either.
export interface Health {
  status: 'ok' | 'degraded'
  database: 'ok' | 'unreachable'
  agency_name: string
  currency: string
}

export async function getHealth(): Promise<Health> {
  try {
    return await apiFetch<Health>('/api/v1/health/')
  } catch (error) {
    // 503 still carries a full health body (database unreachable).
    if (error instanceof ApiError && error.status === 503) {
      return error.body as Health
    }
    throw error
  }
}
