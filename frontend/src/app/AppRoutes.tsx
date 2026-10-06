import { Route, Routes } from 'react-router-dom'

import { HomePage } from '@/components/HomePage'
import { AppShell } from '@/components/layout/AppShell'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { HelpPage } from '@/pages/HelpPage'
import { NotAvailablePage } from '@/pages/NotAvailablePage'
import { NotFoundPage } from '@/pages/NotFoundPage'

import { RequireAuth, RequireRole } from './guards'
import { UPCOMING_ITEMS } from './navigation'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route
        path="app"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        {UPCOMING_ITEMS.map((item) => (
          <Route
            key={item.to}
            path={item.to.replace('/app/', '')}
            element={
              <RequireRole roles={item.roles}>
                <NotAvailablePage item={item} />
              </RequireRole>
            }
          />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
