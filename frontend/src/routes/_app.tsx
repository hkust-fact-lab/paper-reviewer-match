import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'
import { AppShell } from '~/components/layout/app-shell'
import { getUser } from '~/lib/auth'

export const Route = createFileRoute('/_app')({
  beforeLoad: async () => {
    const user = await getUser()
    if (!user) throw redirect({ to: '/login' })
    return { user }
  },
  component: AppLayout,
})

function AppLayout() {
  const { user } = Route.useRouteContext()
  return (
    <AppShell user={user}>
      <Outlet />
    </AppShell>
  )
}
