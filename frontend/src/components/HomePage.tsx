import { useQuery } from '@tanstack/react-query'
import { type ReactNode, useEffect } from 'react'

import { getHealth } from '@/api/health'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

type Tone = 'ok' | 'warn' | 'error' | 'muted'

function StatusPill({ tone, children }: { tone: Tone; children: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        tone === 'ok' && 'bg-emerald-100 text-emerald-800',
        tone === 'warn' && 'bg-amber-100 text-amber-800',
        tone === 'error' && 'bg-red-100 text-red-800',
        tone === 'muted' && 'bg-muted text-muted-foreground',
      )}
    >
      {children}
    </span>
  )
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  )
}

export function HomePage() {
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth })
  const agencyName = health.data?.agency_name

  useEffect(() => {
    if (agencyName) {
      document.title = agencyName
    }
  }, [agencyName])

  let apiTone: Tone = 'muted'
  let apiLabel = 'Checking…'
  if (health.isError) {
    apiTone = 'error'
    apiLabel = 'Unreachable'
  } else if (health.data) {
    apiTone = health.data.status === 'ok' ? 'ok' : 'warn'
    apiLabel = health.data.status === 'ok' ? 'Online' : 'Degraded'
  }

  return (
    <main className="flex min-h-svh items-start justify-center bg-muted/40 px-4 py-8 sm:items-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-xl break-words">
            {agencyName ?? (health.isError ? 'Service unavailable' : 'Loading…')}
          </CardTitle>
          <CardDescription>Vehicle Rental Management System</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="divide-y">
            <Row label="Backend">
              <StatusPill tone={apiTone}>{apiLabel}</StatusPill>
            </Row>
            <Row label="Database">
              {health.data ? (
                <StatusPill tone={health.data.database === 'ok' ? 'ok' : 'error'}>
                  {health.data.database === 'ok' ? 'Reachable' : 'Unreachable'}
                </StatusPill>
              ) : (
                <StatusPill tone="muted">—</StatusPill>
              )}
            </Row>
            <Row label="Currency">{health.data?.currency ?? '—'}</Row>
          </dl>
        </CardContent>
        <CardFooter>
          <Button
            className="w-full sm:w-auto"
            variant="outline"
            onClick={() => health.refetch()}
            disabled={health.isFetching}
          >
            {health.isFetching ? 'Checking…' : 'Check again'}
          </Button>
        </CardFooter>
      </Card>
    </main>
  )
}
